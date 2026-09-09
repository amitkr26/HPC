/* Q11. Simple C Login System:
       - Register a user: prompt to set a username and a password.
       - Login: prompt to enter username and password.
       - Validate credentials against the stored ones.
       - Display success or failure message. */
#include <stdio.h>
#include <string.h>

int main()
{
    char regUser[50], regPass[50];
    char loginUser[50], loginPass[50];

    printf("--- Registration ---\n");
    printf("Enter username: ");
    scanf("%49s", regUser);
    printf("Enter password: ");
    scanf("%49s", regPass);

    printf("\n--- Login ---\n");
    printf("Enter username: ");
    scanf("%49s", loginUser);
    printf("Enter password: ");
    scanf("%49s", loginPass);

    if (strcmp(regUser, loginUser) == 0 && strcmp(regPass, loginPass) == 0)
        printf("\nLogin successful! Welcome, %s.\n", loginUser);
    else
        printf("\nLogin failed! Invalid username or password.\n");

    return 0;
}
