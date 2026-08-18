#include <stdio.h>
#include <string.h>

int isPalindrome(char *s, int start, int end) {
    if(start >= end) return 1;
    if(s[start] != s[end]) return 0;
    return isPalindrome(s, start + 1, end - 1);
}

int main() {
    char str[] = "madam";
    if(isPalindrome(str, 0, strlen(str)-1))
        printf("%s is palindrome\n", str);
    else
        printf("%s is not palindrome\n", str);
    return 0;
}
