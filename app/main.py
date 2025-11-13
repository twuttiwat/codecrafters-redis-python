import socket


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Listen to client
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)

    # Accept connection
    client_socket, client_address = server_socket.accept()  # wait for client
    print(f"Connection established with {client_address}")
    
    while True:

        # Receive data from client
        data = client_socket.recv(1024)
        print(f"Message received: {data}")

        # Send response to client
        client_socket.sendall(b"+PONG\r\n")


if __name__ == "__main__":
    main()
