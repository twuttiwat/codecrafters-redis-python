import asyncio
import sys

from app.Server import Server


async def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    role, port = "master", 6379
    if "--replicaof" in sys.argv:
        role = "slave"
    if "--port" in sys.argv:
        port = sys.argv[sys.argv.index("--port") + 1]

    await Server(role, port).start()


if __name__ == "__main__":
    asyncio.run(main())
