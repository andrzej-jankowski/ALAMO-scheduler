# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import random
import signal
from datetime import datetime, timedelta

from alamo_common import aiostats
from apscheduler.events import (EVENT_JOB_ERROR, EVENT_JOB_MAX_INSTANCES,
                                EVENT_JOB_MISSED)
from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from stevedore import driver

from alamo_scheduler.aioweb import json_response
from alamo_scheduler.conf import settings
from alamo_scheduler.hashing import Hashing
from alamo_scheduler.hooks.push_checks import PushChecks

logger = logging.getLogger(__name__)


class AlamoScheduler(object):
    sender = None
    loop = handler = None
    hashing = None
    name = None

    plugin_namespace = 'pl.allegro.tech.monitoring.alamo.drivers'

    def __init__(self, loop=None):
        kw = dict()
        if loop:
            kw['event_loop'] = loop

        self.scheduler = AsyncIOScheduler(**kw)

    def setup(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
            asyncio.set_event_loop(loop)
        self.loop = loop
        self.sender = driver.DriverManager(
            namespace=self.plugin_namespace,
            name=settings.SENDER_DRIVER,
            invoke_on_load=True,
        )
        self.hashing = Hashing(settings.SCHEDULER_HOSTS)
        self.name = settings.SCHEDULER_NAME
        self.scheduler.add_listener(
            self.event_listener,
            EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_MAX_INSTANCES
        )
        self.scheduler.add_job(
            self.hook, 'interval', id='push_checks', max_instances=1,
            seconds=15
        )

    def hook(self):
        hook = PushChecks()
        result = hook.trigger()
        if result:
            self.scheduler.remove_job('push_checks')

    @aiostats.increment()
    def _schedule_check(self, check):
        """Schedule check."""
        # Measure check count for each environment
        env = check.get('environment', 'unknown')
        aiostats.increment.incr('_schedule_check.{}'.format(env))

        self.sender.driver.send(check)

    def remove_job(self, job_id):
        """Remove job."""
        try:
            logger.info('Removing job for check id=`%s`', job_id)
            self.scheduler.remove_job(str(job_id))
        except JobLookupError:
            pass

    def schedule_check(self, check):
        """Schedule check with proper interval based on `frequency`.

        :param dict check: Check definition
        """
        try:
            frequency = check['fields']['frequency'] = int(
                check['fields']['frequency']
            )
            logger.info(
                'Scheduling check `%s` with id `%s` and interval `%s`',
                check['name'], check['id'], frequency
            )
            jitter = random.randint(0, frequency)
            first_run = datetime.now() + timedelta(seconds=jitter)
            kw = dict(
                seconds=frequency,
                id=str(check['uuid']),
                next_run_time=first_run,
                args=(check,)
            )
            self.schedule_job(self._schedule_check, **kw)

        except KeyError as e:
            logger.exception('Failed to schedule check: %s. Exception: %s',
                             check, e)

    def schedule_job(self, method, **kwargs):
        """Add new job to scheduler.

        :param method: reference to method that should be scheduled
        :param kwargs: additional kwargs passed to `add_job` method
        """
        try:
            self.scheduler.add_job(
                method, 'interval',
                misfire_grace_time=settings.JOBS_MISFIRE_GRACE_TIME,
                max_instances=settings.JOBS_MAX_INSTANCES,
                coalesce=settings.JOBS_COALESCE,
                **kwargs
            )
        except ConflictingIdError as e:
            logger.error(e)

    def event_listener(self, event):
        """React on events from scheduler.

        :param apscheduler.events.JobExecutionEvent event: job execution event
        """
        if event.code == EVENT_JOB_MISSED:
            aiostats.increment.incr('job.missed')
            logger.warning("Job %s scheduler for %s missed.", event.job_id,
                           event.scheduled_run_time)
        elif event.code == EVENT_JOB_ERROR:
            aiostats.increment.incr('job.error')
            logger.error("Job %s scheduled for %s failed. Exc: %s",
                         event.job_id,
                         event.scheduled_run_time,
                         event.exception)
        elif event.code == EVENT_JOB_MAX_INSTANCES:
            aiostats.increment.incr('job.max_instances')
            logger.warning(
                'Job `%s` could not be submitted. '
                'Maximum number of running instances was reached.',
                event.job_id
            )

    @aiostats.increment()
    def get_jobs(self):
        return [job.id for job in self.scheduler.get_jobs()]

    async def checks(self, request=None):

        uuid = request.match_info.get('uuid', None)
        if uuid is None:
            jobs = self.get_jobs()
            return json_response(data=dict(count=len(jobs), results=jobs))
        job = self.scheduler.get_job(uuid)
        if job is None:
            return json_response(
                data={'detail': 'Check does not exists.'}, status=404
            )

        check, = job.args
        return json_response(data=check)

    @aiostats.timer()
    async def update(self, request=None):
        check = await request.json()
        check_uuid = check.get('uuid')
        check_id = check.get('id')

        message = dict(status='ok')

        if not check_id or not check_uuid:
            return json_response(status=400)

        if self.hashing.select(check_uuid) != self.name:
            return json_response(data=message, status=202)
        job = self.scheduler.get_job(str(check_uuid))

        if job:
            scheduled_check, = job.args
            timestamp = scheduled_check.get('timestamp', 0)

            if timestamp > check['timestamp']:
                return json_response(data=message, status=202)
            message = dict(status='deleted')
            self.remove_job(check_uuid)

        if any([trigger['enabled'] for trigger in check['triggers']]):
            self.schedule_check(check)
            message = dict(status='scheduled')

        return json_response(data=message, status=202)

    def wait_and_kill(self, sig):
        logger.warning('Got `%s` signal. Preparing scheduler to exit ...', sig)
        self.scheduler.shutdown()
        self.loop.stop()

    def register_exit_signals(self):
        for sig in ['SIGQUIT', 'SIGINT', 'SIGTERM']:
            logger.info('Registering handler for `%s` signal '
                        'in current event loop ...', sig)
            self.loop.add_signal_handler(
                getattr(signal, sig),
                self.wait_and_kill, sig
            )

    def start(self, loop=None):
        """Start scheduler."""
        self.setup(loop=loop)
        self.register_exit_signals()
        self.scheduler.start()

        logger.info(
            'Press Ctrl+%s to exit.', 'Break' if os.name == 'nt' else 'C'
        )
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        logger.info('Scheduler was stopped!')
