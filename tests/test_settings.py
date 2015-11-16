# -*- coding: utf-8 -*-
from unittest import TestCase

from alamo_scheduler.conf import initialize_settings, settings


class AlamoSettingsTestCase(TestCase):
    def setUp(self):
        data = [
            ('test', 'string', 'tested string'),
            ('test', 'bool', 'True'),
            ('test', 'number', '1234'),
            ('test', 'float', '99.3')
        ]
        initialize_settings(data)

    def test_initialized_object(self):
        self.assertEqual(settings.TEST__STRING, 'tested string')
        self.assertEqual(settings.TEST__NUMBER, 1234)
        self.assertEqual(settings.TEST__FLOAT, 99.3)
        self.assertTrue(settings.TEST__BOOL)

    def test_non_existing_attr_return_None(self):
        self.assertEqual(settings.TEST_NON_EXISTS, None)
