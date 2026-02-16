import time
from dataclasses import dataclass


@dataclass
class EntryId:
    ms: int
    seq: int

    def __init__(self, ms: int, seq: int):
        self.ms = int(ms)
        self.seq = int(seq)

    def __lt__(self, other):
        if self.ms == other.ms:
            return self.seq < other.seq
        return self.ms < other.ms

    def __le__(self, other):
        if self.ms == other.ms:
            return self.seq <= other.seq
        print(f"type of self ms {type(self.ms)} ::type of other ms {type(other.ms)}")
        return self.ms <= other.ms

    def __gt__(self, other):
        if self.ms == other.ms:
            return self.seq > other.seq
        return self.ms > other.ms

    def __ge__(self, other):
        if self.ms == other.ms:
            return int(self.seq) >= int(other.seq)
        return int(self.ms) >= int(other.ms)

    def __eq__(self, other):
        return self.ms == other.ms and self.seq == other.seq

    def __ne__(self, other):
        return self.ms != other.ms or self.seq != other.seq

    def __repr__(self):
        return f"{self.ms}-{self.seq}"

    @staticmethod
    def gen_entry_seq(stream, entry_ms: int) -> int:
        seq = 0
        print(f"stream {stream}")
        if stream:
            for entry in stream[::-1]:
                if entry.id.ms == entry_ms:
                    seq = entry.id.seq + 1
                    break
        return seq

    @staticmethod
    def gen_full_entry_id(stream):
        unix_timestamp_ms = int(time.time() * 1000)
        seq = EntryId.gen_entry_seq(stream, unix_timestamp_ms)
        return EntryId(unix_timestamp_ms, seq)

    @staticmethod
    def gen_partial_entry_id(stream, entry_id):
        [ms, _] = entry_id.split("-")
        seq = EntryId.gen_entry_seq(stream, int(ms))

        if ms == "0" and seq == 0:
            return EntryId(0, 1)
        else:
            e = EntryId(int(ms), int(seq))
            print(f"gen_partial_entry_id: {e}")
            return EntryId(int(ms), int(seq))

    @staticmethod
    def parse(raw_id, stream) -> EntryId:

        def gen_id() -> EntryId:
            if raw_id == "*":
                return EntryId.gen_full_entry_id(stream)
            elif raw_id.endswith("-*"):
                return EntryId.gen_partial_entry_id(stream, raw_id)
            else:
                raise ValueError("Invalid Generate ID format")

        if "*" in raw_id:
            return gen_id()

        match raw_id.split("-"):
            case [ms, seq]:
                return EntryId(int(ms), int(seq))
            case [ms]:
                return EntryId(int(ms), 0)
            case _:
                raise ValueError("Invalid ID format")


INITIAL_ID = EntryId(0, 0)


@dataclass
class Entry:
    id: EntryId
    fields: list[str]
    # cmp_funs: list[str] = ["__lt__", "__gt__", "__eq__", "__ne__", "__le__", "__ge__"]

    # def __getattr__(self, name):
    #     if name in self.cmp_funs:
    #         return getattr(self.id, name)
    #     return getattr(self, name)


class StreamDict:
    dict: dict[str, list[Entry]] = {}

    def has_key(self, key):
        return key in self.dict

    def xadd(self, stream_key, raw_entry_id, *fields):
        stream = self.dict.setdefault(stream_key, [])
        entry_id = EntryId.parse(raw_entry_id, stream)

        def validate_add_id():
            last_entry_id = INITIAL_ID
            if stream:
                last_entry_id = stream[-1].id

            if entry_id == INITIAL_ID:
                return False, "ERR The ID specified in XADD must be greater than 0-0"
            elif entry_id <= last_entry_id:
                return (
                    False,
                    "ERR The ID specified in XADD is equal or smaller than the target stream top item",
                )
            else:
                return True, None

        is_valid, error_message = validate_add_id()
        if not is_valid:
            raise ValueError(error_message)

        entry_id = EntryId.parse(raw_entry_id, stream)
        entry = Entry(entry_id, list(fields))
        stream.append(entry)

        return str(entry_id)

    def xrange(self, stream_key, start, end):
        stream = self.dict.get(stream_key, [])

        start_id, end_id = None, None
        if start == "-":
            start_id = EntryId(0, 1)
        if end == "+":
            end_id = stream[-1].id

        if start_id is None:
            start_id = EntryId.parse(start, stream)
        if end_id is None:
            end_id = EntryId.parse(end, stream)

        result = []
        for entry in stream:
            if start_id <= entry.id <= end_id:
                result.append([str(entry.id), entry.fields])

        return result

    def xread(self, stream_key_id_pairs):
        result = []
        for stream_key, id in stream_key_id_pairs:
            stream = self.dict.get(stream_key, [])

            entry_id = EntryId.parse(id, stream)

            read_entries = []
            for entry in stream:
                if entry.id > entry_id:
                    read_entries.append([str(entry.id), entry.fields])
                    break
            stream_result = [stream_key, read_entries]
            result.append(stream_result)

        return result
