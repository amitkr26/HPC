#include <stdio.h>

enum Day { MON, TUE, WED, THU, FRI, SAT, SUN };
enum Color { RED, GREEN, BLUE };

int main() {
    enum Day today = WED;
    enum Color favorite = BLUE;

    printf("Today is day number: %d\n", today);
    printf("Favorite color number: %d\n", favorite);

    switch(today) {
        case MON: printf("Monday\n"); break;
        case TUE: printf("Tuesday\n"); break;
        case WED: printf("Wednesday\n"); break;
        default: printf("Other day\n");
    }
    return 0;
}
