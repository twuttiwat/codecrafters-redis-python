import asyncio

from app.Command import Command

class Server:
    def __init__(self):
        self.key_value_dict = {}
        self.server = None

    def set(self, key, value):
        self.key_value_dict[key] = value

    def get(self, key):
        return self.key_value_dict.get(key, None)

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Connected by {addr}")

        while True:
            bytes_data = await reader.read(1024)
            if not bytes_data:
                break

            print(f"Received from {addr}: {bytes_data!r}")

            command = Command.parse(bytes_data)
            response = command.get_response(self)

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



