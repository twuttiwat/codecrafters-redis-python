ENTRY_ID_EQ_SMALLER = "The ID specified in XADD is equal or smaller than the target stream top item"
ENTRY_ID_GT_0_0 = "The ID specified in XADD must be greater than 0-0"
MIN_ENTRY_ID = "0-0"

# Interface
def validate_entry_id(last_entry_id: str, entry_id: str) -> (bool, str):
    last_entry_id = "0-0" if last_entry_id is None else last_entry_id

    if cmp_entry_id(MIN_ENTRY_ID, entry_id) >= 0:
        return (False, ENTRY_ID_GT_0_0)

    if cmp_entry_id(last_entry_id, entry_id) < 0:
        return (True, None)
    else:
        return (False, ENTRY_ID_EQ_SMALLER)


# Implementation
def cmp_entry_id(id1: str, id2: str) -> int:
    time1, seq1 = get_time_seq(id1)
    time2, seq2 = get_time_seq(id2)

    if time1 == time2:
        return seq1 - seq2
    else:
        return time1 - time2

def get_time_seq(entry_id: str) -> (int, int):
    return list(map(int, entry_id.split("-")))

"""
if __name__ == "__main__":
    test_cases = [
        {"last_entry_id": None, "entry_id": "1-1", "result" : (True,)},
        {"last_entry_id": "1-1", "entry_id": "1-2", "result" : (True,)},
        {"last_entry_id": "1-2", "entry_id": "1-2", "result" : (False, ENTRY_ID_EQ_SMALLER)},
        {"last_entry_id": "1-2", "entry_id": "0-3", "result" : (False, ENTRY_ID_EQ_SMALLER)},
        {"last_entry_id": "1-2", "entry_id": "0-0", "result" : (False, ENTRY_ID_GT_0_0)}
    ]

    for i, test_case in enumerate(test_cases):
        expected_result = test_case["result"]
        actual_result = validate_entry_id(test_case["last_entry_id"], test_case["entry_id"])
        print(f"test_case {i}: {expected_result} ({"✅" if actual_result == expected_result else "❌"})")
"""
