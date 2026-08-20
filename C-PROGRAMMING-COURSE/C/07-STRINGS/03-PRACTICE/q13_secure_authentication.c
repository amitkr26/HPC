/* Q13. Secure User Authentication:
       Registration: create a username and a password that meets security
       criteria (min 8 chars, at least one uppercase, one lowercase, one digit,
       one special character). Loop until the password is valid.
       Then login: validate entered credentials and display success/failure. */
#include <stdio.h>
#include <string.h>
#include <ctype.h>

int checkPassword(char p[])
{
    char special[] = "!@#$%^&*()_+-=[]{};:'\",.<>/?";
    int len = strlen(p);
    int hasUpper = 0, hasLower = 0, hasDigit = 0, hasSpecial = 0;
    int fail = 0, i, j;

    if (len < 8)
    {
        printf("  - At least 8 characters are required.\n");
        fail = 1;
    }

    for (i = 0; p[i] != '\0'; i++)
    {
        if (isupper(p[i]))
            hasUpper = 1;
        else if (islower(p[i]))
            hasLower = 1;
        else if (isdigit(p[i]))
            hasDigit = 1;
        else
        {
            for (j = 0; special[j] != '\0'; j++)
            {
                if (p[i] == special[j])
                    hasSpecial = 1;
            }
        }
    }

    if (!hasUpper)
    {
        printf("  - At least one uppercase letter (A-Z) is required.\n");
        fail = 1;
    }
    if (!hasLower)
    {
        printf("  - At least one lowercase letter (a-z) is required.\n");
        fail = 1;
    }
    if (!hasDigit)
    {
        printf("  - At least one digit (0-9) is required.\n");
        fail = 1;
    }
    if (!hasSpecial)
    {
        printf("  - At least one special character is required.\n");
        fail = 1;
    }

    return fail;
}

int main()
{
    char username[50], password[50];
    char loginUser[50], loginPass[50];
    char ch;
    int retry;

    printf("--- Registration ---\n");
    printf("Enter username: ");
    scanf("%49s", username);
    while ((ch = getchar()) != '\n' && ch != EOF)
        ;

    do
    {
        printf("Enter a password (8+ chars, A-Z, a-z, 0-9, special): ");
        fgets(password, sizeof(password), stdin);
        password[strcspn(password, "\n")] = '\0';

        retry = checkPassword(password);
        if (retry != 0)
            printf("  Please try again.\n");
    } while (retry != 0);

    printf("Registration successful.\n");

    printf("\n--- Login ---\n");
    printf("Enter username: ");
    scanf("%49s", loginUser);
    printf("Enter password: ");
    scanf("%49s", loginPass);

    if (strcmp(username, loginUser) == 0 && strcmp(password, loginPass) == 0)
        printf("\nLogin successful! Welcome, %s.\n", loginUser);
    else
        printf("\nLogin failed! Invalid username or password.\n");

    return 0;
}
