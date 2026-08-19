#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int getUserGuess()
{
    int guess;
    printf("Enter your guess (1-100, 0 to exit): ");
    scanf("%d", &guess);
    return guess;
}

int checkGuess(int guess, int target)
{
    if (guess > target)
    {
        printf("Too high!\n");
        return 0;
    }
    else if (guess < target)
    {
        printf("Too low!\n");
        return 0;
    }
    printf("Correct! The number was %d.\n", target);
    return 1;
}

int main()
{
    int target, guess, correct = 0;

    srand(time(0));
    target = (rand() % 100) + 1;

    printf("===== NUMBER GUESSING GAME =====\n");
    printf("I have picked a number between 1 and 100.\n");

    while (!correct)
    {
        guess = getUserGuess();

        if (guess == 0)
        {
            printf("You chose to exit. The number was %d. Goodbye!\n", target);
            break;
        }

        correct = checkGuess(guess, target);
    }

    return 0;
}