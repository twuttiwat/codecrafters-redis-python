import socket
import asyncio
import traceback

from app.command_handler import handle_command, State
from app.resp import resp_array_from_strings
import app.decoder as decoder


async def handle_client(state):
    buffer = b''
    try:
        while True:
            data = await state.reader.read(1024)
            if not data:
                break
            buffer += data

            while buffer:
                start_of_array = buffer.find(b"*")
                if start_of_array == -1:
                    buffer = b''
                    continue
                else:
                    buffer = buffer[start_of_array:]

                tokens, consumed = decoder.decode_array(buffer)
                print(f"Received tokens =", tokens)

                response = await handle_command(tokens, state)
                if response:

                    print(f"Response from tokens {tokens}")
                    print(f"{response}")

                    state.writer.write(response)
                    await state.writer.drain()

                buffer = buffer[consumed:]
                print(f"remaining buffer: {buffer=}")

    except Exception as e:
        print("=========== Error handling client ==========", e)
        traceback.print_exc()
    finally:
        state.writer.close()
        await state.writer.wait_closed()

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

    return master_reader, master_writer


async def start(args):
    print(f"Redis EventLoop Start! on port {args.port}")

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
    user_flags = ["nopass"]
    passwords = []
    default_user = "default"

    slave_connections = []

    # Handshake with master server if slave
    if my_role == "slave":
        loop = asyncio.get_event_loop()
        reader, writer = await handshake_master(master_host, int(master_port), int(args.port))
        client_channels = {}
        my_current_user = default_user if not passwords else None

        state = State(role = my_role, reader = reader, writer = writer, slave_connections = slave_connections,
                      store = shared_store, streams = shared_streams, list_store = shared_list_store, shared_channels = my_shared_channels,
                      sorted_sets = shared_sorted_sets, default_passwords = passwords, default_user_flags = user_flags,
                      current_user = my_current_user, channels = client_channels,
                      is_multi = False, command_queue = [], schedule_remove = lambda k, t: loop.call_later(t, shared_store.pop, k))

        asyncio.create_task(handle_client(state))

    async def _handle_client(reader, writer):
        loop = asyncio.get_event_loop()
        client_channels = {}
        my_current_user = default_user if not passwords else None

        state = State(role = my_role, reader = reader, writer = writer, slave_connections = slave_connections,
                      store = shared_store, streams = shared_streams, list_store = shared_list_store, shared_channels = my_shared_channels,
                      sorted_sets = shared_sorted_sets, default_passwords = passwords, default_user_flags = user_flags,
                      current_user = my_current_user, channels = client_channels,
                      is_multi = False, command_queue = [], schedule_remove = lambda k, t: loop.call_later(t, shared_store.pop, k))

        return await handle_client(state)

    server = await asyncio.start_server(
        _handle_client,
        "localhost",
        int(args.port),
    )
    async with server:
        await server.serve_forever()