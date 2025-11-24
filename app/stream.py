from time import time


ENTRY_ID_EQ_SMALLER = "The ID specified in XADD is equal or smaller than the target stream top item"
ENTRY_ID_GT_0_0 = "The ID specified in XADD must be greater than 0-0"
MIN_ENTRY_ID = "0-0"


#
# Interface
#
def validate_entry_id(last_entry_id: str, entry_id: str) -> (bool, str):
    last_entry_id = "0-0" if last_entry_id is None else last_entry_id

    if "*" in entry_id:
        return (True, None)

    if cmp_entry_id(MIN_ENTRY_ID, entry_id) >= 0:
        return (False, ENTRY_ID_GT_0_0)

    if cmp_entry_id(last_entry_id, entry_id) < 0:
        return (True, None)
    else:
        return (False, ENTRY_ID_EQ_SMALLER)


def generate_entry_id(entry_ids: list[str], entry_id: str) -> int:
    if entry_id == "*":
        return generate_auto_entry_id(entry_ids)

    elif entry_id.endswith("-*"):
        new_seq_num = generate_seq_num(entry_ids, entry_id)
        return f"{entry_id.removesuffix('-*')}-{new_seq_num}"

    else:
        return entry_id


#
# Implementation
#
def generate_seq_num(entry_ids: list[str], entry_id: str) -> int:
    max_seq = -1
    for en_time, en_seq in list(map(get_time_seq, entry_ids)):
        if entry_id.startswith(str(en_time) + "-") and max_seq < en_seq:
            max_seq = en_seq

    if max_seq == -1 and entry_id.startswith("0-"):
        return 1
    else:
        return max_seq + 1


def generate_auto_entry_id(entry_ids: list[str]) -> int:
    max_seq = -1
    current_ts = int(time() * 1000)
    for en_time, en_seq in list(map(get_time_seq, entry_ids)):
        if current_ts == en_time and max_seq < en_seq:
            max_seq = en_seq

    return f"{current_ts}-{max_seq + 1}"


def cmp_entry_id(id1: str, id2: str) -> int:
    time1, seq1 = get_time_seq(id1)
    time2, seq2 = get_time_seq(id2)

    if time1 == time2:
        return seq1 - seq2
    else:
        return time1 - time2


def get_time_seq(entry_id: str) -> (int, int):
    return list(map(int, entry_id.split("-")))

