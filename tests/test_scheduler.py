# -*- coding: utf-8 -*-
import asyncio
import json
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, Mock
from uuid import uuid4

from apscheduler.events import (
    JobExecutionEvent,
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED
)
from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from ddt import data, ddt, unpack
from stevedore import driver

from alamo_scheduler.hashing import Hashing
from alamo_scheduler.scheduler import AlamoScheduler
from tests.base import CHECK_TEST_DATA


@ddt
class TestAlamoScheduler(TestCase):
    plugin_namespace = 'pl.allegro.tech.monitoring.alamo.drivers'

    @patch('alamo_scheduler.drivers.default.sender.ZeroMQQueue', Mock())
    def setUp(self, *args):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.scheduler = AlamoScheduler(loop=self.loop)
        self.scheduler.hashing = Hashing(['scheduler1'])
        self.scheduler.name = 'scheduler1'
        self.scheduler.sender = driver.DriverManager(
            namespace=self.plugin_namespace,
            name='default',
            invoke_on_load=True,
        )
        self.check = deepcopy(CHECK_TEST_DATA)
        self.check_two = deepcopy(CHECK_TEST_DATA)
        self.check_two['uuid'] = str(uuid4())
        self.connection = Mock()

    def tearDown(self):
        self.loop.stop()
        asyncio.set_event_loop(None)

    def test_schedule_job(self):
        with self.assertLogs('alamo_scheduler.scheduler', level='ERROR'):
            self.check.pop('uuid')
            self.scheduler.schedule_check(self.check)

    @unpack
    @data({'type': EVENT_JOB_ERROR, 'log_level': 'ERROR'},
          {'type': EVENT_JOB_MISSED, 'log_level': 'WARNING'})
    def test_event_listener(self, *args, **kwargs):
        event = JobExecutionEvent(kwargs['type'], 1, None, '1970-2-2')
        with self.assertLogs('alamo_scheduler.scheduler',
                             level=kwargs['log_level']):
            self.scheduler.event_listener(event)

    def test_schedule_check(self):
        send_mock = Mock()
        self.scheduler.sender = send_mock

        def run_later():
            self.scheduler._schedule_check(self.check)
            self.scheduler.wait_and_kill('SIGINT')

        self.scheduler.loop = self.loop
        self.scheduler.scheduler.start()
        self.loop.call_later(0.5, run_later)
        self.loop.run_forever()

        self.assertTrue(send_mock.driver.send.called)

    def test_remove_job(self):
        job_id = str(self.check['uuid'])
        self.scheduler.schedule_check(self.check)
        self.scheduler.scheduler.start()
        self.assertEqual(len(self.scheduler.scheduler.get_jobs()), 1)
        self.scheduler.remove_job(job_id)
        self.assertEqual(len(self.scheduler.scheduler.get_jobs()), 0)

    def test_removing_non_existing_job(self):
        try:
            self.scheduler.remove_job('fake_job')
        except JobLookupError:
            self.fail('Removing non existing job raise an unexpectedly.')

    def test_conflict_with_adding_the_same_job(self):
        self.scheduler.scheduler.start()
        self.scheduler.schedule_check(self.check)
        try:
            self.scheduler.schedule_check(self.check)
        except ConflictingIdError:
            self.fail(
                'Scheduling duplicated check raise an error unexpectedly.'
            )

    def test_checks_endpoint(self):
        request = Mock(match_info=dict(uuid=self.check['uuid']), method='GET')
        self.scheduler.scheduler.start()
        self.scheduler.schedule_check(self.check)

        response = self.loop.run_until_complete(self.scheduler.checks(request))
        self.assertIn(self.check['uuid'], response.text)

    @patch('alamo_scheduler.scheduler.json_response')
    def test_checks_update_endpoint(self, json_response_mock):
        self.scheduler.scheduler.start()

        check = self.check

        async def _json():
            return check

        request = Mock()
        request.json = _json

        response = self.loop.run_until_complete(
            self.scheduler.update(request)
        )

        self.assertEqual(list(response), [])
        json_response_mock.assert_called_with(
            data={'status': 'scheduled'}, status=202
        )

        # test if already scheduled check will be removed
        check['triggers'] = []
        response = self.loop.run_until_complete(
            self.scheduler.update(request)
        )

        self.assertEqual(list(response), [])
        json_response_mock.assert_called_with(
            data={'status': 'deleted'}, status=202
        )

    def test_checks_endpoint_with_not_provided_uuid(self):
        request = Mock(match_info=dict(), method='GET')

        response = self.loop.run_until_complete(
            self.scheduler.checks(request)
        )
        self.assertDictEqual(
            json.loads(response.text), dict(count=0, results=[])
        )

    @patch('alamo_scheduler.drivers.default.sender.ZeroMQQueue')
    def test_setup(self, zmq):
        zmq_mock = Mock()
        zmq.return_value = zmq_mock
        loop = self.loop

        async def retrieve(*args, **kwargs):
            await asyncio.sleep(0.1)

        def run_later():
            self.scheduler.wait_and_kill('SIGINT')

        loop.call_later(0.2, run_later)
        self.scheduler.retrieve_all_jobs = retrieve
        self.scheduler.fetch_messages = Mock()
        self.scheduler.start(loop=self.loop)
        self.loop.close()
        self.assertTrue(zmq_mock.connect.called)
        self.assertFalse(loop.is_running())

    @patch('alamo_scheduler.scheduler.PushChecks')
    def test_hook(self, push_checks):
        job_id = 'push_checks'
        self.check['uuid'] = job_id
        self.scheduler.schedule_check(self.check)
        self.scheduler.scheduler.start()
        self.assertEqual(len(self.scheduler.scheduler.get_jobs()), 1)
        self.assertEqual(None, self.scheduler.hook())
        self.assertEqual(len(self.scheduler.scheduler.get_jobs()), 0)
