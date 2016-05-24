# -*- coding: utf-8 -*-
from unittest import TestCase
from unittest.mock import patch

from alamo_scheduler.manage import AlamoManager, execute


class TestAlamoWorker(TestCase):
    @patch('alamo_scheduler.scheduler.KafkaConsumer')
    @patch('alamo_scheduler.manage.AlamoScheduler.start')
    def test_manager_execute_method(self, start_mock, _):
        self.manager = AlamoManager()
        self.manager.execute()
        self.assertTrue(start_mock.called)

    @patch('alamo_scheduler.scheduler.KafkaConsumer')
    @patch('alamo_scheduler.manage.AlamoManager.execute')
    def test_execute_method(self, execute_mock, _):
        execute()
        self.assertTrue(execute_mock.called)
