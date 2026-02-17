import asyncio
from dataclasses import dataclass
from types import SimpleNamespace

from app.Command import Command
from app.state.ClientState import ClientState
from app.state.State import State


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
