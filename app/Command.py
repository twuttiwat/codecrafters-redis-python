import app.resp as resp

COMMANDS = {}


def command(name=None):
    def decorator(f):
        cmd_name = name if name is not None else f.__name__.lower()
        COMMANDS[cmd_name] = f
        return f

    return decorator


@command()
def ping(ctx):
    return b"+PONG\r\n"


@command()
def echo(ctx, message):
    return resp.encode_bulk_str(message)


@command()
def set(ctx, key, value, exp_unit=None, exp_val=None):
    expired_in_ms = None
    if exp_unit and exp_val:
        match exp_unit.upper():
            case "PX":
                expired_in_ms = int(exp_val)
            case "EX":
                expired_in_ms = int(exp_val) * 1000

    ctx.state.set(key, value, expired_in_ms)
    return resp.OK


@command()
def get(ctx, key):
    value = ctx.state.get(key)
    if value is None:
        return resp.NULL_BULK_STR
    else:
        return resp.encode_bulk_str(value)


@command()
def rpush(ctx, key, value):
    count = ctx.state.rpush(key, value)
    return resp.encode_int(count)


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

    def dispatch(self, ctx):
        func = COMMANDS.get(self.name.lower())
        if not func:
            return "Unknown command"

        final_args = [ctx] + self.args
        return func(*final_args)
