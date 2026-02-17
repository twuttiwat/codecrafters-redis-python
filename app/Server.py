import asyncio
from dataclasses import dataclass
from types import SimpleNamespace

import app.resp as resp
from app.Command import Command
from app.state.State import State


class ClientState:
    def __init__(self):
        self.is_multi = False
        self.multi_queue = []

    def multi(self):
        self.is_multi = True
        return resp.OK

    async def exec(self):
        if not self.is_multi:
            raise ValueError("ERR EXEC without MULTI")

        results = []
        for func, args in self.multi_queue:
            results.append(await func(*args))
        self.is_multi = False
        self.multi_queue = []

        return results


class Server:
    def __init__(self):
        self.state = State()
        self.server = None

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info("peername")
        print(f"Connected by {addr}")

        client_state = ClientState()

        while True:
            bytes_data = await reader.read(1024)
            if not bytes_data:
                break

            print(f"Received from {addr}: {bytes_data!r}")

            command = Command.parse(bytes_data)
            ctx = SimpleNamespace(state=self.state, client_state=client_state)
            response = await command.dispatch(ctx)

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
