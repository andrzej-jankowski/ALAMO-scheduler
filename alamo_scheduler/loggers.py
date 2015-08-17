# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

LOG_LEVEL = "DEBUG"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

console_handler = logging.StreamHandler()
log_level = getattr(logging, LOG_LEVEL, 10)
console_handler.setLevel(log_level)
formatter = logging.Formatter(LOG_FORMAT)
console_handler.setFormatter(formatter)
logger = logging.getLogger('alamo.scheduler')
logger.setLevel(log_level)
logger.addHandler(console_handler)
