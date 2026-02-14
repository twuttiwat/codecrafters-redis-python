import time
from dataclasses import dataclass


@dataclass
class StreamDict:
    dict = {}

    def validate_entry_id(self, stream, entry_id):
        [ms, seq] = entry_id.split("-")
        last_ms = last_seq = "0"
        if stream:
            [last_ms, last_seq] = stream[-1][0].split("-")

        def id_less_than_or_equal_last():
            return int(ms) < int(last_ms) or (
                int(ms) == int(last_ms) and int(seq) <= int(last_seq)
            )

        if entry_id == "0-0":
            return False, "ERR The ID specified in XADD must be greater than 0-0"
        elif id_less_than_or_equal_last():
            return (
                False,
                "ERR The ID specified in XADD is equal or smaller than the target stream top item",
            )
        else:
            return True, None

    def gen_entry_seq(self, stream, entry_ms):
        seq = "0"
        if stream:
            for curr_entry in stream[::-1]:
                [curr_ms, curr_seq] = curr_entry[0].split("-")
                if curr_ms == entry_ms:
                    seq = str(int(curr_seq) + 1)
                    break
        return seq

    def gen_full_entry_id(self, stream):
        unix_timestamp_ms = str(int(time.time() * 1000))
        seq = "0"
        if stream:
            for curr_entry in stream[::-1]:
                [curr_ms, curr_seq] = curr_entry[0].split("-")
                if curr_ms == unix_timestamp_ms:
                    seq = int(curr_seq) + 1
                    break

        return f"{unix_timestamp_ms}-{seq}"

    def gen_partial_entry_id(self, stream, entry_id):
        [ms, _] = entry_id.split("-")
        seq = "0"
        if stream:
            for curr_entry in stream[::-1]:
                [curr_ms, curr_seq] = curr_entry[0].split("-")
                if curr_ms == ms:
                    seq = int(curr_seq) + 1
                    break

        if ms == "0" and seq == "0":
            return "0-1"
        else:
            return f"{ms}-{seq}"

    def xadd(self, stream_key, entry_id, *fields):
        stream = self.dict.setdefault(stream_key, [])

        if entry_id == "*":
            entry_id = self.gen_full_entry_id(stream)
        elif entry_id.endswith("-*"):
            entry_id = self.gen_partial_entry_id(stream, entry_id)
        else:
            is_valid, error_message = self.validate_entry_id(stream, entry_id)
            if not is_valid:
                raise ValueError(error_message)

        key_value_pairs = list(zip(fields[::2], fields[1::2]))
        stream.append((entry_id, key_value_pairs))
        return entry_id

    def has_key(self, key):
        return key in self.dict
