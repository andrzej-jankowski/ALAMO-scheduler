# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import random
import signal
from datetime import datetime, timedelta

from alamo_common import aiostats
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.jobstores.base import JobLookupError, ConflictingIdError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc as pytz_utc

from alamo_scheduler.aioweb import server, json_response
from alamo_scheduler.conf import settings
from alamo_scheduler.zero_mq import ZeroMQQueue

logger = logging.getLogger(__name__)


class AlamoScheduler(object):
    message_queue = None
    loop = handler = None

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
        self.message_queue = ZeroMQQueue(
            settings.ZERO_MQ_HOST,
            settings.ZERO_MQ_PORT
        )
        self.message_queue.connect()
        self.scheduler.add_listener(self.event_listener,
                                    EVENT_JOB_ERROR | EVENT_JOB_MISSED)

    @aiostats.increment()
    def _schedule_check(self, check):
        """Schedule check."""
        logger.info(
            'Check `%s:%s` scheduled!', check['uuid'], check['name']
        )

        check['scheduled_time'] = datetime.now(tz=pytz_utc).isoformat()
        self.message_queue.send(check)

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

    def checks(self, request=None):
        if request.method == 'GET':
            uuid = request.match_info.get('uuid', '<unknown>')
            job = self.scheduler.get_job(uuid)
            if job is None:
                return json_response(
                    data={'detail': 'Check does not exists.'}, status=404
                )

            check, = job.args
            return json_response(data=check)

        elif request.method == 'POST':
            return self.update(request)

    def update(self, request=None):
        data = yield from request.json()
        check_uuid = data.get('uuid', None)
        check_id = data.get('id', None)
        should_be_scheduled = False

        if not check_id or not check_uuid:
            return json_response(status=400)

        if check_id % settings.SCHEDULER_COUNT == settings.SCHEDULER_NR:
            should_be_scheduled = True

        job = self.scheduler.get_job(str(check_uuid))
        message = {'status': 'ok'}

        if job:
            self.remove_job(check_uuid)
            message = {'status': 'removed'}

        if any([trigger['enabled'] for trigger in data['triggers']]) \
                and should_be_scheduled:
            self.schedule_check(data)
            message = {'status': 'scheduled'}

        return json_response(data=message, status=202)

    @asyncio.coroutine
    def wait_and_kill(self, sig):
        logger.warning('Got `%s` signal. Preparing scheduler to exit ...', sig)
        self.scheduler.shutdown()

        yield from asyncio.sleep(0.2)
        for task in asyncio.Task.all_tasks():
            task.cancel()
        self.loop.run_until_complete(server.finish_connections())
        self.loop.stop()

    def register_exit_signals(self):
        for sig in ['SIGQUIT', 'SIGINT', 'SIGTERM']:
            logger.info('Registering handler for `%s` signal '
                        'in current event loop ...', sig)
            self.loop.add_signal_handler(
                getattr(signal, sig), asyncio.async,
                self.wait_and_kill(sig)
            )

    def start(self, loop=None):
        """Start scheduler."""
        self.setup(loop=loop)
        self.register_exit_signals()
        self.scheduler.start()

        srv, self.handler = self.loop.run_until_complete(
            server.init(self.loop)
        )

        logger.info('Press Ctrl+{0} to exit.'.format(
            'Break' if os.name == 'nt' else 'C'))
        self.loop.run_forever()
        logger.info('Scheduler was stopped!')
