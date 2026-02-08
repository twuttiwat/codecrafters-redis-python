import asyncio

from app.Server import Server

async def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    await Server().start()

if __name__ == "__main__":
    asyncio.run(main())
