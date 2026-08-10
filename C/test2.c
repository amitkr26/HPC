#include <stdio.h>

int main() {
    
    int x =10, y=20,z;
    z=x++ * --y;
    printf("%d %d %d\n", x,y,z);

    return 0;
}