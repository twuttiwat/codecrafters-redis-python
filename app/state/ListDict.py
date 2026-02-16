import asyncio
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

    def lrange(self, key, start, stop):
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

    def llen(self, key):
        length = self.dict.get(key, [])
        return len(length)

    def lpop(self, key):
        values = self.dict.get(key, [])
        if not values:
            return None

        return values.pop(0)

    def lpop_many(self, key, pop_count):
        values = self.dict.get(key, [])
        if not values:
            return None

        if pop_count > len(values):
            pop_count = len(values)

        popped_values = []
        for _ in range(pop_count):
            popped_values.append(values.pop(0))

        return popped_values

    async def blpop(self, key, timeout):
        async def wait_for_data():
            start = asyncio.get_event_loop().time()
            while not self.dict.get(key):
                if timeout > 0 and asyncio.get_event_loop().time() - start >= timeout:
                    raise asyncio.TimeoutError("List is still empty after timeout")
                await asyncio.sleep(0.1)

        try:
            await wait_for_data()
        except TimeoutError:
            return None

        values = self.dict[key]
        return values.pop(0)
