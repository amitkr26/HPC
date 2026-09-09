#include <stdio.h>

void reverseArray(int *arr, int n) {
    int *left = arr;
    int *right = arr + n - 1;
    while(left < right) {
        int temp = *left;
        *left = *right;
        *right = temp;
        left++;
        right--;
    }
}

int main() {
    int arr[] = {1, 2, 3, 4, 5};
    int n = 5, i;
    reverseArray(arr, n);
    for(i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\n");
    return 0;
}
