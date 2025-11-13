import socket
import threading
from collections import namedtuple

set_dict = {}

def handle_client_1(client_socket):
    try:
        while True:
            # Receive data from client
            data = client_socket.recv(1024)
            print(f"Message received: {data}")
            if not data:
                break

            # Parse commands
            commands = data.split(b"\r\n")
            num_commands = int(commands[0][1::])
            if num_commands < 1:
                break

            match commands[2].lower().decode():
                case "ping":
                    client_socket.sendall(b"+PONG\r\n")
                case "echo":
                    resp = commands[3] + b"\r\n" + commands[4] + b"\r\n"
                    client_socket.sendall(resp)
                case "set":
                    set_name = commands[4]
                    set_value = commands[6]
                    set_dict[set_name] = set_value
                    client_socket.sendall(b"+OK\r\n")
                case "get":
                    get_name = commands[4]
                    if get_name in set_dict:
                        get_value = set_dict[get_name]
                        print(f"get_value: {get_value}")
                        resp =  b"$" + bytes(str(len(get_value)), 'utf-8') + b"\r\n" + get_value + b"\r\n"
                        client_socket.sendall(resp)
                    else:
                        client_socket.sendall(b"$-1\r\n")

                case _:
                    break

    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        client_socket.close()


Command = namedtuple("Command", ["name", "params"])

def parse_command(data):
    parts = data.split(b"\r\n")
    num_parts = int(parts[0][1::])

    name = parts[2]
    params = []
    index = 4
    while index < len(parts):
        params.append(parts[index])
        index += 2

    return Command(name, params)

def handle_client(client_socket):
    try:
        while True:
            # Receive data from client
            data = client_socket.recv(1024)
            print(f"Message received: {data}")
            if not data:
                break

            # Parse command
            command = parse_command(data)

            # Evaluate command
            match command.name.lower().decode():
                case "ping":
                    client_socket.sendall(b"+PONG\r\n")
                case "echo":
                    echo_value = command.params[0]
                    resp = b"$" + bytes(str(len(echo_value)), 'utf-8') + b"\r\n" + echo_value + b"\r\n"
                    client_socket.sendall(resp)
                case "set":
                    set_name = command.params[0]
                    set_value = command.params[1]
                    set_dict[set_name] = set_value
                    client_socket.sendall(b"+OK\r\n")
                case "get":
                    get_name = command.params[0]
                    if get_name in set_dict:
                        get_value = set_dict[get_name]
                        print(f"get_value: {get_value}")
                        resp =  b"$" + bytes(str(len(get_value)), 'utf-8') + b"\r\n" + get_value + b"\r\n"
                        client_socket.sendall(resp)
                    else:
                        client_socket.sendall(b"$-1\r\n")

                case _:
                    break

    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        client_socket.close()

def main():
    # Listen to client
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)

   
    while True:
        # Accept connection
        client_socket, _ = server_socket.accept()  # wait for client
        print(f"Connection established")

        # Handle client using new thread
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    main()
