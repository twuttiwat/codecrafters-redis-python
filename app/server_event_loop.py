import socket
import asyncio
from .command_handler import handle_command, State

async def handle_client(state):
    while True:
        request = await asyncio.get_event_loop().sock_recv(state.connection, 1024)
        if not request:
            break

        data = request.decode().strip()
        if not data:
            continue

        response = await handle_command(data, state)
        print(f"response: {response}")
        state.connection.send(response)

async def start():
    print("Redis EventLoop Start!")

    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    server_socket.setblocking(False)

    shared_store = {}
    shared_list_store = {}
    shared_sorted_sets = {}
    my_shared_channels = {}
    user_flags = {"nopass"}
    passwords = []
    default_user = "default"

    while True:
        my_connection, _ = await asyncio.get_event_loop().sock_accept(server_socket)  # wait for client
        loop = asyncio.get_event_loop()
        client_channels = {}
        my_current_user = default_user if not passwords else None
        state = State(store = shared_store, list_store = shared_list_store, shared_channels = my_shared_channels,
                      sorted_sets = shared_sorted_sets, default_passwords = passwords, default_user_flags = user_flags,
                      current_user = my_current_user, channels = client_channels, connection = my_connection,
                      is_multi = False, command_queue = [], schedule_remove = lambda k, t: loop.call_later(t, shared_store.pop, k))
        asyncio.create_task(handle_client(state))

