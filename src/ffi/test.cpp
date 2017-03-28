#include "test.h"

extern "C" int test_function(int x)
{
    return x + 1;
}
extern "C" int test_tuple(int* x, int count)
{
    int sum = 0;
    for (int i = 0; i < count; i++)
    {
        sum += x[i];
    }

    return sum;
}
extern "C" int test_mapping(struct mapping* m, int count)
{
    int sum = 0;

    for (int i = 0; i < count; i++)
    {
        for (int j = 0; j < m[i].value2Size; j++)
        {
            sum += m[i].value2[j];
        }
    }

    return sum;
}
