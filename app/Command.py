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

    def get_response(self):
        match self.name.upper():
            case "PING":
                return b"+PONG\r\n"
            case "ECHO":
                # ECHO message
                message = self.args[0]
                message_bulk_str = f"${len(message)}\r\n{message}\r\n".encode()
                return message_bulk_str

