import app.resp as resp

class Command:
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __repr__(self):
        return f"{self.name}{self.args}"

    @staticmethod
    def parse(bytes_data):
        values = resp.decode_command(bytes_data)
        match values:
            case [command, *args]:
                return Command(command, args)
            case _:
                raise ValueError("Invalid or empty RESP command array")

    def get_response(self, server):
        match self.name.upper():
            case "PING":
                return b"+PONG\r\n"
            case "ECHO":
                # ECHO message
                message = self.args[0]
                return resp.encode_bulk_str(message)
            case "SET":
                key, value = self.args[0], self.args[1]
                server.set(key, value)
                return resp.OK
            case "GET":
                key = self.args[0]
                value = server.get(key)
                if value is None:
                    return resp.NULL_BULK_STR
                else:
                    return resp.encode_bulk_str(value)

