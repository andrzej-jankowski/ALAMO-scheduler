# -*- coding: utf-8 -*-

from logging.config import dictConfig

LOGGING = \
    {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
            },
            'vverbose': {
                'format': '%(asctime)s %(levelname)s %(pathname)s line:%(lineno)d: "%(message)s"'
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
            }
        },
        'loggers': {
            'alamo_scheduler': {
                'handlers': ['console'],
                'level': 'DEBUG'
            },
        }
    }


def configure_logging():
    dictConfig(LOGGING)
