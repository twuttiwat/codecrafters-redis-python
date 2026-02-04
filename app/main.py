import asyncio

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Connected by {addr}")

    while True:
        data = await reader.read(1024)
        if not data:
            break

        print(f"Received from {addr}: {data!r}")

        writer.write(b"+PONG\r\n")
        await writer.drain()

    print(f"Closing {addr}")
    writer.close()
    await writer.wait_closed()


async def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server = await asyncio.start_server(handle_client, "localhost", 6379)

    addr = server.sockets[0].getsockname()
    print(f"Serving on {addr}")

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
