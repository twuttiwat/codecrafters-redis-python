import socket
import threading
import asyncio
from dataclasses import dataclass

@dataclass
class State:
    store: dict
    is_multi: bool
    schedule_remove: object

def process_command(data, state):
    if data.startswith("*"):
        if state.is_multi:
            return b"+QUEUED\r\n"
        lines = data.split("\r\n")
        command = lines[2].upper()
        match command:
            case "PING":
                response = b"+PONG\r\n"
            case "ECHO":
                message = lines[4]
                response = f"${len(message)}\r\n{message}\r\n".encode()
            case "SET":
                key = lines[4]
                value = lines[6]
                if len(lines) > 8:
                    ttl_seconds = int(lines[10]) / 1000 if lines[8].lower() == "px" else int(lines[10])
                    state.schedule_remove(key, ttl_seconds)
                state.store[key] = value
                response = b"+OK\r\n"
            case "GET":
                key = lines[4]
                value = state.store.get(key, None)
                if value is not None:
                    response = f"${len(value)}\r\n{value}\r\n".encode()
                else:
                    response = b"$-1\r\n"
            case "INCR":
                key = lines[4]
                value = state.store.get(key, "0")
                if value.isdigit():
                    new_value = int(value) + 1
                    state.store[key] = str(new_value)
                    response = f":{new_value}\r\n".encode()
                else:
                    response = b"-ERR value is not an integer or out of range\r\n"
            case "MULTI":
                state.is_multi = True
                response = b"+OK\r\n"
            case _:
                response = b"-ERR unknown command\r\n"
        return response
    else:
        return b"-ERR invalid request\r\n"

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

async def handle_client_el(client_socket, state):
    loop = asyncio.get_event_loop()
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
    my_store = {}
    state = State(store = my_store, is_multi = False, schedule_remove = lambda k, t: loop.call_later(t, my_store.pop, k))

    while True:
        connection, _ = await loop.sock_accept(server_socket)  # wait for client
        loop.create_task(handle_client_el(connection, state))


if __name__ == "__main__":
    main_th()
    # asyncio.run(main_el())
