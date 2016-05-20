# -*- coding: utf-8 -*-
import os

get_env = os.getenv

# default

DEFAULT__VERBOSE = get_env('ALAMO_DEFAULT_VERBOSE', True)

# check
CHECK__API_URL = get_env('ALAMO_CHECK_API_URL')
CHECK__USER = get_env('ALAMO_CHECK_USER')
CHECK__PASSWORD = get_env('ALAMO_CHECK_PASSWORD')

# kafka
KAFKA__HOSTS = get_env('ALAMO_KAFKA_HOSTS')
KAFKA__GROUP = get_env('ALAMO_KAFKA_GROUP')
KAFKA__TOPIC = get_env('ALAMO_KAFKA_TOPIC')
KAFKA__MESSAGES_COUNT = int(get_env('ALAMO_KAFKA_MESSAGES_COUNT', 40))
KAFKA__INTERVAL = int(get_env('ALAMO_KAFKA_INTERVAL', 10))

# jobs
JOBS__MISFIRE_GRACE_TIME = int(get_env('ALAMO_JOBS_MISFIRE_GRACE_TIME', 1))
JOBS__MAX_INSTANCES = int(get_env('ALAMO_JOBS_MAX_INSTANCES', 4))
JOBS__COALESCE = get_env('ALAMO_JOBS_COALESCE', True)

# zeromq
ZERO_MQ__HOST = get_env('ALAMO_ZERO_MQ_HOST', 'tcp://127.0.0.1')
ZERO_MQ__PORT = int(get_env('ALAMO_ZERO_MQ_PORT', 5557))

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
