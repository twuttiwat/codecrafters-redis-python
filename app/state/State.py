from app.state.KeyValueDict import KeyValueDict
from app.state.ListDict import ListDict


class State:
    def __init__(self):
        self.key_value_dict = KeyValueDict()
        self.list_dict = ListDict()

    def set(self, key, value, expired_in_ms=None):
        self.key_value_dict.set(key, value, expired_in_ms)

    def get(self, key):
        return self.key_value_dict.get(key)

    def rpush(self, key, value):
        return self.list_dict.push(key, value)
