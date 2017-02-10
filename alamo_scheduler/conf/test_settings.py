# -*- coding: utf-8 -*-

# default
PAGE_SIZE = 1000
TRIES = 10
DEFAULT_VERBOSE = True

# server
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 18080

# check
CHECK_API_URL = 'http://example.com/api/checks/'
CHECK_PUSH_URL = 'http://example.com/api/hooks/push_checks/'
CHECK_USER = ''
CHECK_PASSWORD = ''

# kafka
KAFKA_HOSTS = 'localhost'
KAFKA_GROUP = ''
KAFKA_TOPIC = ''
KAFKA_MESSAGES_COUNT = 40
KAFKA_INTERVAL = 10

# jobs
JOBS_MISFIRE_GRACE_TIME = 1
JOBS_MAX_INSTANCES = 4
JOBS_COALESCE = True

# zeromq
ZERO_MQ_HOST = 'tcp://128.0.0.1'
ZERO_MQ_PORT = 5559

# statsd
STATSD_HOST = 'localhost'
STATSD_PORT = 8126
STATSD_PREFIX = 'stats.alamo_scheduler.test'
STATSD_MAXUDPSIZE = 100

SCHEDULER_COUNT = 1
SCHEDULER_NR = 0
