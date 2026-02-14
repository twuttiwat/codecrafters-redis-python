import app.resp as resp

COMMANDS = {}


def command(name=None):
    def decorator(f):
        cmd_name = name if name is not None else f.__name__.lower()
        COMMANDS[cmd_name] = f
        return f

    return decorator


@command()
async def ping(ctx):
    return b"+PONG\r\n"


@command()
async def echo(ctx, message):
    return resp.encode_bulk_str(message)


@command()
async def set(ctx, key, value, exp_unit=None, exp_val=None):
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
async def get(ctx, key):
    value = ctx.state.get(key)
    if value is None:
        return resp.NULL_BULK_STR
    else:
        return resp.encode_bulk_str(value)


@command()
async def rpush(ctx, key, value, *values):
    if len(values) == 0:
        count = ctx.state.rpush(key, value)
    else:
        count = ctx.state.rpush_many(key, [value] + list(values))
    return resp.encode_int(count)


@command()
async def lrange(ctx, key, start, stop):
    values = ctx.state.lrange(key, int(start), int(stop))
    return resp.encode_array(values)


@command()
async def lpush(ctx, key, value, *values):
    if len(values) == 0:
        count = ctx.state.lpush(key, value)
    else:
        count = ctx.state.lpush_many(key, [value] + list(values))
    return resp.encode_int(count)


@command()
async def llen(ctx, key):
    length = ctx.state.llen(key)
    return resp.encode_int(length)


@command()
async def lpop(ctx, key, pop_count=None):
    if pop_count is None:
        value = ctx.state.lpop(key)
        if value is None:
            return resp.NULL_BULK_STR
        else:
            return resp.encode_bulk_str(value)
    else:
        values = ctx.state.lpop_many(key, int(pop_count))
        return resp.encode_array(values)


@command()
async def blpop(ctx, key, timeout):
    value = await ctx.state.blpop(key, float(timeout))
    if value is None:
        return resp.NULL_ARRAY
    else:
        return resp.encode_array([key, value])


@command()
async def type(ctx, key):
    value = ctx.state.type(key)
    if value is None:
        return resp.encode_simple_str("none")
    else:
        return resp.encode_simple_str(value)


@command()
async def xadd(ctx, key, id, *fields):
    try:
        result = ctx.state.xadd(key, id, *fields)
        return resp.encode_bulk_str(result)
    except ValueError as e:
        print(f"Error adding to stream: {e}")
        return resp.encode_simple_err(str(e))


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

    async def dispatch(self, ctx):
        func = COMMANDS.get(self.name.lower())
        if not func:
            return "Unknown command"

        final_args = [ctx] + self.args
        result = await func(*final_args)
        return result
