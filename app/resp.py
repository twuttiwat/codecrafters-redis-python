OK = b"+OK\r\n"
NULL_BULK_STR = b"$-1\r\n"


def decode_command(bytes_data):
    """Decode simple Redis RESP command array (*N\r\n$len\r\nvalue\r\n...). Returns only command name and arguments"""
    lines = bytes_data.decode().strip().split("\r\n")
    values = lines[2::2]  # skip lenght of array
    return values


def encode_bulk_str(str):
    return f"${len(str)}\r\n{str}\r\n".encode()


def encode_int(num):
    return f":{num}\r\n".encode()
