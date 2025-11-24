import stream

#
# validate_entry_id
#
def test_validate_entry_id_with_first_entry_id():
    """First entry_id should work"""
    actual = stream.validate_entry_id(None, "1-1")
    assert actual == (True, None)


def test_validate_entry_id_with_larger_entry_id():
    """Entry_id greater than last_entry_id should work"""
    actual = stream.validate_entry_id("1-1", "1-2")
    assert actual == (True, None)


def test_validate_entry_id_with_equal_entry_id():
    """Entry_id equal with last_entry_id should fail"""
    actual = stream.validate_entry_id("1-2", "1-2")
    assert actual == (False, stream.ENTRY_ID_EQ_SMALLER)


def test_validate_entry_id_with_smaller_entry_id():
    """Entry_id smaller with last_entry_id should fail"""
    actual = stream.validate_entry_id("1-2", "0-3")
    assert actual == (False, stream.ENTRY_ID_EQ_SMALLER)


def test_validate_entry_id_with_min_entry_id():
    """Entry Id smaller than minimum id should fail"""
    actual = stream.validate_entry_id("1-2", "0-0")
    assert actual == (False, stream.ENTRY_ID_GT_0_0)


#
# generate_seq_num
#
def test_generate_seq_num_with_no_prior_entries():
    """Sequence Number with no prior entries should be 1"""
    actual = stream.generate_seq_num([], "0-*")
    assert actual == 1


def test_generate_seq_num_with_prior_entries():
    """Sequence Number with no prior entries should be 1"""
    actual = stream.generate_seq_num([], "5-*")
    assert actual == 0


