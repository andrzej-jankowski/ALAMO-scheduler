# -*- coding: utf-8 -*-
import logging

from datetime import datetime
from pytz import utc as pytz_utc

from alamo_scheduler.conf import settings
from alamo_scheduler.zero_mq import ZeroMQQueue

logger = logging.getLogger(__name__)


class DefaultSender(object):
    def __init__(self):
        self.queue = ZeroMQQueue(
            settings.ZERO_MQ_HOST,
            settings.ZERO_MQ_PORT
        )
        self.queue.connect()

    def send(self, check):
        """Schedule check."""
        logger.info(
            'Check `%s:%s` scheduled.', check['uuid'], check['name']
        )

        check['scheduled_time'] = datetime.now(tz=pytz_utc).isoformat()
        self.queue.send(check)
