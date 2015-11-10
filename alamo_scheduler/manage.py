# -*- coding: utf-8 -*-
import argparse
import os
from configparser import ConfigParser

from alamo_scheduler.conf import initialize_settings
from alamo_scheduler.loggers import configure_logging
from alamo_scheduler.scheduler import AlamoScheduler


class AlamoManager(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser()

        self.setup()

    def setup(self):
        configure_logging()

        self.build_args()

        config_parser = self.parse_config()
        config_data = []
        for section in config_parser.sections():
            for attr, value in config_parser.items(section):
                config_data.append((section, attr, value))

        initialize_settings(config_data)

    def build_args(self):
        self.parser.add_argument(
            '--config', '-c',
            type=str,
            required=False,
            help=(
                'Provide config file for Alamo scheduler. '
                'If not provided default config file will be taken.'
            )
        )

    def parse_config(self):
        """Parse config file."""
        args = self.parser.parse_args()
        config_file = args.config or os.path.join(
            os.path.dirname(__file__), 'config.cfg'
        )

        config_parser = ConfigParser()
        config_parser.read(config_file)

        return config_parser

    def execute(self):
        AlamoScheduler().start()


def main():
    AlamoManager().execute()


if __name__ == '__main__':
    main()
