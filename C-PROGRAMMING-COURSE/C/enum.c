#include <stdio.h>

enum level {
    Low = 1,
    Medium,
    High
};

int main()
{
    enum level myvar = High;

    switch(myvar) {
        case Low:
            printf("Low level\n");
            break;
        case Medium:
            printf("Medium level\n");
            break;
        case High:
            printf("High level\n");
            break;
        default:
            printf("Unknown level\n");
    }

    return 0;
}