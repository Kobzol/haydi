import haydi as hd


def test_bool_flags():
    a = hd.Boolean()
    assert not a.filtered
    assert a.step_jumps
    assert a.strict


def test_bool_iter():
    a = hd.Boolean()

    assert list(a) == [False, True]
    assert list(a.cnfs()) == [False, True]


def test_bool_compare():
    assert hd.Boolean() == hd.Boolean()


def test_bool_hash():
    assert len({hd.Boolean(), hd.Boolean()}) == 1
