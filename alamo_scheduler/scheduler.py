# -*- coding: utf-8 -*-
import asyncio
import json
import logging
import os
import random
from datetime import datetime, timedelta

import pytz
from aiomeasures import StatsD
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from kafka.consumer.kafka import KafkaConsumer
from requests import Session, RequestException

from alamo_scheduler.conf import settings
from alamo_scheduler.zero_mq import ZeroMQQueue

logger = logging.getLogger(__name__)


class AlamoScheduler(object):
    message_queue = None

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.kafka_consumer = KafkaConsumer(
            settings.KAFKA__TOPIC,
            group_id=settings.KAFKA__GROUP,
            bootstrap_servers=settings.KAFKA__HOSTS.split(',')
        )
        self.statsd = self.initialize_statsd()

    def initialize_statsd(self):
        host = 'udp://{}:{}'.format(settings.STATSD__STATSD_HOST,
                                    settings.STATSD__STATSD_PORT)
        return StatsD(addr=host, prefix=settings.STATSD__STATSD_PREFIX)

    def setup(self):
        self.message_queue = ZeroMQQueue(
            settings.ZERO_MQ__HOST,
            settings.ZERO_MQ__PORT
        )
        self.message_queue.connect()

    def retrieve_all_jobs(self):
        checks, page = [], 1

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
                checks.extend(data['results'])
                page += 1
                if not data['next']:
                    break

        except (RequestException, ValueError, TypeError) as e:
            logger.error('Unable to retrieve jobs. `%s`', e)

        return checks

    def _verbose(self, message):
        if settings.DEFAULT__VERBOSE:
            logger.debug(message)

    def _schedule_check(self, check):
        """Schedule check."""

        self.statsd.incr('_scheduled_check', 1)
        logger.info(
            'Check `%s:%s` scheduled!', check['id'], check['name']
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

    def schedule_job(self, check):
        """Schedule new job."""
        try:
            check['fields']['frequency'] = int(check['fields']['frequency'])
            logger.info(
                'Scheduling check `%s` with id `%s` and interval `%s`',
                check['name'], check['id'], check['fields']['frequency']
            )
            jitter = random.randint(0, check['fields']['frequency'])
            first_run = datetime.now() + timedelta(seconds=jitter)
            self.scheduler.add_job(
                self._schedule_check, 'interval',
                seconds=check['fields']['frequency'],
                misfire_grace_time=settings.JOBS__MISFIRE_GRACE_TIME,
                max_instances=settings.JOBS__MAX_INSTANCES,
                coalesce=settings.JOBS__COALESCE,
                id=str(check['id']),
                next_run_time=first_run,
                args=(check,)
            )
        except KeyError as e:
            logger.exception('Failed to schedule check: %s. Exception: %s',
                             check, e)

    def consumer_messages(self):
        logger.debug('Fetching messages from kafka.')
        checks = {}
        messages = []
        for message in self.kafka_consumer.fetch_messages():
            logger.debug('Retrieved message `%s`', message)
            messages.append(json.loads(message.value.decode('utf-8')))

        for check in messages:
            timestamp = checks.get(check['id'], {}).get('timestamp', 0)
            if timestamp < check['timestamp']:
                checks[check['id']] = check

        for check_id, check in checks.items():
            logger.info(
                'New check definition retrieved from kafka: `%s`', check
            )
            job = self.scheduler.get_job(str(check_id))

            if job:
                scheduled_check, = job.args

                timestamp = scheduled_check.get('timestamp', 0)
                # outdated message
                if timestamp > check['timestamp']:
                    continue

                self.remove_job(check['id'])

            if any([trigger['enabled'] for trigger in check['triggers']]):
                self.schedule_job(check)

        logger.debug('Consumed %s checks from kafka.', len(checks))

    def start(self):
        """Start scheduler."""
        self.setup()
        checks = self.retrieve_all_jobs()
        self.scheduler.add_job(
            self.consumer_messages, 'interval',
            seconds=settings.KAFKA__INTERVAL
        )

        for check in checks:
            self.schedule_job(check)

        self.scheduler.start()
        self._verbose('Press Ctrl+{0} to exit.'.format(
            'Break' if os.name == 'nt' else 'C'))

        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass
