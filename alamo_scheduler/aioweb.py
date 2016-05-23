# -*- coding: utf-8 -*-
import asyncio
import logging

from alamo_scheduler.conf import settings
from pip import get_installed_distributions

from aiohttp.client import ClientSession
from aiohttp.web import Application, Response, json_response

logger = logging.getLogger(__name__)

__all__ = ['ClientSession', 'json_response', 'Response',
           'SchedulerServerApplication']


class SchedulerServerApplication(object):
    _app = None
    _srv = _handler = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(
                SchedulerServerApplication, cls
            ).__new__(cls, *args)
        return cls._inst

    @asyncio.coroutine
    def init(self, loop=None):
        loop = loop or asyncio.get_event_loop()
        if self._srv is not None and self._handler is not None:
            return self._srv, self._handler
        self.configure_contract()
        self._handler = self.app.make_handler()

        self._srv = yield from loop.create_server(
            self._handler, settings.SERVER_HOST, settings.SERVER_PORT
        )
        logger.info('Server started at http://{}:{}'.format(
            settings.SERVER_HOST, settings.SERVER_PORT
        ))
        return self._srv, self._handler

    @asyncio.coroutine
    def finish_connections(self):
        yield from self._handler.finish_connections()
        self._srv = self._handler = None

    @property
    def app(self):
        if self._app is None:
            self.setup()
        return self._app

    def ping(self, request):
        return Response(body=b'pong')

    def dependencies(self, request):
        installed_packages = get_installed_distributions(local_only=True)
        dependencies = [dict(name=i.key, version=i.version)
                        for i in installed_packages]
        return json_response(data=dict(dependencies=dependencies))

    def info(self, request):
        package = 'alamo-scheduler'
        version = next(iter([p.version for p in
                             get_installed_distributions(local_only=True)
                             if p.key == package]), '<unknown>')

        return json_response(data=dict(title=package, version=version))

    def endpoints(self, request):
        endpoints = []
        router = request.app.router
        for resource in router._resources:
            path = getattr(resource, '_path', None)
            if path is None:
                path = getattr(resource, '_formatter')
            routes = resource._routes
            if '/status/' in path:
                continue
            for route in routes:
                endpoints.append(dict(
                    path=path, method=route.method,
                    accept='application/json', tags=[]
                ))
        return json_response(data=dict(endpoints=endpoints))

    def setup(self):
        if self._app is None:
            self._app = Application(loop=asyncio.get_event_loop())

    def add_route(self, *args, **kwargs):
        """Add route to server."""
        self.app.router.add_route(*args, **kwargs)

    def configure_contract(self):
        self.add_route('GET', '/status/dependencies', self.dependencies)
        self.add_route('GET', '/status/ping', self.ping)
        self.add_route('GET', '/status/info', self.info)
        self.add_route('GET', '/status/public-endpoints', self.endpoints)


server = SchedulerServerApplication()
