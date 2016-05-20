# -*- coding: utf-8 -*-
import asyncio

import pip
import json
from aiohttp.web import Application, Response


def json_response(func):
    def wrapped(*args, **kwargs):
        response = Response()
        result = func(*args, **kwargs)
        response.body = json.dumps(result).encode('utf8')
        return response

    return wrapped


class SchedulerServerApplication(object):
    scheduler = _app = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(
                SchedulerServerApplication, cls
            ).__new__(cls, *args)
        return cls._inst

    @asyncio.coroutine
    def init(self, loop=None):
        loop = loop or asyncio.get_event_loop()
        self.configure_contract()
        handler = self._app.make_handler()
        srv = yield from loop.create_server(handler, '0.0.0.0', 8080)
        print("Server started at http://0.0.0.0:8080")
        return srv, handler

    @property
    def app(self):
        if self._app is None:
            self.setup()
        return self._app

    def ping(self, request):
        return Response(body=b'pong')

    @json_response
    def dependencies(self, request):
        installed_packages = pip.get_installed_distributions(local_only=True)
        deps = [dict(name=i.key, version=i.version)
                for i in installed_packages]
        return dict(endpoints=deps)

    @json_response
    def info(self, request):
        package = 'alamo-scheduler'
        version = next(iter([p.version for p in
                             pip.get_installed_distributions(local_only=True)
                             if p.key == package]), '<unknown>')

        return dict(title=package, version=version)

    @json_response
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
        return dict(endpoints=endpoints)

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
