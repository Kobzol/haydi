import cffi

ffibuilder = cffi.FFI()
ffibuilder.set_source("_api", r"""
    #include <test.h>
""",
                      libraries=["test"],
                      library_dirs=["./"],
                      include_dirs=["./"])   # <=
ffibuilder.cdef(r"""
    struct mapping
    {
        int* key;
        int keySize;
        int value1;
        int* value2;
        int value2Size;
    };

    int test_function(int x);
    int test_tuple(int* x, int count);
    int test_mapping(struct mapping* m, int count);
""")

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
