#include <stdio.h>

int linearSearch(int arr[], int n, int key, int i) {
    if(i >= n) return -1;
    if(arr[i] == key) return i;
    return linearSearch(arr, n, key, i + 1);
}

int main() {
    int arr[] = {10, 20, 30, 40, 50};
    int n = 5;
    int key = 30;
    int result = linearSearch(arr, n, key, 0);
    if(result != -1)
        printf("Found %d at index %d\n", key, result);
    else
        printf("%d not found\n", key);
    return 0;
}
