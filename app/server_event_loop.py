import socket
import asyncio
from app.command_handler import handle_command, State
from app.resp import resp_array_from_strings

async def handle_client(state):
    while True:
        request = await asyncio.get_event_loop().sock_recv(state.connection, 1024)
        if not request:
            break

        data = request.decode().strip()
        if not data:
            continue

        response = await handle_command(data, state, request)
        print(f"response: {response}")
        state.connection.send(response)


async def handshake_master(master_host, master_port, listening_port):
    master_reader, master_writer = await asyncio.open_connection(master_host, master_port)

    async def send_recv_cmd(cmd):
        cmd_arr = cmd.split(" ")
        master_writer.write(resp_array_from_strings(cmd_arr))
        await master_writer.drain()
        data = await master_reader.read(100)
        #print(f"Received {data.decode()}")
        return data

    await send_recv_cmd("PING")
    await send_recv_cmd(f"REPLCONF listening-port {listening_port}")
    await send_recv_cmd("REPLCONF capa psync2")
    await send_recv_cmd("PSYNC ? -1")

    return master_reader


async def start(args):
    print(f"Redis EventLoop Start! on port {args.port}")

    server_socket = socket.create_server(("localhost", int(args.port)), reuse_port=True)
    server_socket.setblocking(False)

    my_role = "master" if args.replicaof is None else "slave"

    if args.replicaof:
        master_parts = args.replicaof.split(" ")
        master_host, master_port = master_parts[0], master_parts[1]
    else:
        master_host, master_port = None, None

    shared_store = {}
    shared_streams = {}
    shared_list_store = {}
    shared_sorted_sets = {}
    my_shared_channels = {}
    user_flags = {"nopass"}
    passwords = []
    default_user = "default"

    # Handshake with master server if slave
    if my_role == "slave":
        await handshake_master(master_host,master_port, args.port)

    slave_connections = []

    while True:
        my_connection, _ = await asyncio.get_event_loop().sock_accept(server_socket)  # wait for client
        loop = asyncio.get_event_loop()
        client_channels = {}
        my_current_user = default_user if not passwords else None

        state = State(role = my_role, slave_connections = slave_connections,
                      store = shared_store, streams = shared_streams, list_store = shared_list_store, shared_channels = my_shared_channels,
                      sorted_sets = shared_sorted_sets, default_passwords = passwords, default_user_flags = user_flags,
                      current_user = my_current_user, channels = client_channels, connection = my_connection,
                      is_multi = False, command_queue = [], schedule_remove = lambda k, t: loop.call_later(t, shared_store.pop, k))

        asyncio.create_task(handle_client(state))
        #asyncio.create_task(handle_replica(state))

