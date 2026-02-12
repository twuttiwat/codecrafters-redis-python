from dataclasses import dataclass


@dataclass
class ListDict:
    dict = {}

    def rpush(self, key, value):
        self.dict[key] = self.dict.get(key, []) + [value]
        return len(self.dict[key])

    def rpush_many(self, key, values):
        self.dict[key] = self.dict.get(key, []) + values
        return len(self.dict[key])

    def range(self, key, start, stop):
        values = self.dict.get(key, [])

        if start < 0:
            start = max(0, len(values) + start)
        if stop < 0:
            stop = max(0, len(values) + stop)

        if start >= len(values):
            return []
        if stop >= len(values):
            stop = len(values) - 1

        return values[start : stop + 1]

    def lpush(self, key, value):
        self.dict[key] = [value] + self.dict.get(key, [])
        return len(self.dict[key])

    def lpush_many(self, key, values):
        rev_values = values[:]
        rev_values.reverse()
        self.dict[key] = rev_values + self.dict.get(key, [])
        return len(self.dict[key])
