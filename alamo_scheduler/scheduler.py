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
from kafka.client import KafkaClient
from kafka.consumer.simple import SimpleConsumer
from requests import Session, RequestException

from alamo_scheduler.conf import settings
from alamo_scheduler.zero_mq import ZeroMQQueue

logger = logging.getLogger(__name__)


class AlamoScheduler(object):
    message_queue = None

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        kafka_client = KafkaClient(settings.KAFKA__HOSTS)
        self.kafka_consumer = SimpleConsumer(
            kafka_client,
            settings.KAFKA__GROUP,
            settings.KAFKA__TOPIC
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
            logger.error('Unable to retrieve jobs. `{}`'.format(e))

        return checks

    def _verbose(self, message):
        if settings.DEFAULT__VERBOSE:
            logger.debug(message)

    def _schedule_check(self, check):
        """Schedule check."""

        self.statsd.incr('_scheduled_check', 1)
        logger.info(
            'Check `{}:{}` scheduled!'.format(check['id'], check['name'])
        )

        check['scheduled_time'] = datetime.now(tz=pytz.utc).isoformat()
        self.message_queue.send(check)

    def remove_job(self, job_id):
        """Remove job."""
        try:
            logger.info('Removing job for check id=`{}`'.format(job_id))
            self.scheduler.remove_job(str(job_id))
        except JobLookupError:
            pass

    def schedule_job(self, check):
        """Schedule new job."""
        check['fields']['frequency'] = int(check['fields']['frequency'])
        logger.info(
            'Scheduling check `{}` with id `{}` and interval `{}`'.format(
                check['name'], check['id'], check['fields']['frequency']
            )
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

    def consumer_messages(self):
        logger.debug('Fetching messages from kafka.')
        messages = self.kafka_consumer.get_messages(
            count=settings.KAFKA__MESSAGES_COUNT
        )
        for message in messages:
            _, message = message
            check = json.loads(message.value.decode('utf-8'))

            logger.info(
                'New check definition retrieved from kafka: `{}`'.format(check)
            )
            self.remove_job(check['id'])
            if any([trigger['enabled'] for trigger in check['triggers']]):
                self.schedule_job(check)

        logger.debug('Messages consumed.')

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
