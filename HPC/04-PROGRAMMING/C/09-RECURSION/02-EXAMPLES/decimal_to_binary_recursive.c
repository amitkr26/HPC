#include <stdio.h>

void decToBinary(int n) {
    if(n > 1)
        decToBinary(n / 2);
    printf("%d", n % 2);
}

int main() {
    printf("Binary of 10: ");
    decToBinary(10);
    printf("\nBinary of 255: ");
    decToBinary(255);
    printf("\n");
    return 0;
}
