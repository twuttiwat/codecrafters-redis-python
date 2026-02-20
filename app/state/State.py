from app.state.KeyValue import KeyValue
from app.state.List import List
from app.state.Stream import Stream


class State:
    def __init__(self):
        self.key_value_dict = KeyValue()
        self.list_dict = List()
        self.stream_dict = Stream()
        self.is_multi = False
        self.multi_queue = []
        self._states = [self.key_value_dict, self.list_dict, self.stream_dict]
        self._replica_writes = []

    def __getattr__(self, name):
        for state in self._states:
            if hasattr(state, name):
                return getattr(state, name)
        raise AttributeError(f"'State' object has no attribute '{name}'")

    def multi(self):
        self.is_multi = True

    async def exec(self):
        if not self.is_multi:
            raise ValueError("ERR EXEC without MULTI")

        results = []
        for func, args in self.multi_queue:
            result = await func(*args)
            results.extend(result)

        self.is_multi = False
        self.multi_queue = []

        return results

    def type(self, key):
        if self.key_value_dict.has_key(key):
            return "string"
        elif self.stream_dict.has_key(key):
            return "stream"
        else:
            return None

    def add_replica_write(self, write_func):
        self._replica_writes.append(write_func)

    def replicate(self, command_in_bytes):
        for write_func in self._replica_writes:
            write_func(command_in_bytes)
