# -*- coding: utf-8 -*-
from unittest import TestCase
from alamo_scheduler.conf import settings
from ddt import ddt, data, unpack


@ddt
class AlamoSettingsTestCase(TestCase):
    @unpack
    @data(
        ('SERVER_HOST', '0.0.0.0'),
        ('SERVER_PORT', 18080),
        ('SCHEDULER_HOSTS', ['scheduler1', 'scheduler2']),
        ('SCHEDULER_NAME', 'scheduler1'),
        ('CHECK_API_URL', 'http://example.com/api/checks/'),
        ('CHECK_PUSH_URL', 'http://example.com/api/hooks/push_checks/'),
        ('CHECK_PASSWORD', ''),
        ('JOBS_MISFIRE_GRACE_TIME', 1),
        ('JOBS_MAX_INSTANCES', 4),
        ('JOBS_COALESCE', True),
        ('ZERO_MQ_HOST', 'tcp://128.0.0.1'),
        ('ZERO_MQ_PORT', 5559),
        ('STATSD_HOST', 'localhost'),
        ('STATSD_PORT', 8126),
        ('STATSD_PREFIX', 'stats.alamo_scheduler.test'),
        ('STATSD_MAXUDPSIZE', 100),
    )
    def test_settings_for_tests(self, field, value):
        self.assertEqual(getattr(settings, field), value)
