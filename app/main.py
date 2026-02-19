import asyncio
import sys
from doctest import master

from app.Server import Server


async def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    role, port = "master", 6379
    master_host, master_port = None, None
    if "--replicaof" in sys.argv:
        role = "slave"
        master_host, master_port = sys.argv[sys.argv.index("--replicaof") + 1].split()
        print(f"Replicating from {master_host}:{master_port}")
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])

    await Server(role, port, master_host, master_port).start()


if __name__ == "__main__":
    asyncio.run(main())
