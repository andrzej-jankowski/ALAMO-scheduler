# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import zmq
from threading import RLock

from alamo_scheduler.conf import settings


class ZeroMQQueue(object):
    """Zero MQ message queue client."""
    host = None
    port = None
    context = None
    zmq_socket = None

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.lock = RLock()
        self.context = zmq.Context()
        self.connect()

    def connect(self):
        self.zmq_socket = self.context.socket(zmq.PUSH)
        self.zmq_socket.bind("{}:{}".format(self.host, self.port))

    def send(self, payload):
        with self.lock:
            self.zmq_socket.send_json(payload)


class ZeroMQ(object):
    def __new__(cls):
        for p, env in enumerate(settings.ENVIRONMENTS,
                                start=settings.ZERO_MQ_PORT):
            setattr(cls, env, ZeroMQQueue(settings.ZERO_MQ_HOST, p))
        return super(ZeroMQ, cls).__new__(cls)
