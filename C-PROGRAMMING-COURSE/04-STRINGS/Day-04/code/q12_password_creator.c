/* Q12. Secure Password Creator:
       Repeatedly prompt for a password until it meets all criteria:
       - at least 8 characters
       - at least one uppercase letter (A-Z)
       - at least one lowercase letter (a-z)
       - at least one digit (0-9)
       - at least one special character
       For each failed attempt, list exactly which requirements were not met. */
#include <stdio.h>
#include <string.h>
#include <ctype.h>

int main()
{
    char password[100];
    char special[] = "!@#$%^&*()_+-=[]{}|;:'\",.<>/?";
    int len, hasUpper, hasLower, hasDigit, hasSpecial;
    int valid, i, j;

    do
    {
        printf("Enter a new password: ");
        fgets(password, sizeof(password), stdin);
        password[strcspn(password, "\n")] = '\0';

        len = strlen(password);
        hasUpper = hasLower = hasDigit = hasSpecial = 0;

        for (i = 0; i < len; i++)
        {
            if (isupper(password[i]))
                hasUpper = 1;
            if (islower(password[i]))
                hasLower = 1;
            if (isdigit(password[i]))
                hasDigit = 1;
            for (j = 0; special[j] != '\0'; j++)
            {
                if (password[i] == special[j])
                    hasSpecial = 1;
            }
        }

        valid = 1;
        if (len < 8)
        {
            printf("  - Password must be at least 8 characters long.\n");
            valid = 0;
        }
        if (!hasUpper)
        {
            printf("  - Password must contain at least one uppercase letter (A-Z).\n");
            valid = 0;
        }
        if (!hasLower)
        {
            printf("  - Password must contain at least one lowercase letter (a-z).\n");
            valid = 0;
        }
        if (!hasDigit)
        {
            printf("  - Password must contain at least one digit (0-9).\n");
            valid = 0;
        }
        if (!hasSpecial)
        {
            printf("  - Password must contain at least one special character.\n");
            valid = 0;
        }

        if (!valid)
            printf("  Please try again.\n");
    } while (!valid);

    printf("Password has been set successfully.\n");

    return 0;
}
