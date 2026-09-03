#include <stdio.h>

int isPalindrome(int n) {
    int original = n, reversed = 0, remainder;
    while(n > 0) {
        remainder = n % 10;
        reversed = reversed * 10 + remainder;
        n /= 10;
    }
    return (original == reversed);
}

int main() {
    int num = 121;
    if(isPalindrome(num))
        printf("%d is palindrome\n", num);
    else
        printf("%d is not palindrome\n", num);
    return 0;
}
