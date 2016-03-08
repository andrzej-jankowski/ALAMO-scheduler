# -*- coding: utf-8 -*-
from unittest import TestCase
from unittest.mock import patch


from ddt import data, ddt, unpack

from apscheduler.events import (
    JobExecutionEvent,
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED)

from alamo_scheduler.scheduler import AlamoScheduler


@ddt
class TestAlamoScheduler(TestCase):

    @patch('alamo_scheduler.scheduler.KafkaConsumer')
    @patch('alamo_scheduler.scheduler.settings')
    @patch('alamo_scheduler.scheduler.AlamoScheduler.initialize_statsd')
    def setUp(self, *args):
        self.scheduler = AlamoScheduler()
        self.bad_sample_check = {'description': '',
                                 'entity_name': 'sample-entity',
                                 'environment': 'prod',
                                 'fields': {'debounce': '2',
                                            'expected_num_hosts': '1',
                                            'metric': 'foo.bar'},
                                 'id': 1,
                                 'integration_key': '123456',
                                 'name': 'Sample Check',
                                 'service_name': 'sample-service',
                                 'tags': [],
                                 'triggers': [{'condition': '==',
                                               'enabled': True,
                                               'id': 1,
                                               'name': 'Sample Trigger',
                                               'severity': 'ERROR',
                                               'tags': [],
                                               'threshold': '1'}],
                                 'type': 'APP.Cabot.metrics'}

    def test_schedule_job(self):
        with self.assertLogs('alamo_scheduler.scheduler', level='ERROR'):
            self.scheduler.schedule_job(self.bad_sample_check)

    @unpack
    @data({'type': EVENT_JOB_ERROR, 'log_level': 'ERROR'},
          {'type': EVENT_JOB_MISSED, 'log_level': 'WARNING'})
    @patch('alamo_scheduler.scheduler.AlamoScheduler.initialize_statsd')
    def test_event_listener(self, *args, **kwargs):
        event = JobExecutionEvent(kwargs['type'], 1, None, '1970-2-2')
        with self.assertLogs('alamo_scheduler.scheduler',
                             level=kwargs['log_level']):
            self.scheduler.event_listener(event)
