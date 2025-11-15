from dataclasses import dataclass

@dataclass
class State:
    store: dict
    is_multi: bool
    command_queue: list
    schedule_remove: object

def process_command(data, state):
    if data.startswith("*"):
        lines = data.split("\r\n")
        command = lines[2].upper()

        if state.is_multi and command != "EXEC":
            state.command_queue.append(data)
            return b"+QUEUED\r\n"

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
            case "EXEC":
                if not state.is_multi:
                    print(f"Error Exec")
                    response = b"-ERR EXEC without MULTI\r\n"
                elif not state.command_queue:
                    print(f"No queue: {state.command_queue}")
                    state.is_multi = False
                    response = b"*0\r\n";
                else:
                    print(f"Ok")
                    response = b"+OK\r\n"
            case _:
                response = b"-ERR unknown command\r\n"
        return response
    else:
        return b"-ERR invalid request\r\n"
