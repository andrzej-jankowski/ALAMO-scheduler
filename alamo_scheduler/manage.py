# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import argparse
import os
from configparser import ConfigParser

from alamo_scheduler.scheduler import AlamoScheduler
from alamo_scheduler.queue import ZeroMQQueue

parser = argparse.ArgumentParser()

parser.add_argument(
    '--config', '-c',
    type=str,
    required=False,
    help=(
        'Provide config file for Alamo scheduler. '
        'If not provided default config file will be taken.'
    )
)


def main():
    args = parser.parse_args()

    config_file = args.config or os.path.join(
        os.path.dirname(__file__), 'config.cfg')

    config_parser = ConfigParser()
    config_parser.read(config_file)

    verbose = config_parser.getboolean('default', 'verbose')
    redis_host = config_parser.get('redis', 'host')
    redis_port = config_parser.getint('redis', 'port')
    redis_db = config_parser.getint('redis', 'db')
    cache_update_key = config_parser.get('cache', 'update_key')

    misfire_grace_time = config_parser.getint('jobs', 'misfire_grace_time')
    max_instances = config_parser.getint('jobs', 'max_instances')
    coalesce = config_parser.getboolean('jobs', 'coalesce')

    zero_mq_port = config_parser.get('zero_mq', 'host')
    zero_mq_host = config_parser.get('zero_mq', 'port')

    scheduler = AlamoScheduler(
        redis_host, redis_port, redis_db,
        cache_update_key,
        ZeroMQQueue(zero_mq_port, zero_mq_host),
        misfire_grace_time=misfire_grace_time,
        max_instances=max_instances,
        coalesce=coalesce,
        verbose=verbose)
    scheduler.run()


if __name__ == '__main__':
    main()
