#include <stdio.h>
#include<math.h>
int factorial(int k){
    if (k==0 || k==1){
        return 1;
    }
    else{
        return k * factorial(k-1);
    }
}
int main()
{
    int num;
    printf("Enter a number: ");
    scanf("%d", &num);
    printf("%d",factorial(num));
    return 0;
}