import time
from dataclasses import dataclass


@dataclass
class KeyValueDict:
    dict = {}

    def set(self, key, value, expired_in_ms=None):
        set_at = time.perf_counter()
        self.dict[key] = (value, set_at, expired_in_ms)

    def get(self, key):
        dict_value = self.dict.get(key, None)
        if dict_value is None:
            return None

        if self.is_expired(key):
            return None

        value, _, _ = dict_value
        return value

    def is_expired(self, key):
        dict_value = self.dict.get(key, None)
        if dict_value is None:
            return False

        value, set_at, expired_in_ms = dict_value
        if expired_in_ms is None:
            return False

        get_at = time.perf_counter()
        elapsed_ms = (get_at - set_at) * 1000
        return elapsed_ms > expired_in_ms

    def type(self, key):
        if key in self.dict:
            return "string"
        else:
            return None
