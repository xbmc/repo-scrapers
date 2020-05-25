#!/usr/bin/env python
# -*- coding: UTF-8 -*-


class PathSpecificSettings(object):
    # read-only shim for typed `xbmcaddon.Addon().getSetting*` methods
    def __init__(self, settings_dict, log_fn):
        self.data = settings_dict
        self.log = log_fn

    def getSettingBool(self, id):
        return self._inner_get_setting(id, bool, False)

    def getSettingInt(self, id):
        return self._inner_get_setting(id, int, 0)

    def getSettingNumber(self, id):
        return self._inner_get_setting(id, float, 0.0)

    def getSettingString(self, id):
        return self._inner_get_setting(id, str, '')

    def _inner_get_setting(self, setting_id, setting_type, default):
        value = self.data.get(setting_id)
        if isinstance(value, setting_type):
            return value
        self._log_bad_value(value, setting_id)
        return default

    def _log_bad_value(self, value, setting_id):
        if value is None:
            self.log(
                f"requested setting ({setting_id}) was not found.")
        else:
            self.log(
                f'failed to load value "{value}" for setting {setting_id}')
