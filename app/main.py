import socket
import threading

def handle_client(client_socket):
    try:
        while True:
            # Receive data from client
            data = client_socket.recv(1024)
            print(f"Message received: {data}")
            if not data:
                break

            # Send response to client
            client_socket.sendall(b"+PONG\r\n")

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
