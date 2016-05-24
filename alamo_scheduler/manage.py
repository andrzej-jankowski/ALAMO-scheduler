# -*- coding: utf-8 -*-

from alamo_scheduler.scheduler import AlamoScheduler
from alamo_scheduler.aioweb import server


class AlamoManager(object):
    def __init__(self):
        self.scheduler = AlamoScheduler()
        server.add_route('GET', '/checks', self.scheduler.checks)
        server.add_route('GET', '/checks/{uuid}', self.scheduler.checks)

    def execute(self):
        self.scheduler.start()


def execute():
    AlamoManager().execute()
