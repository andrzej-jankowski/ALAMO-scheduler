# -*- coding: utf-8 -*-

import logging

from requests import Session, RequestException

from alamo_scheduler.conf import settings

logger = logging.getLogger(__name__)


class PushChecks(object):

    def __init__(self):
        self.url = settings.CHECK_PUSH_URL
        self.session = Session()
        self.session.auth = (settings.CHECK_USER, settings.CHECK_PASSWORD)
        self.session.headers.update({'content-type': 'application/json'})

    def trigger(self):
        logger.info('Triggering check feeder')

        try:
            response = self.session.get(self.url)
            data = response.json()
            logger.info('Scheduled: {}'.format(data['scheduled']))
            return True
        except (KeyError, ValueError, RequestException) as e:
            logger.error('Unable to trigger check feeder: %s' % e)

        return False
