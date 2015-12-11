# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from unittest import TestCase
from argparse import ArgumentParser

from mock import MagicMock, patch

from alamo_scheduler.manage import AlamoManager


class TestAlamoWorker(TestCase):

    @patch('alamo_scheduler.manage.AlamoManager.__init__',
           MagicMock(return_value=None))
    def setUp(self):
        self.manager = AlamoManager()
        self.manager.parser = AlamoManager.build_args()

    def test_build_args(self):
        parser = self.manager.build_args()
        self.assertTrue(
            isinstance(parser, ArgumentParser))
