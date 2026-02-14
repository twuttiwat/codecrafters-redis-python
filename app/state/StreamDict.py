from dataclasses import dataclass


@dataclass
class StreamDict:
    dict = {}

    def xadd(self, stream_key, entry_id, *fields):
        stream = self.dict.setdefault(stream_key, [])
        key_value_pairs = list(zip(fields[::2], fields[1::2]))
        stream.append((entry_id, key_value_pairs))
        return entry_id

    def has_key(self, key):
        return key in self.dict
