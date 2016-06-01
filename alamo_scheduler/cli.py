# -*- coding: utf-8 -*-
import os


def main():
    os.environ.setdefault(
        "ALAMO_SETTINGS_MODULE", "alamo_scheduler.conf.default_settings"
    )

    from alamo_scheduler.manage import execute

    execute()


if __name__ == '__main__':
    main()
