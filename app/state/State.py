from app.state.KeyValueDict import KeyValue
from app.state.ListDict import List
from app.state.StreamDict import Stream


class State:
    def __init__(self):
        self.key_value_dict = KeyValue()
        self.list_dict = List()
        self.stream_dict = Stream()
        self._states = [self.key_value_dict, self.list_dict, self.stream_dict]

    def __getattr__(self, name):
        for state in self._states:
            if hasattr(state, name):
                return getattr(state, name)
        raise AttributeError(f"'State' object has no attribute '{name}'")

    def type(self, key):
        if self.key_value_dict.has_key(key):
            return "string"
        elif self.stream_dict.has_key(key):
            return "stream"
        else:
            return None
