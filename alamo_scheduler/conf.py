# -*- coding: utf-8 -*-


class AlamoSettings(object):
    """Alamo settings."""

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_inst'):
            cls._inst = super(AlamoSettings, cls).__new__(cls, *args, **kwargs)
        return cls._inst

    def __getattr__(self, name):
        return None


settings = AlamoSettings()


def initialize_settings(config_data: list):
    """Initialize settings object and fill with data.

    :param config_data: list of tuples in format
            tuple(section, attr, attr_value)
    """
    bool_map = {'true': True, 'false': False}
    for section, attr, value in config_data:
        _float = None
        try:
            value = bool_map[value.lower()]
        except KeyError:
            try:
                _float = float(value)
                _int = int(value)
                value = _int if _float == _int else _float
            except ValueError:
                value = value if _float is None else _float

        attr = '{}__{}'.format(section, attr).upper()
        setattr(settings, attr, value)
