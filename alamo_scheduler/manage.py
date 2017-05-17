# -*- coding: utf-8 -*-

import asyncio

from alamo_scheduler.aioweb import SchedulerServerApplication
from alamo_scheduler.scheduler import AlamoScheduler


class AlamoManager(object):

    def __init__(self):

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.server = SchedulerServerApplication()
        self.scheduler = AlamoScheduler(loop=self.loop)
        self.server.add_get('/checks', self.scheduler.checks)
        self.server.add_get('/checks/{uuid}', self.scheduler.checks)
        self.server.add_post('/checks', self.scheduler.update)

    def execute(self):
        self.server.init(loop=self.loop)
        self.scheduler.start()
        self.server.finish_connections()
        self.loop.close()


def execute():
    AlamoManager().execute()
