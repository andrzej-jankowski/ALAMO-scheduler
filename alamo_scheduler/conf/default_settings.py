# -*- coding: utf-8 -*-
import os

get_env = os.getenv

# default
PAGE_SIZE = int(get_env('ALAMO_PAGE_SIZE', 1000))
TRIES = int(get_env('ALAMO_TRIES', 10))
DEFAULT_VERBOSE = get_env('ALAMO_DEFAULT_VERBOSE', True)
SCHEDULER_COUNT = int(get_env('ALAMO_SCHEDULER_COUNT', 1))
SCHEDULER_NR = int(get_env('ALAMO_SCHEDULER_NR', 0))
# server
SERVER_HOST = get_env('ALAMO_SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(get_env('ALAMO_SERVER_PORT', 18080))

# check
CHECK_API_URL = get_env(
    'ALAMO_CHECK_API_URL', 'http://example.com/api/checks/'
)
CHECK_USER = get_env('ALAMO_CHECK_USER', '')
CHECK_PASSWORD = get_env('ALAMO_CHECK_PASSWORD', '')

# kafka
KAFKA_HOSTS = get_env('ALAMO_KAFKA_HOSTS', 'localhost')
KAFKA_GROUP = get_env('ALAMO_KAFKA_GROUP', '')
KAFKA_TOPIC = get_env('ALAMO_KAFKA_TOPIC', '')
KAFKA_MESSAGES_COUNT = int(get_env('ALAMO_KAFKA_MESSAGES_COUNT', 40))
KAFKA_INTERVAL = int(get_env('ALAMO_KAFKA_INTERVAL', 10))

# jobs
JOBS_MISFIRE_GRACE_TIME = int(get_env('ALAMO_JOBS_MISFIRE_GRACE_TIME', 1))
JOBS_MAX_INSTANCES = int(get_env('ALAMO_JOBS_MAX_INSTANCES', 4))
JOBS_COALESCE = get_env('ALAMO_JOBS_COALESCE', True)

# zeromq
ZERO_MQ_HOST = get_env('ALAMO_ZERO_MQ_HOST', 'tcp://127.0.0.1')
ZERO_MQ_PORT = int(get_env('ALAMO_ZERO_MQ_PORT', 5557))

# statsd
STATSD_HOST = get_env('ALAMO_STATSD_HOST', 'localhost')
STATSD_PORT = int(get_env('ALAMO_STATSD_PORT', 8125))
STATSD_PREFIX = get_env('ALAMO_STATSD_PREFIX', 'stats')
STATSD_MAXUDPSIZE = int(get_env('ALAMO_STATSD_MAXUDPSIZE', 512))

datefmt = '%Y-%m-%d %H:%M:%S'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'vverbose': {
            'datefmt': datefmt,
            'format': (
                '%(asctime)s - %(levelname)-7s - %(process)-6d - '
                '%(pathname)s line:%(lineno)-4d - "%(message)s"'
            )
        },
        'verbose': {
            'datefmt': datefmt,
            'format': (
                '%(asctime)s - %(levelname)-7s - %(process)-6d - '
                '%(module)-10s line:%(lineno)-4d - %(message)s'
            )
        },
        'simple': {
            'datefmt': datefmt,
            'format': '%(asctime)s - %(levelname)-7s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'aiohttp': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
        'alamo_scheduler': {
            'handlers': ['console'],
            'level': 'DEBUG'
        }
    }
}
