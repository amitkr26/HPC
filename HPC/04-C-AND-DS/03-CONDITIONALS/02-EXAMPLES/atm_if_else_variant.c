/*Write a C program to simulate a simple ATM machine using only if...else statements.
The program should:
1. Ask the user to enter a 4-digit PIN.
○ If the PIN is correct (1234), display a menu with the following options:
1. Check Balance
2. Withdraw Money
3. Deposit Money
○ If the PIN is incorrect, display "Access Denied" and end the program.
2. If the user selects:
○ Check Balance → Display the current balance.
○ Withdraw Money → Ask for the amount to withdraw, check if the balance is
enough, and update the balance.
○ Deposit Money → Ask for the deposit amount and update the balance.
○ Any other choice → Display "Invalid choice".
3. Display a thank-you message before ending the program.*/

#include<stdio.h>
int main()
{
    int pin=1234;
    int currentbalance=5000;
    int choice, withdraw, balance, deposit, newbalance;
    printf("Enter your pin: ");
    scanf("%d", &pin);

    if(pin==1234)
    {
        printf("1. Check Balance\n");
        printf("2. Withdraw Money\n");
        printf("3. Deposit Money\n");
        printf("Select your choice: ");
        scanf("%d", &choice);
        if(choice==1)
        {
            printf("Your current balance is: %d", currentbalance);
        }
        else if(choice==2)
        {
            printf("Enter the amount you want to withdraw :");
            scanf("%d", &withdraw);
            if(withdraw<=currentbalance)
            {
                balance = currentbalance - withdraw;  
                printf("Your withdrawl is successful\n ");
                printf("Your available balance is %d", balance);
            }
            else{
                printf("Available is not enough");
            }
        }
        else if(choice==3)
        {
            printf("How much you want to deposit: ");
            scanf("%d", &deposit);
            newbalance = currentbalance + deposit;
            printf("Your available balance is:%d",newbalance);
        }
        else{
            printf("Invalid choice");
        }

    }
    else{
        printf("Access Denied");
    }

    return 0;

}