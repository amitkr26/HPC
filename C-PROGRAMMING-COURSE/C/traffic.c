#include <stdio.h>

enum traffic {
    RED = 1,
    GREEN = 2,
    YELLOW = 3,
};

int main()
{
    enum traffic light;
    int input;
    printf("Enter the Light (1=RED, 2=GREEN, 3=YELLOW): ");
    scanf("%d", &input);
    light = (enum traffic)input;

    switch(light) {
        case RED:
            printf("Light is RED. Please STOP\n");
            break;
        case GREEN:
            printf("Light is GREEN. Please GO\n");
            break;
        case YELLOW:
            printf("Light is YELLOW. Please prepare to STOP\n");
            break;
        default:
            printf("Invalid\n");
    }

    return 0;
}
