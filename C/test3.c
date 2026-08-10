#include <stdio.h>

int main() {

    int p=4,q;
    q= ++p * p++;
    printf("%d %d", p,q);

    return 0;
}