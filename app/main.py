import asyncio
import sys

from app.Server import Server


async def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    port = 6379
    try:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    except ValueError:
        pass

    await Server().start(port)


if __name__ == "__main__":
    asyncio.run(main())
