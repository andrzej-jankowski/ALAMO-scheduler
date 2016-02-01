# -*- coding: utf-8 -*-
from unittest import TestCase

from alamo_scheduler.scheduler import AlamoScheduler

from unittest.mock import patch


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
