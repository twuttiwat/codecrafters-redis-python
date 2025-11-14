import socket
import threading
import asyncio

store_th = {}

def handle_client_th(client_socket):
    while True:
        request = client_socket.recv(1024)
        if not request:
            break

        data = request.decode().strip()
        if not data:
            continue

        if data.startswith("*"):
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
                        ttl = int(lines[10]) / 1000 if lines[8].lower() == "px" else int(lines[10])
                        threading.Timer(ttl, store_th.pop, args=[key]).start()
                    store_th[key] = value
                    response = b"+OK\r\n"
                case "GET":
                    key = lines[4]
                    value = store_th.get(key, None)
                    if value is not None:
                        response =  f"${len(value)}\r\n{value}\r\n".encode()
                    else:
                        response = b"$-1\r\n"
                case _:
                    response = b"-ERR unknow command\r\n"
            client_socket.send(response)
        else:
            client_socket.send(b"-ERR invalid request\r\n")

def main_th():
    print("Redis Multi-Thread Start!")

    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    while True:
        connection, _ = server_socket.accept()  # wait for client
        threading.Thread(target=handle_client_th, args=(connection,)).start()

async def handle_client_el(client_socket, store_el):
    loop = asyncio.get_event_loop()
    while True:
        request = await loop.sock_recv(client_socket, 1024)
        print(f"request: {request}")
        if not request:
            break

        data = request.decode().strip()
        if not data:
            continue

        if data.startswith("*"):
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
                        ttl = int(lines[10]) / 1000 if lines[8].lower() == "px" else int(lines[10])
                        loop.call_later(ttl, store_el.pop, key)
                    store_el[key] = value
                    response = b"+OK\r\n"
                case "GET":
                    key = lines[4]
                    value = store_el.get(key, None)
                    if value is not None:
                        response =  f"${len(value)}\r\n{value}\r\n".encode()
                    else:
                        response = b"$-1\r\n"
                case _:
                    response = b"-ERR unknow command\r\n"
            client_socket.send(response)
        else:
            client_socket.send(b"-ERR invalid request\r\n")



async def main_el():
    print("Redis EventLoop Start!")

    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    server_socket.setblocking(False)
    loop = asyncio.get_event_loop()
    store_el = {}

    while True:
        connection, _ = await loop.sock_accept(server_socket)  # wait for client
        loop.create_task(handle_client_el(connection, store_el))


if __name__ == "__main__":
    asyncio.run(main_el())
