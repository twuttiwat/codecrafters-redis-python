from dataclasses import dataclass


@dataclass
class ListDict:
    dict = {}

    def push(self, key, value):
        self.dict[key] = self.dict.get(key, []) + [value]
        return len(self.dict[key])
