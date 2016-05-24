# -*- coding: utf-8 -*-
import asyncio
import json
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, Mock, call
from uuid import uuid4

from aiohttp.client_reqrep import ClientResponse
from apscheduler.events import (
    JobExecutionEvent,
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED
)
from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from ddt import data, ddt, unpack

from alamo_scheduler.conf import settings
from alamo_scheduler.scheduler import AlamoScheduler
from tests.base import CHECK_TEST_DATA


@ddt
class TestAlamoScheduler(TestCase):
    @patch('alamo_scheduler.scheduler.KafkaConsumer')
    @patch('alamo_scheduler.scheduler.ZeroMQQueue', Mock())
    def setUp(self, *args):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.scheduler = AlamoScheduler(loop=self.loop)
        self.check = deepcopy(CHECK_TEST_DATA)
        self.check_two = deepcopy(CHECK_TEST_DATA)
        self.check_two['uuid'] = str(uuid4())
        self.connection = Mock()

    def tearDown(self):
        self.loop.close()
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
        queue_mock = Mock()
        self.scheduler.message_queue = queue_mock
        self.scheduler._schedule_check(self.check)

        self.assertTrue(queue_mock.send.called)

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
        request = Mock(match_info=dict(uuid=self.check['uuid']))
        self.scheduler.scheduler.start()
        self.scheduler.schedule_check(self.check)

        response = self.scheduler.checks(request)
        self.assertIn(self.check['uuid'], response.text)

    def test_checks_endpoint_with_not_provided_uuid(self):
        request = Mock(match_info=dict())

        response = self.scheduler.checks(request)
        self.assertIn('Check does not exists.', response.text)

    @patch('alamo_scheduler.scheduler.ClientSession.get')
    def test_job_retrieving(self, get_mock):
        queue_mock = Mock()
        self.scheduler.message_queue = queue_mock

        def _get_response():
            """Create new partially mocked response object."""
            response = ClientResponse('get', settings.CHECK_API_URL)
            response.headers = {'CONTENT-TYPE': 'application/json'}
            response._post_init(self.loop)
            response._setup_connection(self.connection)
            return response

        def _get_future(result):
            """Wrap `result` as Future object."""
            fut = asyncio.Future(loop=self.loop)
            fut.set_result(result)
            return fut

        first_result = _get_future(
            json.dumps({'next': True, 'results': [self.check]}).encode('utf8')
        )
        second_result = _get_future(
            json.dumps({'next': False, 'results': [self.check_two]}).encode(
                'utf8'
            )
        )
        first_response = _get_response()
        second_response = _get_response()
        first_response.content = Mock()
        first_response.content.read.side_effect = [first_result]
        second_response.content = Mock()
        second_response.content.read.side_effect = [second_result]
        # each call should return different response object
        get_mock.side_effect = [
            _get_future(first_response), _get_future(second_response)
        ]

        self.loop.run_until_complete(
            self.scheduler.retrieve_all_jobs()
        )
        calls = [
            call(settings.CHECK_API_URL,
                 params={'page': 1, 'page_size': settings.PAGE_SIZE}),
            call(settings.CHECK_API_URL,
                 params={'page': 2, 'page_size': settings.PAGE_SIZE})
        ]
        get_mock.assert_has_calls(calls, any_order=True)
        self.assertEqual(len(self.scheduler.scheduler.get_jobs()), 2)

    @patch('alamo_scheduler.scheduler.ZeroMQQueue')
    def test_setup(self, zmq):
        zmq_mock = Mock()
        zmq.return_value = zmq_mock
        loop = self.loop

        @asyncio.coroutine
        def retrieve(*args, **kwargs):
            yield from asyncio.sleep(0.1)

        def run_later():
            loop.run_until_complete(self.scheduler.wait_and_kill('SIGINT'))

        loop.call_later(0.2, run_later)
        self.scheduler.retrieve_all_jobs = retrieve
        self.scheduler.fetch_messages = Mock()
        self.scheduler.start(loop=self.loop)
        self.assertTrue(zmq_mock.connect.called)
        self.assertFalse(loop.is_running())
