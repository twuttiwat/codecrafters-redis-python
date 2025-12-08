class DecodeError(Exception):
    """Raised when RESP decoding fails"""
    pass


def decode_simple_string(data: bytes) -> tuple[str, int]:
    """
    Decode a simple string from RESP format.
    Returns (decoded_string, bytes_consumed)
    """
    if not data.startswith(b"+"):
        raise DecodeError("Simple string must start with '+'")

    end = data.find(b"\r\n")
    if end == -1:
        raise DecodeError("Incomplete simple string")

    return data[1:end].decode(), end + 2


def decode_bulk_string(data: bytes) -> tuple[str | None, int]:
    """
    Decode a bulk string from RESP format.
    Returns (decoded_string, bytes_consumed) or (None, bytes_consumed) for null
    """
    if not data.startswith(b"$"):
        raise DecodeError("Bulk string must start with '$'")

    end = data.find(b"\r\n")
    if end == -1:
        raise DecodeError("Incomplete bulk string length")

    length = int(data[1:end])
    # Returns None if data is NULL_BULK_STRING
    if length == -1:
        return None, end + 2

    start = end + 2
    if len(data) < start + length + 2:
        raise DecodeError("Incomplete bulk string data")

    string = data[start:start + length].decode()
    return string, start + length + 2


def decode_integer(data: bytes) -> tuple[int, int]:
    """
    Decode an integer from RESP format.
    Returns (decoded_integer, bytes_consumed)
    """
    if not data.startswith(b":"):
        raise DecodeError("Integer string must start with ':'")

    end = data.find(b"\r\n")
    if end == -1:
        raise DecodeError("Incomplete integer")

    return int(data[1:end]), end + 2


def decode_array(data: bytes) -> tuple[list | None, int]:
    """
    Decode an array from RESP format.
    Returns (decoded_array, bytes_consumed) or (None, bytes_consumed) for null
    """
    print(f"decode_array with data: {data}")
    if not data.startswith(b"*"):
        raise DecodeError("Array must start with '*'")

    end = data.find(b"\r\n")
    if end == -1:
        raise DecodeError("Incomplete array length")

    count = int(data[1:end])
    if count == -1:
        return None, end + 2

    result = []
    pos = end + 2

    for _ in range(count):
        if pos >= len(data):
            raise DecodeError("Incomplete array data")

        type_char = chr(data[pos])
        if type_char == "+":
            item, consumed = decode_simple_string(data[pos:])
        elif type_char == "$":
            item, consumed = decode_bulk_string(data[pos:])
        elif type_char == ":":
            item, consumed = decode_integer(data[pos:])
        elif type_char == "*":
            item, consumed = decode_array(data[pos:])
        else:
            raise DecodeError(f"Unknow type character: {type_char}")

        result.append(item)
        pos += consumed

    return result, pos


def decode_null_array(data: bytes) -> tuple[None, int]:
    """
    Decode a null array from RESP format.
    Returns (None, bytes_consumed)
    """
    if not data.startswith(b"*-1\r\n"):
        raise DecodeError("Null array must be '*\\r\\n'")

    return None, 5

def decode(data: bytes) -> tuple[any, int]:
    """
    Decode any RESP data type.
    Returns (decoded_value, bytes_consumed)
    """
    if not data:
        raise  DecodeError("Empty data")

    type_char = chr(data[0])
    if type_char == "+":
        return decode_simple_string(data)
    elif type_char == "$":
        return decode_bulk_string(data)
    elif type_char == ":":
        return decode_integer(data)
    elif type_char == "*":
        return decode_array(data)
    else:
        raise DecodeError(f"Unknow type character: {type_char}")
