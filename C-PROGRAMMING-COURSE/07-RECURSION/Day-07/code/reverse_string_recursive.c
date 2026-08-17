#include <stdio.h>

void reverseString(char *s) {
    if(*s == '\0') return;
    reverseString(s + 1);
    printf("%c", *s);
}

int main() {
    printf("Reverse of HELLO: ");
    reverseString("HELLO");
    printf("\n");
    return 0;
}
