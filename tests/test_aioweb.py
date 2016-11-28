# -*- coding: utf-8 -*-
import asyncio
from unittest import TestCase
from urllib.parse import urljoin

from alamo_scheduler.aioweb import ClientSession, json_response
from alamo_scheduler.aioweb import SchedulerServerApplication
from alamo_scheduler.conf import settings


class RequestClient(object):
    """Basic http client for tests.

    It can perform async requests in sync manner (ready to use in tests).
    """

    def __init__(self):
        self.base = 'http://{}:{}'.format(
            settings.SERVER_HOST, settings.SERVER_PORT
        )
        self.loop = asyncio.get_event_loop()
        self._session = ClientSession()

    @asyncio.coroutine
    def _request(self, method, url, *args, **kwargs):
        json = kwargs.pop('json', False)
        coro = getattr(self._session, method)
        url = urljoin(self.base, url)
        response = yield from coro(url, *args, **kwargs)
        if json:
            data = yield from response.json()
        else:
            data = yield from response.read()
        yield from response.release()
        return data

    def get(self, url, *args, **kwargs):
        return self.loop.run_until_complete(
            self._request('get', url, *args, **kwargs)
        )


class ServerTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(cls.loop)
        cls.client = RequestClient()
        cls.server = SchedulerServerApplication()
        cls.server.add_route('GET', '/foo', cls.foo)
        cls.server.init(loop=cls.loop)

    @classmethod
    def tearDownClass(cls):
        cls.server.finish_connections()
        cls.loop.close()
        asyncio.set_event_loop(None)

    @staticmethod
    def foo(*args):
        return json_response(dict(foo='bar'))

    def test_ping_endpoint(self):
        data = self.client.get('/status/ping')
        self.assertEqual(data, b'pong')

    def test_dependencies_endpoint(self):
        resp_data = self.client.get('/status/dependencies', json=True)
        self.assertIn('dependencies', resp_data)
        self.assertTrue(len(resp_data['dependencies']) != 0)

    def test_info_endpoint(self):
        resp_data = self.client.get('/status/info', json=True)
        self.assertIn('title', resp_data)
        self.assertIn('version', resp_data)
        self.assertEqual(resp_data['title'], 'alamo-scheduler')

    def test_endpoints_endpoint(self):
        resp_data = self.client.get('/status/public-endpoints', json=True)
        # contract endpoint are not visible here
        self.assertEqual(resp_data['endpoints'], [
            {
                'accept': 'application/json', 'method': 'GET', 'path': '/foo',
                'tags': []
            },
            {
                'path': '/', 'method': 'GET', 'accept': 'application/json',
                'tags': []
            }
        ])

    def test_custom_endpoint(self):
        resp_data = self.client.get('/foo', json=True)
        # contract endpoint are not visible here
        self.assertEqual(resp_data['foo'], 'bar')
