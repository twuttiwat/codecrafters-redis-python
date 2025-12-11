import asyncio
from dataclasses import dataclass
import hashlib

import app.geo as geo
from app.resp import EMPTY_ARRAY, NULL_ARRAY, NULL_BULK_STRING, OK_STRING, bulk_string, resp_array, resp_array_from_strings, resp_int, simple_error, simple_string
from app.sorted_set import SortedSet
from app.stream import validate_entry_id, generate_entry_id
import app.encoder as encoder
import app.decoder as decoder

@dataclass
class State:
    role: str
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    slave_connections: list
    received_bytes: int
    store: dict
    streams: dict
    list_store: dict
    shared_channels: dict
    sorted_sets: dict
    channels: dict
    default_user_flags: list
    default_passwords: list
    current_user: str
    is_multi: bool
    command_queue: list
    schedule_remove: object


def check_range_negative(lst_len, value):
    return max(lst_len + value, 0) if value < 0 else value


async def blpop(list_name: str, timeout: float|None, state) -> bytes:
    timeout = None if timeout == 0.0 else timeout
    try:
        async with asyncio.timeout(timeout):
            while True:
                current_list = state.list_store.get(list_name, [])
                if len(current_list) == 0:
                    print(f"BLPOP: No elements in list")
                    await asyncio.sleep(0.01)
                else:
                    print(f"BLPOP: list: {current_list}")
                    value = current_list.pop(0)
                    response =  resp_array_from_strings([list_name, value])
                    print(f"response: {response}")
                    return response
    except asyncio.TimeoutError:
        print(f"BLPOP Block timeout after {timeout} seconds")
        return b"*-1\r\n"


async def xread_block(timeout, state, stream_key, start_entry):
    timeout = None if timeout == 0.0 else timeout
    if start_entry == "$":
        stream = state.streams.get(stream_key, [])
        start_entry = stream[-1]["id"] if stream else "0-0"
    try:
        async with asyncio.timeout(timeout):
            while True:
                stream = state.streams.get(stream_key, [])

                read_entries = []
                for entry in stream:
                    if entry["id"] > start_entry:
                        read_entries.append(entry)

                if len(read_entries) == 0:
                    #print(f"XREAD BLOCK: No entries in stream")
                    await asyncio.sleep(0.01)
                else:
                    print(f"XREAD BLOCK: {read_entries}")

                    resp_entries = []
                    for entry in read_entries:
                        key_values_arr = resp_array_from_strings(entry["key_values"])
                        resp_entries.append(resp_array([bulk_string(entry["id"]), key_values_arr]))

                    return resp_array([resp_array([bulk_string(stream_key), resp_array(resp_entries)])])

    except asyncio.TimeoutError:
        # print(f"XREAD BLOCK timeout after {timeout} seconds")
        return b"*-1\r\n"


async def handle_command(tokens: list[str], state) -> bytes | None:
    command, *args = tokens
    command = command.upper()

    if command != "AUTH" and state.current_user is None:
        return b"-NOAUTH Authentication required.\r\n"

    subscribed_commands = ["SUBSCRIBE", "UNSUBSCRIBE", "PSUBSCRIBE", "PUNSUBSCRIBE", "PING", "QUIT"]
    if len(state.channels) > 0 and not command in subscribed_commands:
        return simple_error(f"Can't execute '{command}' in subscribed mode")

    if state.is_multi and command != "EXEC" and command != "DISCARD":
        state.command_queue.append(encoder.encode_array(tokens))
        return encoder.encode_simple_string("QUEUED")

    match command.upper():
        case "PING":
            if state.role == "slave":
                return None
            elif len(state.channels) == 0:
                return simple_string("PONG")
            else:
                return encoder.encode_array(["pong", ""])
        case "ECHO":
            return encoder.encode_bulk_string(args[0])
        case "SET":
            key, value = args[0], args[1]

            if len(args) >= 4:
                ttl_unit, ttl_amount = args[2].lower(), int(args[3])
                ttl_seconds = ttl_amount / 1000 if ttl_unit == "px" else ttl_amount
                state.schedule_remove(key, ttl_seconds)

            state.store[key] = value

            # Replicate command to slaves
            print(f"Number of slaves {len(state.slave_connections)}")
            for slave_connection in state.slave_connections:
                print(f"*****Replicate****")
                slave_connection.write(encoder.encode_array(tokens))

            if state.role == "master":
                return encoder.encode_simple_string("OK")
            else:
                return None
        case "GET":
            key = args[0]

            value = state.store.get(key, None)
            if value is not None:
                return encoder.encode_bulk_string(value)
            else:
                return encoder.encode_null_bulk_string()

        case "INCR":
            key = args[0]
            value = state.store.get(key, "0")
            if value.isdigit():
                new_value = int(value) + 1
                state.store[key] = str(new_value)
                return encoder.encode_integer(new_value)
            else:
                print(f"INCR key is {key} and value is {value}")
                return simple_error("value is not an integer or out of range")

        case "TYPE":
            key = args[0]
            value = state.store.get(key, None)
            if value is not None:
                return simple_string("string")
            elif key in state.streams:
                return simple_string("stream")
            else:
                return simple_string("none")

        case "XADD":
            stream_key, entry_id = args[0], args[1]
            key_values = []
            index = 2
            while index + 1 < len(args):
                key, value = args[index], args[index + 1]
                key_values.extend([key, value])
                index += 1

            stream = state.streams.get(stream_key, [])

            last_entry_id = stream[-1]["id"] if (len(stream) > 0) else None
            is_valid, validate_err = validate_entry_id(last_entry_id, entry_id)
            if not is_valid:
                return simple_error(validate_err)

            entry_ids = [entry["id"] for entry in stream]
            entry_id = generate_entry_id(entry_ids, entry_id)

            new_entry = {
                "id": entry_id,
                "key_values": key_values
            }

            stream.append(new_entry)
            state.streams[stream_key] = stream

            return encoder.encode_bulk_string(entry_id)

        case "XRANGE":
            stream_key, start_entry, end_entry = args[0], args[1], args[2]
            stream = state.streams.get(stream_key, [])

            if "-" not in start_entry:
                start_entry = start_entry + "-0"

            if end_entry == "+":
                end_entry = stream[-1]["id"] if stream else "0-0"
            elif "-" not in end_entry:
                end_max_seq = "0"
                for entry_id in stream:
                   if entry_id.startswith(end_entry):
                        end_max_seq = entry_id.split("-")[1]
                end_entry = end_entry + "-" + end_max_seq

            range_entries = []
            for entry in stream:
                if start_entry <= entry["id"] <= end_entry:
                    range_entries.append(entry)

            resp_entries = []
            for entry in range_entries:
                resp_entries.append( encoder.encode_array([ entry["id"], entry["key_values"] ]) )

            return resp_array(resp_entries)

        case "XREAD":
            sub_command = args[0]
            match sub_command.upper():
                case "STREAM":
                    stream_key, start_entry = args[1], args[2]
                    stream = state.streams.get(stream_key, [])

                    read_entries = []
                    for entry in stream:
                        if entry["id"] > start_entry:
                            read_entries.append(entry)

                    resp_entries = []
                    for entry in read_entries:
                        resp_entries.append([
                            entry["id"], entry["key_values"]
                        ])

                    return  encoder.encode_array([
                       stream_key, resp_entries
                    ])

                case "STREAMS":
                    key_and_ids = []
                    index = 1
                    while index < len(args):
                        key_and_ids.append(args[index])
                        index += 1

                    key_id_pairs = []
                    for i in range(0, len(key_and_ids) // 2):
                        stream_key, entry_id = key_and_ids[i], key_and_ids[i + len(key_and_ids) // 2]
                        key_id_pairs.append((stream_key, entry_id))

                    result_entries = []
                    for stream_key, start_entry in key_id_pairs:
                        stream = state.streams.get(stream_key, [])

                        read_entries = []
                        for entry in stream:
                            if entry["id"] > start_entry:
                                read_entries.append(entry)

                        resp_entries = []
                        for entry in read_entries:
                            resp_entries.append([ entry["id"], entry["key_values"] ])

                        result_entries.append([stream_key, resp_entries])

                    return encoder.encode_array(result_entries)

                case "BLOCK":
                    timeout_ms, stream_key, start_entry = int(args[1]), args[3], args[4]
                    print(f"XREAD BLOCK: timeout {timeout_ms}, key {stream_key}, entry {start_entry}")
                    return await xread_block(timeout_ms / 1000.0, state, stream_key, start_entry)

        case "MULTI":
            state.is_multi = True
            return OK_STRING

        case "EXEC":
            if not state.is_multi:
                return simple_error("EXEC without MULTI")
            elif not state.command_queue:
                state.is_multi = False
                return EMPTY_ARRAY
            else:
                state.is_multi = False
                responses = []
                print(f"EXEC command queue: {state.command_queue=}")
                for command in state.command_queue:
                    exec_tokens, _ = decoder.decode_array(command)
                    command_resp = await handle_command(exec_tokens, state)
                    print(f"Command Response {command_resp=}")
                    # decoded_resp, _ = decoder.decode(command_resp)
                    if command_resp:
                        print(f"Response from tokens {exec_tokens=}")
                        print(f"is: {command_resp=}")

                        #state.writer.write(command_resp)
                        #await state.writer.drain()
                        responses.append(command_resp)
                state.command_queue = []
                return resp_array(responses)
                #return encoder.encode_array(responses)

        case "DISCARD":
            if not state.is_multi:
                return simple_error("DISCARD without MULTI")
            else:
                state.is_multi = False
                state.command_queue = []
                return OK_STRING

        case "RPUSH":
            key = args[0]
            current_list = state.list_store.get(key, [])
            elem_index = 1
            while elem_index < len(args):
                current_list.append(args[elem_index])
                elem_index += 1
            state.list_store[key] = current_list
            return encoder.encode_integer(len(current_list))

        case "LPUSH":
            key = args[0]
            current_list = state.list_store.get(key, [])
            elem_index = 1
            while elem_index < len(args):
                current_list.insert(0, args[elem_index])
                elem_index += 1
            state.list_store[key] = current_list
            return encoder.encode_integer(len(current_list))

        case "LLEN":
            key = args[0]
            current_list = state.list_store.get(key, [])
            return encoder.encode_integer(len(current_list))

        case "LPOP":
            key = args[0]
            current_list = state.list_store.get(key, [])
            if len(current_list) == 0:
                return NULL_BULK_STRING
            elif len(args) >= 2:
                count = int(args[1])
                values = []
                for _ in range(count):
                    values.append(current_list.pop(0))
                return encoder.encode_array(values)
            else:
                value = current_list.pop(0)
                return encoder.encode_bulk_string(value)

        case "BLPOP":
            key, timeout = args[0], float(args[1])
            return await blpop(key, timeout, state)

        case "LRANGE":
            key, start, stop = args[0], int(args[1]), int(args[2])

            current_list = state.list_store.get(key, [])
            lst_len = len(current_list)

            start = check_range_negative(lst_len, start)
            stop = check_range_negative(lst_len, stop)

            if lst_len == 0 or start >= lst_len:
                return EMPTY_ARRAY
            else:
                if stop >= lst_len:
                   stop = lst_len - 1
                slice = current_list[start:stop + 1]
                return resp_array_from_strings(slice)

        case "SUBSCRIBE":
            channel_name = args[0]

            channel_clients = state.shared_channels.get(channel_name, [])
            channel_clients.append(state.writer)
            state.shared_channels[channel_name] = channel_clients

            current_channel = state.channels.get(channel_name, None)
            if current_channel is None:
                state.channels[channel_name] = True

            return encoder.encode_array([ "subscribe", channel_name, len(state.channels) ])

        case "UNSUBSCRIBE":
            channel_name = args[0]

            channel_clients = state.shared_channels.get(channel_name, [])
            if state.writer in channel_clients:
                channel_clients.remove(state.writer)
            state.shared_channels[channel_name] = channel_clients

            current_channel = state.channels.get(channel_name, None)
            if not current_channel is None:
                del state.channels[channel_name]

            return encoder.encode_array([ "unsubscribe", channel_name, len(state.channels) ])

        case "PUBLISH":
            channel_name, message = args[:2]

            channel_clients = state.shared_channels.get(channel_name, [])
            channel_resp = encoder.encode_array([ "message", channel_name, message ])
            for client in channel_clients:
                client.write(channel_resp)

            return encoder.encode_integer( len(channel_clients) )

        case "ZADD":
            set_name, score, member = args[0], float(args[1]), args[2]
            current_set = state.sorted_sets.get(set_name, SortedSet())

            count = current_set.add((score, member))
            state.sorted_sets[set_name] = current_set

            return encoder.encode_integer(count)

        case "ZRANK":
            set_name, member = args[:2]
            current_set = state.sorted_sets.get(set_name, SortedSet())

            rank = current_set.rank(member)

            return  encoder.encode_integer(rank) if (rank is not None) else NULL_BULK_STRING

        case "ZRANGE":
            set_name, start, stop = args[0], int(args[1]), int(args[2])
            current_set = state.sorted_sets.get(set_name, SortedSet())

            items = current_set.range(start, stop)
            if items:
                members = [member for (_, member) in items]
                return encoder.encode_array(members)
            else:
                return EMPTY_ARRAY

        case "ZCARD":
            set_name = args[0]
            current_set = state.sorted_sets.get(set_name, SortedSet())
            return encoder.encode_integer(current_set.count())

        case "ZSCORE":
            set_name, member = args[:2]
            current_set = state.sorted_sets.get(set_name, SortedSet())

            score = current_set.score(member)
            if score:
                return encoder.encode_bulk_string(str(score))
            else:
                return NULL_BULK_STRING

        case "ZREM":
            set_name, member = args[:2]
            current_set = state.sorted_sets.get(set_name, SortedSet())

            set_count = current_set.remove(member)
            state.sorted_sets[set_name] = current_set

            return encoder.encode_integer(set_count)

        case "GEOADD":
            loc_key, long, lat, member = args[0], float(args[1]), float(args[2]), args[3]

            invalid_long = not geo.validate_long(long)
            invalid_lat = not geo.validate_lat(lat)
            if invalid_long and invalid_lat:
                return simple_error("invalid longitude and latitude")
            elif invalid_long:
                return simple_error("invalid longitude")
            elif invalid_lat:
                return simple_error("invalid latitude")
            else:
                current_set = state.sorted_sets.get(loc_key, SortedSet())
                score = geo.encode(lat, long)
                set_count = current_set.add((score, member))
                state.sorted_sets[loc_key] = current_set
                return encoder.encode_integer(set_count)

        case "GEOPOS":
            loc_key = args[0]

            # Get list of members
            members = []
            member_index = 1
            while member_index < len(args):
                members.append( args[member_index] )
                member_index += 1

            current_set = state.sorted_sets.get(loc_key, SortedSet())
            if current_set.count() == 0:
                null_responses = [ [-1] for _ in range(1, len(members) + 1) ]
                return encoder.encode_array(null_responses)
            else:
                member_responses = []
                for member in members:
                    score = current_set.score(member)
                    if score is not None:
                        score = int(current_set.score(member))
                        lat, long = geo.decode(score)
                        member_responses.append( [str(long), str(lat)] )
                    else:
                        member_responses.append([-1])
                return encoder.encode_array(member_responses)

        case "GEODIST":
            loc_key, member1, member2 = args[:3]

            current_set = state.sorted_sets.get(loc_key, SortedSet())
            if current_set.count() == 0:
                return NULL_BULK_STRING
            else:
                score1 = int(current_set.score(member1))
                lat1, long1 = geo.decode(score1)

                score2 = int(current_set.score(member2))
                lat2, long2 = geo.decode(score2)

                return encoder.encode_bulk_string( str(geo.haversine(lat1, long1, lat2, long2)) )

        case "GEOSEARCH":
            loc_key, lon, lat, radius, unit = args[0], float(args[2]), float(args[3]), float(args[5]), args[6]

            current_set = state.sorted_sets.get(loc_key, SortedSet())
            if current_set.count() == 0:
                return EMPTY_ARRAY
            else:
                places_in_radius = []
                for score, member in current_set.items:
                    member_lat, member_lon = geo.decode(score)
                    dist_in_m = geo.haversine(lat, lon, member_lat, member_lon)
                    if dist_in_m <= radius:
                        places_in_radius.append(member)
                return resp_array_from_strings(places_in_radius)

        case "ACL":
            sub_command = args[0]
            if sub_command == "WHOAMI":
                if state.current_user:
                    return encoder.encode_bulk_string("default")
                else:
                    return b"-NOAUTH Authentication required.\r\n"
            elif sub_command == "GETUSER":
                user_flags = state.default_user_flags if state.default_user_flags else []
                if state.default_passwords:
                    res = [ "flags", user_flags,
                            "passwords", state.default_passwords ]

                    print(f"Result with default pwd: {res}")

                    return encoder.encode_array([
                            "flags", user_flags,
                            "passwords", state.default_passwords ])
                else:
                    res = [ "flags", user_flags,
                            "passwords", [] ]

                    print(f"Result with NO default pwd: {res}")

                    return encoder.encode_array([
                            "flags", user_flags,
                            "passwords", [] ])
            elif sub_command == "SETUSER":
                user, password = args[1], args[2].removeprefix(">")

                password_hash = hashlib.sha256(password.encode()).hexdigest()
                state.default_passwords.append(password_hash)
                state.default_user_flags = []

                return OK_STRING
            else:
                return NULL_BULK_STRING

        case "AUTH":
            password = args[1]

            if state.default_passwords:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                existing_password = state.default_passwords[0]
                if password_hash == existing_password:
                    state.current_user = "default"
                    return OK_STRING
                else:
                    return b"-WRONGPASS\r\n"
            else:
                return simple_error("WRONGPASS")

        case "INFO":
            sub_command = args[0]
            match sub_command.upper():
                case "REPLICATION":
                    master_replid = "8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb"
                    response_str = f"""role:{state.role}
                                       master_replid:{master_replid}
                                       master_repl_offset:0"""
                    return encoder.encode_bulk_string(response_str)
                case _:
                    return simple_error("Unknow INFO sub-command")

        case "REPLCONF":
            sub_command = args[0]
            match sub_command.upper():
                case "GETACK":
                    ACK_BYTES = 37
                    return encoder.encode_array(["REPLCONF", "ACK", str(state.received_bytes - ACK_BYTES)])
                case _:
                    return OK_STRING

        case "PSYNC":
            replid = "8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb"
            response = encoder.encode_simple_string(f"FULLRESYNC {replid} 0")
            state.writer.write(response)
            state.slave_connections.append(state.writer)

            empty_rdb_hex = "524544495330303131fa0972656469732d76657205372e322e30fa0a72656469732d62697473c040fa056374696d65c26d08bc65fa08757365642d6d656dc2b0c41000fa08616f662d62617365c000fff06e3bfec0ff5aa2"
            return b"$" + str(len(bytes.fromhex(empty_rdb_hex))).encode() + b"\r\n" + bytes.fromhex(empty_rdb_hex)

        # Unknow Command
        case _:
            return simple_error("unknown command")

    return b""