# -*- coding: utf-8 -*-


# server
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 18080

SCHEDULER_HOSTS = ['scheduler1', 'scheduler2']
SCHEDULER_NAME = 'scheduler1'

# check
CHECK_API_URL = 'http://example.com/api/checks/'
CHECK_PUSH_URL = 'http://example.com/api/hooks/push_checks/'
CHECK_USER = ''
CHECK_PASSWORD = ''

# jobs
JOBS_MISFIRE_GRACE_TIME = 1
JOBS_MAX_INSTANCES = 4
JOBS_COALESCE = True

# zeromq
ZERO_MQ_HOST = 'tcp://128.0.0.1'
ZERO_MQ_PORT = 5559
ENVIRONMENTS = ['prod']

# statsd
STATSD_HOST = 'localhost'
STATSD_PORT = 8126
STATSD_PREFIX = 'stats.alamo_scheduler.test'
STATSD_MAXUDPSIZE = 100

SCHEDULER_COUNT = 1
SCHEDULER_NR = 0
