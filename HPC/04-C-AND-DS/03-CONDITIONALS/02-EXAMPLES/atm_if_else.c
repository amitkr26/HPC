#include <stdio.h>
 
int main()
{
    int pin, choice;
    float balance = 5000.0, amount;
 
    printf("Enter your 4-digit PIN: ");
    scanf("%d", &pin);
 
    if(pin == 1234)
    {
        printf("\nWelcome!\n");
        printf("1. Check Balance\n");
        printf("2. Withdraw Money\n");
        printf("3. Deposit Money\n");
        printf("Enter your choice: ");
        scanf("%d", &choice);
 
        if(choice == 1)
        {
            printf("Your current balance is: %.2f\n", balance);
        }
        else if(choice == 2)
        {
            printf("Enter amount to withdraw: ");
            scanf("%f", &amount);
 
            if(amount <= balance)
            {
                balance = balance - amount;
                printf("Withdrawal successful. New balance: %.2f\n", balance);
            }
            else
            {
                printf("Insufficient balance.\n");
            }
        }
        else if(choice == 3)
        {
            printf("Enter amount to deposit: ");
            scanf("%f", &amount);
 
            balance = balance + amount;
            printf("Deposit successful. New balance: %.2f\n", balance);
        }
        else
        {
            printf("Invalid choice.\n");
        }
    }
    else
    {
        printf("Access Denied\n");
    }
 
    printf("Thank you for using our ATM.\n");
 
    return 0;
}