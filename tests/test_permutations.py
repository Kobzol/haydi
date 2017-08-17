import haydi as hd


def test_permutations_iterate():
    v = hd.Values(("A", "B", "C"))
    p = hd.Permutations(v)
    assert p.size == 6

    result = set(p)
    expected = {('A', 'B', 'C'), ('A', 'C', 'B'), ('B', 'A', 'C'),
                ('B', 'C', 'A'), ('C', 'A', 'B'), ('C', 'B', 'A')}
    assert result == expected


def test_permutations_to_values():
    r = hd.Range(3)
    p = hd.Permutations(r)

    v = p.to_values()

    assert isinstance(v, hd.Values)
    assert list(v) == list(p)


def test_permutations_to_values_maxsize():
    r = hd.Range(3)
    p = hd.Permutations(r)

    v = p.to_values(max_size=r.size)

    assert isinstance(v, hd.Permutations)
    assert isinstance(v.domain, hd.Values)
    assert list(v) == list(p)


def test_permutations_compare():
    r = hd.Range(5)
    assert hd.Permutations(r) == hd.Permutations(r)
    assert hd.Permutations(r) != hd.Permutations(hd.Range(6))


def test_permutations_hash():
    assert len({hd.Permutations(hd.Range(5)),
                hd.Permutations(hd.Range(5))}) == 1
