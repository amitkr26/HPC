#include <stdio.h>
#include <string.h>
#include <ctype.h>

int main()
{
    char password[50];
    int has_upper, has_lower, has_digit, has_special;

    while(1)
    {
        has_upper = has_lower = has_digit = has_special = 0;

        printf("Enter password: ");
        scanf("%s", password);

        int length = strlen(password);

        for(int i = 0; i < length; i++)
        {
            if(isupper(password[i]))
            {
                has_upper = 1;
            }
            else if(islower(password[i]))
            {
                has_lower = 1;
            }
            else if(isdigit(password[i]))
            {
                has_digit = 1;
            }
            else if(strchr("@#$^&*()-=+{}[]|<,>./", password[i])!=NULL)
            {
                has_special = 1;
            }
        }

        if(length < 8)
        {
            printf("Error: too short.\n");
        }

        if(!has_digit)
        {
            printf("Error: needs digit.\n");
        }

        if(!has_lower)
        {
            printf("Error: needs lower.\n");
        }

        if(!has_upper)
        {
            printf("Error: needs upper.\n");
        }

        if(!has_special)
        {
            printf("Error: needs special.\n");
        }

        if(length > 8 && has_digit && has_lower && has_upper && has_special)
        {
            printf("Password is valid!\n");
            break;
        }
        else
        {
            printf("Invalid password. Try again.\n\n");
        }
    }

    return 0;
}