import socket
import threading
import asyncio
from .command_handler import State, process_command

def handle_client_th(client_socket, state):
    while True:
        request = client_socket.recv(1024)
        if not request:
            break

        data = request.decode().strip()
        if not data:
            continue

        response = process_command(data, state)
        client_socket.send(response)

def main_th():
    print("Redis Multi-Thread Start!")

    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    while True:
        connection, _ = server_socket.accept()  # wait for client
        my_store = {}
        state = State(store = my_store, is_multi = False, schedule_remove = lambda k, t: threading.Timer(t, my_store.pop, args=[k]).start())
        threading.Thread(target=handle_client_th, args=(connection, state)).start()

async def handle_client_el(client_socket):
    loop = asyncio.get_event_loop()
    my_store = {}
    state = State(store = my_store, is_multi = False, command_queue = [], schedule_remove = lambda k, t: loop.call_later(t, my_store.pop, k))
    while True:
        request = await loop.sock_recv(client_socket, 1024)
        if not request:
            break

        data = request.decode().strip()
        if not data:
            continue

        response = process_command(data, state)
        client_socket.send(response)



async def main_el():
    print("Redis EventLoop Start!")

    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    server_socket.setblocking(False)
    loop = asyncio.get_event_loop()

    while True:
        connection, _ = await loop.sock_accept(server_socket)  # wait for client
        loop.create_task(handle_client_el(connection))


if __name__ == "__main__":
    # main_th()
    asyncio.run(main_el())
