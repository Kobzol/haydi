#pragma once

struct mapping
{
    int* key;
    int keySize;
    int value1;
    int* value2;
    int value2Size;
};

#ifdef __cplusplus
extern "C" {
#endif

int test_function(int x);
int test_tuple(int* x, int count);
int test_mapping(struct mapping* m, int count);

#ifdef __cplusplus
}
#endif
