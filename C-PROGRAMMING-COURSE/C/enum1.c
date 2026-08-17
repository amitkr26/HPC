#include <stdio.h>

enum WeekDays {
    MONDAY,
    TUESDAY,
    WEDNESDAY,
    THURSDAY,
    FRIDAY,
    SATURDAY,
    SUNDAY
};

int main()
{
    enum WeekDays today;
    today = MONDAY;

    if(today == MONDAY) {
        printf("It is the start of the week\n");
    }

    printf("The integer value of MONDAY is: %d\n", MONDAY);

    return 0;
}
