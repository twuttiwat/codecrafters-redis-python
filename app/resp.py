OK = b"+OK\r\n"
NULL_ARRAY = b"*-1\r\n"
NULL_BULK_STR = b"$-1\r\n"


def decode_command(bytes_data):
    """Decode simple Redis RESP command array (*N\r\n$len\r\nvalue\r\n...). Returns only command name and arguments"""
    lines = bytes_data.decode().strip().split("\r\n")
    values = lines[2::2]  # skip lenght of array
    return values


def encode_array(values):
    num_elems = f"*{len(values)}\r\n".encode()
    elems = b"".join([encode_bulk_str(value) for value in values])
    return num_elems + elems


def encode_bulk_str(str):
    return f"${len(str)}\r\n{str}\r\n".encode()


def encode_int(num):
    return f":{num}\r\n".encode()


def encode_simple_str(str):
    return f"+{str}\r\n".encode()
