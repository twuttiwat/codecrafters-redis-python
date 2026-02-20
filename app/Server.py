import asyncio
from dataclasses import dataclass
from types import SimpleNamespace

import app.resp as resp
from app.Command import Command
from app.state.ClientState import ClientState
from app.state.State import State


class Server:
    def __init__(self, role="master", port=6379, master_host=None, master_port=None):
        self.state = State()
        self.role = role
        self.port = port
        self.master_host = master_host
        self.master_port = master_port
        self.server = None

    async def handle_client(self, reader, writer):
        async def write_response(response):
            writer.write(response)
            await writer.drain()

        addr = writer.get_extra_info("peername")
        print(f"Connected by {addr}")

        client_state = ClientState()

        while True:
            bytes_data = await reader.read(1024)
            if not bytes_data:
                break

            print(f"Received from {addr}: {bytes_data!r}")

            command = Command.parse(bytes_data)
            ctx = SimpleNamespace(
                role=self.role,
                state=self.state,
                client_state=client_state,
                write=write_response,
            )
            response = await command.dispatch(ctx)

            writer.write(response)
            await writer.drain()

        print(f"Closing {addr}")
        writer.close()
        await writer.wait_closed()

    async def handshake(self):
        reader, writer = await asyncio.open_connection(
            self.master_host, self.master_port
        )

        async def send_command(*args):
            command = resp.encode_command(*args)
            writer.write(command)
            await writer.drain()
            response = await reader.read(1024)
            print(f"Received response from master: {response!r}")

        await send_command("PING")
        await send_command(f"REPLCONF listening-port {self.port}")
        await send_command("REPLCONF capa psync2")
        await send_command("PSYNC ? -1")

    async def start(self):

        if self.role == "slave":
            await self.handshake()

        self.server = await asyncio.start_server(
            self.handle_client, "localhost", self.port
        )

        addr = self.server.sockets[0].getsockname()
        print(f"Serving on {addr}")

        async with self.server:
            await self.server.serve_forever()
