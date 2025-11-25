import asyncio
import argparse

from .server_event_loop import start


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=6379)
    args = parser.parse_args()

    asyncio.run(start(args))
