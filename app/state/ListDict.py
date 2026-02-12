from dataclasses import dataclass


@dataclass
class ListDict:
    dict = {}

    def push(self, key, value):
        self.dict[key] = self.dict.get(key, []) + [value]
        return len(self.dict[key])

    def push_many(self, key, values):
        self.dict[key] = self.dict.get(key, []) + values
        return len(self.dict[key])

    def range(self, key, start, stop):
        values = self.dict.get(key, [])
        if start >= len(values):
            return []
        if stop >= len(values):
            stop = len(values) - 1

        return values[start : stop + 1]
