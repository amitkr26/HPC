/* Q6. Assume the correct password is "admin123". Read a password from the user
       and compare it using strcmp(). Display "Access Granted" or "Access Denied". */
#include <stdio.h>
#include <string.h>

int main()
{
    char password[100];

    printf("Enter password: ");
    fgets(password, sizeof(password), stdin);
    password[strcspn(password, "\n")] = '\0';

    if (strcmp(password, "admin123") == 0)
        printf("Access Granted\n");
    else
        printf("Access Denied\n");

    return 0;
}
