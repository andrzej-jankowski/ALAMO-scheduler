# -*- coding: utf-8 -*-
from unittest import TestCase
from alamo_scheduler.conf import settings
from ddt import ddt, data, unpack


@ddt
class AlamoSettingsTestCase(TestCase):
    @unpack
    @data(
        ('PAGE_SIZE', 1000),
        ('SERVER_HOST', '0.0.0.0'),
        ('SERVER_PORT', 18080),
        ('CHECK_API_URL', 'http://example.com/api/checks/'),
        ('CHECK_PUSH_URL', 'http://example.com/api/hooks/push_checks/'),
        ('CHECK_PASSWORD', ''),
        ('KAFKA_HOSTS', 'localhost'),
        ('KAFKA_GROUP', ''),
        ('KAFKA_TOPIC', ''),
        ('KAFKA_MESSAGES_COUNT', 40),
        ('KAFKA_INTERVAL', 10),
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
