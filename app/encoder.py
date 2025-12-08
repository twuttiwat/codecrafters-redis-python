def encode_simple_string(s: str) -> bytes:
    """Encode a simple string: +OK\r\n"""
    return f"+{s}\r\n".encode()


def encode_null_bulk_string() -> bytes:
    return "$-1\r\n".encode()


def encode_bulk_string(s: str | None) -> bytes:
    """Encode a bulk string: $6\r\n\foobar\r\n or null bulk string: $-1\r\n"""
    if s is None:
        return b"$-1\r\n"
    return f"${len(s)}\r\n{s}\r\n".encode()


def encode_integer(n: int) -> bytes:
    """Encode an integer: :1000\r\n"""
    return f":{n}\r\n".encode()


def encode_array(items: list | None) -> bytes:
    """Encode an array of items or null array: *-1\r\n"""
    if items is None or items == [-1]:
        return b"*-1\r\n"

    result = f"*{len(items)}\r\n".encode()
    for item in items:
        if isinstance(item, str):
            result += encode_bulk_string(item)
        elif isinstance(item, int):
            result += encode_integer(item)
        elif isinstance(item, list):
            result += encode_array(item)
        elif item is None:
            result += encode_bulk_string(None)
    return result


def encode_null_array() -> bytes:
    """Encode a null array: *-1\r\n"""
    return b"*-1\r\n"