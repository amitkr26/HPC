#include <stdio.h>

union Data {
    int i;
    float f;
    char c;
};

int main() {
    union Data d;
    printf("Size of union: %lu bytes\n", sizeof(union Data));

    d.i = 10;
    printf("d.i = %d\n", d.i);

    d.f = 3.14;
    printf("d.f = %.2f (d.i is now garbage)\n", d.f);

    d.c = 'A';
    printf("d.c = %c\n", d.c);

    return 0;
}
