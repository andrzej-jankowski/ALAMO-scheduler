# -*- coding: utf-8 -*-
from unittest import TestCase

import responses
from alamo_scheduler.conf import settings
from alamo_scheduler.hooks.push_checks import PushChecks


class TestPushChecks(TestCase):

    @responses.activate
    def test_trigger_feeder(self):
        responses.add(responses.GET, settings.CHECK_PUSH_URL,
            body='{"status": "ok", "scheduled": 3}', status=200,
            content_type="application/json")
        push = PushChecks()
        self.assertEqual(True, push.trigger())

    @responses.activate
    def test_trigger_feeder_connection(self):
        responses.add(responses.GET, settings.CHECK_PUSH_URL,
            body=ConnectionError('error'))
        push = PushChecks()
        with self.assertRaises(ConnectionError):
            trigger = push.trigger()
            self.assertFalse(trigger)
