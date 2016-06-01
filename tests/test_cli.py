# -*- coding: utf-8 -*-
from unittest import TestCase
from unittest.mock import patch

from alamo_scheduler.cli import main
import os


class TestAlamoWorker(TestCase):

    @patch('alamo_scheduler.manage.execute')
    def test_execute_method(self, execute_mock):
        main()
        self.assertEqual(
            os.environ.get('ALAMO_SETTINGS_MODULE'),
            'alamo_scheduler.conf.test_settings'
        )
        self.assertTrue(execute_mock.called)
