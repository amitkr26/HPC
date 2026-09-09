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
    if (guess == target)
    {
        printf("Congratulations! You guessed the correct number: %d\n", target);
        return 1;
    }
    else if (guess > target)
        printf("Too high! Try again.\n");
    else
        printf("Too low! Try again.\n");
    return 0;
}

int main()
{
    int target, guess, correct = 0;

    srand(time(0));
    target = (rand() % 100) + 1;

    printf("========== NUMBER GUESSING GAME ==========\n");
    printf("I have chosen a number between 1 and 100.\n");
    printf("Enter 0 at any time to exit the game.\n");
    printf("==========================================\n\n");

    while (correct == 0)
    {
        guess = getUserGuess();

        if (guess == 0)
        {
            printf("\nYou chose to exit. The secret number was %d.\n", target);
            printf("Better luck next time!\n");
            break;
        }

        correct = checkGuess(guess, target);
    }

    printf("\n===== GAME OVER =====\n");
    return 0;
}
