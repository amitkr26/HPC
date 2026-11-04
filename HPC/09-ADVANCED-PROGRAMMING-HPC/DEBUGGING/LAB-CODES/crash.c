// Lab 2: segmentation fault (backtrace, frame, print, core dump)
#include <stdio.h>
#include <stddef.h>

int *sophisticated(int *p) { return NULL; }   // quietly returns NULL
int *complicated(int *p)   { return p; }

void crash(int *i) {
    *i = 1;                                    // segfault if i == NULL
}

void f(int *i) {
    int *j = i;
    j = sophisticated(j);
    j = complicated(j);
    crash(j);                                  // j == NULL here
}

int main() {
    int i;
    f(&i);
    return 0;
}
