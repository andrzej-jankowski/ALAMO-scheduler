# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import asyncio
import os
from datetime import datetime

from redis import StrictRedis
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from alamo_scheduler.fixtures.checks import (
    load_data_to_memory,
    generate_check_def
)

from alamo_scheduler.loggers import logger


class AlamoScheduler(object):
    def __init__(self, redis_host, redis_port, redis_db, cache_update_key,
                 misfire_grace_time=1,
                 max_instances=4, coalesce=True,
                 verbose=False):
        self.scheduler = AsyncIOScheduler()
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.cache_update_key = cache_update_key
        self.verbose = verbose
        self.misfire_grace_time = misfire_grace_time
        self.max_instances = max_instances
        self.coalesce = coalesce

    def load_checks(self):
        return load_data_to_memory(3000)

    def _verbose(self, message):
        if self.verbose:
            logger.debug(message)

    def _schedule_check(self, check, test):
        """Schedule check."""
        if 'check_{}'.format(test) == check['name']:
            self._verbose('{} Tick! Interval is: {}. The time is: {}'.
                          format(check['name'], check['interval'],
                                 datetime.now()))

    def _update_is_required(self):
        """Check if update is required."""
        conn = StrictRedis(host=self.redis_host, port=self.redis_port,
                           db=self.redis_db)

        return conn.get(self.cache_update_key)

    def _update_jobs(self):
        """Update jobs.
        Check in cache flag 'update_required' if it's set update checks.
        """

        if not self._update_is_required():
            return

        check_id = 900
        check = generate_check_def(check_id, 1)

        self.scheduler.remove_job(str(check_id))
        self.scheduler.add_job(
            self._schedule_check, 'interval', seconds=check['interval'],
            misfire_grace_time=self.misfire_grace_time,
            max_instances=self.max_instances,
            coalesce=self.coalesce,
            id=str(check_id),
            args=(check, check_id))

        self._verbose("Updating")

    def run(self):
        """Run scheduler."""
        checks = self.load_checks()
        self.scheduler.add_job(self._update_jobs,
                               'interval', seconds=10)
        for k, v in checks.items():
            self.scheduler.add_job(self._schedule_check, 'interval',
                                   seconds=v['interval'],
                                   misfire_grace_time=self.misfire_grace_time,
                                   max_instances=self.max_instances,
                                   coalesce=self.coalesce,
                                   id=str(k),
                                   args=(v, 900))
        self.scheduler.start()
        self._verbose('Press Ctrl+{0} to exit.'.format(
            'Break' if os.name == 'nt' else 'C'))

        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass
