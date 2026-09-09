/*
 * Question: Check if temperature is hot or cold (30 C or above is Hot).
 * Answer:   Input 35 -> "Hot"
 *           Input 22 -> "Cold"
 */
#include <stdio.h>

int main()
{
    int temperature;

    printf("Enter the temperature: ");
    scanf("%d", &temperature);

    if(temperature >= 30)
    {
        printf("Hot\n");
    }
    else
    {
        printf("Cold\n");
    }

    return 0;
}
