import weakref
from _api import ffi, lib

# API out-of-line mode
assert lib.test_function(0) == 1

t = (1, 2, 3, 4, 5)
assert lib.test_tuple(t, len(t)) == sum(t)

# items from Map
items = [
    ((1, 2, 3), (1, (1, 2, 3))),
    ((4, 5, 6), (1, (4, 5, 6)))
]

mapping = ffi.new("struct mapping[{}]".format(len(items)))

# dynamic memory must be cached so that it won't be GC'ed
cache = weakref.WeakKeyDictionary()

for index, item in enumerate(items):
    mapping[index].keySize = 3
    mapping[index].value1 = item[1][0]
    mapping[index].value2Size = len(item[1][1])

    keys = ffi.new("int[]".format(len(item[0])), item[0])
    mapping[index].key = keys
    cache[mapping[index]] = keys

    values = ffi.new("int[]".format(len(item[1][1])), item[1][1])
    mapping[index].value2 = values
    cache[mapping[index]] = values


print(lib.test_mapping(mapping, len(items)))
