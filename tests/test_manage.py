# -*- coding: utf-8 -*-
from unittest import TestCase
from unittest.mock import Mock, patch

import asyncio
from alamo_scheduler.manage import AlamoManager, execute
from asyncio.test_utils import TestLoop


class TestAlamoWorker(TestCase):
    def setUp(self):
        self.loop = TestLoop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()
        asyncio.set_event_loop(None)

    @patch('alamo_scheduler.manage.AlamoScheduler')
    def test_manager_execute_method(self, scheduler):
        scheduler_mock = Mock()
        scheduler.return_value = scheduler_mock
        self.manager = AlamoManager()
        self.manager.execute()
        self.assertTrue(scheduler_mock.start.called)

    @patch('alamo_scheduler.manage.AlamoManager.execute')
    def test_execute_method(self, execute_mock):
        execute()
        self.assertTrue(execute_mock.called)
