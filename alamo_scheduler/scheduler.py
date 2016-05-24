# -*- coding: utf-8 -*-
import asyncio
import json
import logging
import os
import random
import signal
from datetime import datetime, timedelta

from aiohttp import BasicAuth
from alamo_common import aiostats
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.jobstores.base import JobLookupError, ConflictingIdError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from kafka import KafkaConsumer
from pytz import utc as pytz_utc

from alamo_scheduler.aioweb import server, json_response, ClientSession
from alamo_scheduler.conf import settings
from alamo_scheduler.zero_mq import ZeroMQQueue

logger = logging.getLogger(__name__)
loop = asyncio.get_event_loop()


class AlamoScheduler(object):
    message_queue = None
    handler = None

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.kafka_consumer = KafkaConsumer(
            settings.KAFKA_TOPIC,
            group_id=settings.KAFKA_GROUP,
            bootstrap_servers=settings.KAFKA_HOSTS.split(','),
            consumer_timeout_ms=100
        )

    def setup(self):
        self.message_queue = ZeroMQQueue(
            settings.ZERO_MQ_HOST,
            settings.ZERO_MQ_PORT
        )
        self.message_queue.connect()
        self.scheduler.add_listener(self.event_listener,
                                    EVENT_JOB_ERROR | EVENT_JOB_MISSED)

    @asyncio.coroutine
    @aiostats.timer()
    def retrieve_all_jobs(self):
        page = 1

        with ClientSession(
                loop=loop,
                auth=BasicAuth(
                    settings.CHECK_USER, settings.CHECK_PASSWORD
                )
        ) as session:
            while True:
                params = {'page': page, 'page_size': settings.PAGE_SIZE}
                try:
                    response = yield from session.get(
                        settings.CHECK_API_URL,
                        params=params
                    )
                    data = yield from response.json()
                    for check in data['results']:
                        self.schedule_check(check)
                    yield from response.release()
                    page += 1
                    if not data['next']:
                        break

                except (ValueError, TypeError) as e:
                    logger.error('Unable to retrieve jobs. `%s`', e)

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

    @aiostats.increment(metric_name='kafka.consumer.runs')
    @aiostats.timer(metric_name='kafka.consumer.fetch_messages')
    def fetch_messages(self):
        logger.debug('Fetching messages from kafka.')
        checks = {}
        messages = []
        for message in self.kafka_consumer:
            logger.debug('Retrieved message `%s`', message)
            kafka_message = json.loads(message.value.decode('utf-8'))
            if isinstance(kafka_message, list):
                for km in kafka_message:
                    messages.append(km)
            elif isinstance(kafka_message, dict):
                messages.append(kafka_message)

        for check in messages:
            timestamp = checks.get(check['uuid'], {}).get('timestamp', 0)
            if timestamp < check['timestamp']:
                checks[check['uuid']] = check

        for check_uuid, check in checks.items():
            logger.info(
                'New check definition retrieved from kafka: `%s`', check
            )
            job = self.scheduler.get_job(str(check_uuid))

            if job:
                scheduled_check, = job.args

                timestamp = scheduled_check.get('timestamp', 0)
                # outdated message
                if timestamp > check['timestamp']:
                    continue

                self.remove_job(check['uuid'])

            if any([trigger['enabled'] for trigger in check['triggers']]):
                self.schedule_check(check)

        logger.debug('Consumed %s checks from kafka.', len(checks))

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
        uuid = request.match_info.get('uuid', '<unknown>')
        job = self.scheduler.get_job(uuid)
        if job is None:
            return json_response(
                data={'detail': 'Check does not exists.'}, status=404
            )

        check, = job.args
        return json_response(data=check)

    @asyncio.coroutine
    def wait_and_kill(self, sig):
        logger.warning('Got `%s` signal. Preparing scheduler to exit ...', sig)
        self.scheduler.shutdown()

        yield from asyncio.sleep(0.2)
        for task in asyncio.Task.all_tasks():
            task.cancel()
        loop.run_until_complete(server.finish_connections())
        loop.stop()

    def register_exit_signals(self):
        for sig in ['SIGQUIT', 'SIGINT', 'SIGTERM']:
            logger.info('Registering handler for `%s` signal '
                        'in current event loop ...', sig)
            loop.add_signal_handler(
                getattr(signal, sig), asyncio.async,
                self.wait_and_kill(sig)
            )

    def start(self):
        """Start scheduler."""
        self.setup()
        self.register_exit_signals()
        self.scheduler.start()

        srv, self.handler = loop.run_until_complete(server.init(loop))
        loop.run_until_complete(self.retrieve_all_jobs())
        self.schedule_job(self.fetch_messages,
                          seconds=settings.KAFKA_INTERVAL)

        logger.info('Press Ctrl+{0} to exit.'.format(
            'Break' if os.name == 'nt' else 'C'))
        loop.run_forever()
        logger.info('Scheduler was stopped!')
