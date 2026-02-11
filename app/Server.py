import asyncio
import time

from dataclasses import dataclass
from types import SimpleNamespace

from app.Command import Command

@dataclass
class KeyValueDict:
    dict = {}

    def set(self, key, value, expired_in_ms=None):
        set_at = time.perf_counter()
        self.dict[key] = (value, set_at, expired_in_ms)

    def get(self, key):
        dict_value = self.dict.get(key, None)
        if dict_value is None:
            return None

        if self.is_expired(key):
            return None

        value, _, _ = dict_value
        return value

    def is_expired(self, key):
        dict_value = self.dict.get(key, None)
        value, set_at, expired_in_ms = dict_value
        if expired_in_ms is None:
            return False

        get_at = time.perf_counter()
        elapsed_ms = (get_at - set_at) * 1000
        return elapsed_ms > expired_in_ms

class State:
    def __init__(self):
        self.key_value_dict = KeyValueDict()

    def set(self, key, value, expired_in_ms=None):
        self.key_value_dict.set(key, value, expired_in_ms)

    def get(self, key):
        return self.key_value_dict.get(key)

class Server:
    def __init__(self):
        self.state = State()

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Connected by {addr}")

        while True:
            bytes_data = await reader.read(1024)
            if not bytes_data:
                break

            print(f"Received from {addr}: {bytes_data!r}")

            command = Command.parse(bytes_data)
            ctx = SimpleNamespace(state=self.state)
            response = command.dispatch(ctx)

            writer.write(response)
            await writer.drain()

        print(f"Closing {addr}")
        writer.close()
        await writer.wait_closed()


    async def start(self):
        self.server = await asyncio.start_server(self.handle_client, "localhost", 6379)

        addr = self.server.sockets[0].getsockname()
        print(f"Serving on {addr}")

        async with self.server:
            await self.server.serve_forever()



