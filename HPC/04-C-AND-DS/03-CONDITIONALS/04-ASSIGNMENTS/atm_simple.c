/*
 * Question (Bonus): Simulate a simple ATM machine using only if...else statements.
 *           1. Ask for a 4-digit PIN.
 *              - Correct PIN (1234) shows a menu:
 *                1. Check Balance
 *                2. Withdraw Money
 *                3. Deposit Money
 *              - Incorrect PIN prints "Access Denied" and ends the program.
 *           2. Based on the choice:
 *              - Check Balance  -> display current balance
 *              - Withdraw Money -> ask amount, verify enough balance, update it
 *              - Deposit Money  -> ask amount, update the balance
 *              - Any other      -> "Invalid choice"
 *           3. Print a thank-you message before ending.
 * Answer:   PIN 1234 -> menu. Wrong PIN -> "Access Denied".
 *           Starting balance is 5000.
 */
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
