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
        return self.list_dict.rpush(key, value)

    def rpush_many(self, key, values):
        return self.list_dict.rpush_many(key, values)

    def lrange(self, key, start, stop):
        values = self.list_dict.range(key, start, stop)
        return values

    def lpush(self, key, value):
        return self.list_dict.lpush(key, value)

    def lpush_many(self, key, values):
        return self.list_dict.lpush_many(key, values)

    def llen(self, key):
        length = self.list_dict.llen(key)
        return length

    def lpop(self, key):
        value = self.list_dict.lpop(key)
        return value

    def lpop_many(self, key, pop_count):
        values = self.list_dict.lpop_many(key, pop_count)
        return values

    async def blpop(self, key, timeout):
        value = await self.list_dict.blpop(key, timeout)
        return value

    def type(self, key):
        return self.key_value_dict.type(key)
