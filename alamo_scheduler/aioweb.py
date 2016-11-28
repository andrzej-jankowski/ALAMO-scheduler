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

    def init(self, loop=None):
        loop = loop or self.app.loop
        backlog = 128

        self.configure_contract()

        self._handler = self.app.make_handler()
        self._server = loop.create_server(
            self._handler, settings.SERVER_HOST,
            settings.SERVER_PORT, backlog=backlog
        )
        self._srv, self._startup_res = loop.run_until_complete(
            asyncio.gather(self._server, self.app.startup(), loop=loop)
        )
        logger.info('Server started at http://{}:{}'.format(
            settings.SERVER_HOST, settings.SERVER_PORT
        ))

    def finish_connections(self):
        loop = self.app.loop
        self._srv.close()
        loop.run_until_complete(self._srv.wait_closed())
        loop.run_until_complete(self.app.shutdown())
        loop.run_until_complete(self._handler.finish_connections(60))
        loop.run_until_complete(self.app.cleanup())
        self._app = None

    @property
    def app(self):
        if self._app is None:
            self.setup()
        return self._app

    def setup(self):
        if self._app is None:
            self._app = Application(loop=asyncio.get_event_loop())

    async def ping(self, request):
        return Response(body=b'pong')

    async def dependencies(self, request):
        installed_packages = get_installed_distributions(local_only=True)
        dependencies = [dict(name=i.key, version=i.version)
                        for i in installed_packages]
        return json_response(data=dict(dependencies=dependencies))

    async def info(self, request):
        package = 'alamo-scheduler'
        version = next(iter([p.version for p in
                             get_installed_distributions(local_only=True)
                             if p.key == package]), '<unknown>')

        return json_response(data=dict(title=package, version=version))

    async def endpoints(self, request):
        endpoints = []
        router = request.app.router
        for resource in router.resources():
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

    def add_route(self, *args, **kwargs):
        """Add route to server."""
        self.app.router.add_route(*args, **kwargs)

    def add_get(self, *args, **kwargs):
        self.app.router.add_get(*args, **kwargs)

    def add_post(self, *args, **kwargs):
        self.app.router.add_post(*args, **kwargs)

    def configure_contract(self):
        self.add_route('GET', '/status/dependencies', self.dependencies)
        self.add_route('GET', '/status/ping', self.ping)
        self.add_route('GET', '/status/info', self.info)
        self.add_route('GET', '/status/public-endpoints', self.endpoints)
        self.add_route('GET', '/', self.endpoints)
