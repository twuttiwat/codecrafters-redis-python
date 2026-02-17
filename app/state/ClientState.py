import app.resp as resp


class ClientState:
    def __init__(self):
        self.is_multi = False
        self.multi_queue = []

    def queue_command(self, func, args):
        self.multi_queue.append((func, args))
        return resp.encode_simple_str("QUEUED")

    def multi(self):
        self.is_multi = True

    async def exec(self):
        if not self.is_multi:
            raise ValueError("ERR EXEC without MULTI")

        results = []
        for func, args in self.multi_queue:
            results.append(await func(*args))
        self.is_multi = False
        self.multi_queue = []

        return results
