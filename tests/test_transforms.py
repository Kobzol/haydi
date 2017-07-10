from testutils import init
init()

import haydi as hd  # noqa


def test_take():
    r = hd.Range(10)

    assert range(10) == list(r.take(100))
    assert range(5) == list(r.take(5))


def test_take_filter():
    def f(x):
        return x % 2 == 0

    r = hd.Range(20)

    a = r.iterate().filter(f).take(3)
    assert list(a) == [0, 2, 4]

    b = r.iterate().take(3).filter(f)
    assert list(b) == [0, 2]


def test_map():
    r = hd.Range(5)
    assert [0, 2, 4, 6, 8] == list(r.map(lambda x: x * 2))


def test_map2():
    r = hd.Range(10).filter(lambda x: x % 2 == 0).map(lambda x: x * 10)
    assert [0, 20, 40, 60, 80] == list(r)
    assert [20, 40] == list(r.iterate_steps(2, 5))


def test_sparse_map():
    r = hd.Range(6).filter(lambda x: x % 2 == 1)
    result = list(r.map(lambda x: x * 10).iterate_steps(0, 5))
    assert result == [10, 30]


def test_filter():
    r = hd.Range(10)

    assert list(r.filter(lambda x: False)) == []
    assert list(r.filter(lambda x: True)) == range(10)
    assert list(r.filter(lambda x: x % 2 == 1)) == [1, 3, 5, 7, 9]

    f = r.filter(lambda x: False)
    assert not f.strict

    f = r.filter(lambda x: False, strict=True)
    assert f.strict
