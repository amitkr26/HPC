/*
 * Number Guessing Game
 *
 * The computer picks a random number between 1 and 100. The player keeps
 * guessing until they get it right; the program says whether each guess is
 * too high or too low and counts how many attempts were used.
 *
 * Concepts: while loop, if-else, rand()/srand(), scanf.
 * Built on: Day 1 (I/O) + Day 2 (conditions and loops).
 */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main()
{
    int secret, guess, attempts = 0;

    /* Seed the random generator with the current time so the
       secret number is different every run. */
    srand((unsigned int)time(NULL));
    secret = (rand() % 100) + 1;    /* 1 to 100 */

    printf("Guess my number (1 to 100): ");
    do
    {
        scanf("%d", &guess);
        attempts++;

        if (guess < secret)
        {
            printf("Too low. Try again: ");
        }
        else if (guess > secret)
        {
            printf("Too high. Try again: ");
        }
    } while (guess != secret);

    printf("Correct! The number was %d.\n", secret);
    printf("You took %d attempts.\n", attempts);

    return 0;
}
