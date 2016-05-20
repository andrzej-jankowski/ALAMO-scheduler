# -*- coding: utf-8 -*-
from alamo_common.conf import AlamoSettings
from alamo_scheduler.conf import default_settings


settings = AlamoSettings()
settings.reconfigure(default_settings)
