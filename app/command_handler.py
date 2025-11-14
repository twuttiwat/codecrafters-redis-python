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
