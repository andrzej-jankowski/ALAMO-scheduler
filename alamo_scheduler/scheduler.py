# -*- coding: utf-8 -*-
import asyncio
import json
import logging
import os
import random
from datetime import datetime, timedelta

import pytz
from aiohttp.web import Response
from aiomeasures import StatsD
from alamo_common.io import stats
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.jobstores.base import JobLookupError, ConflictingIdError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from kafka import KafkaConsumer
from requests import Session, RequestException

from alamo_scheduler.conf import settings
from alamo_scheduler.server import server
from alamo_scheduler.zero_mq import ZeroMQQueue

logger = logging.getLogger(__name__)


class AlamoScheduler(object):
    message_queue = None

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.kafka_consumer = KafkaConsumer(
            settings.KAFKA__TOPIC,
            group_id=settings.KAFKA__GROUP,
            bootstrap_servers=settings.KAFKA__HOSTS.split(','),
            consumer_timeout_ms=100
        )

    def initialize_statsd(self):
        host = 'udp://{}:{}'.format(settings.STATSD_HOST,
                                    settings.STATSD_PORT)
        return StatsD(addr=host, prefix=settings.STATSD_PREFIX)

    def setup(self):
        self.message_queue = ZeroMQQueue(
            settings.ZERO_MQ__HOST,
            settings.ZERO_MQ__PORT
        )
        self.message_queue.connect()
        self.scheduler.add_listener(self.event_listener,
                                    EVENT_JOB_ERROR | EVENT_JOB_MISSED)

    @stats.timer()
    def retrieve_all_jobs(self):
        page = 1

        try:
            session = Session()

            while True:
                params = {'page': page, 'page_size': 1000}
                response = session.get(
                    settings.CHECK__API_URL,
                    auth=(settings.CHECK__USER, settings.CHECK__PASSWORD),
                    params=params
                )
                data = response.json()
                yield data['results']
                page += 1
                if not data['next']:
                    break

        except (RequestException, ValueError, TypeError) as e:
            logger.error('Unable to retrieve jobs. `%s`', e)

    def _verbose(self, message):
        if settings.DEFAULT__VERBOSE:
            logger.debug(message)

    @stats.increment()
    def _schedule_check(self, check):
        """Schedule check."""
        logger.info(
            'Check `%s:%s` scheduled!', check['uuid'], check['name']
        )

        check['scheduled_time'] = datetime.now(tz=pytz.utc).isoformat()
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
            frequency = 30
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
                misfire_grace_time=settings.JOBS__MISFIRE_GRACE_TIME,
                max_instances=settings.JOBS__MAX_INSTANCES,
                coalesce=settings.JOBS__COALESCE,
                **kwargs
            )
        except ConflictingIdError as e:
            logger.error(e)

    @stats.increment(metric_name='kafka.consumer.runs')
    @stats.timer(metric_name='kafka.consumer.fetch_messages')
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
            stats.increment.incr('job.missed')
            logger.warning("Job %s scheduler for %s missed.", event.job_id,
                           event.scheduled_run_time)
        elif event.code == EVENT_JOB_ERROR:
            stats.increment.incr('job.error')
            logger.error("Job %s scheduled for %s failed. Exc: %s",
                         event.job_id,
                         event.scheduled_run_time,
                         event.exception)

    def checks(self, request=None):
        uuid = request.match_info.get('uuid', '<unknown>')
        job = self.scheduler.get_job(uuid)
        if job is None:
            return Response(
                body=b'{"detail": "Check does not exists."}',
                status=404)

        resp = Response()
        check, = job.args
        resp.body = json.dumps(check).encode('utf8')

        return resp

    def start(self):
        """Start scheduler."""
        self.setup()
        self.scheduler.start()
        for checks in self.retrieve_all_jobs():
            for check in checks:
                self.schedule_check(check)

        self.schedule_job(self.fetch_messages,
                          seconds=settings.KAFKA__INTERVAL)

        self._verbose('Press Ctrl+{0} to exit.'.format(
            'Break' if os.name == 'nt' else 'C'))
        event_loop = asyncio.get_event_loop()

        try:
            srv, handler = event_loop.run_until_complete(
                server.init(event_loop)
            )
            event_loop.run_forever()
        except (KeyboardInterrupt, SystemExit):
            event_loop.run_until_complete(handler.finish_connections())
            d = ''
            self.scheduler.shutdown()
            pass
