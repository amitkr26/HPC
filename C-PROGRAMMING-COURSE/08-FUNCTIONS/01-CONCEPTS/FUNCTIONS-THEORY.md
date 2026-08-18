# Theory: Functions

## What is a Function?
A function is a reusable block of code that performs a specific task.
Functions help in:
- Code reusability
- Modularity
- Easy debugging
- Code organization

## Function Structure
```c
return_type function_name(parameter_list) {
    // body
    return value;
}
```

## Function Declaration (Prototype)
Tells the compiler about the function before it is used:
```c
int add(int a, int b);  // prototype
```

## Function Definition
The actual implementation:
```c
int add(int a, int b) {
    return a + b;
}
```

## Function Call
```c
int result = add(5, 3);  // result = 8
```

## Parameters vs Arguments
- **Parameters** are in the function definition: `int add(int a, int b)`
- **Arguments** are in the function call: `add(5, 3)`

## Return Types
```c
int func(void)     // returns int
void func(void)    // returns nothing
float func(int x)  // returns float
char func(...)     // returns char
```

## Call by Value
A copy of the argument is passed:
```c
void change(int x) {
    x = 100;  // only changes local copy
}
int main() {
    int a = 5;
    change(a);
    printf("%d", a);  // still 5
}
```

## Call by Reference
The address is passed (using pointers):
```c
void change(int *x) {
    *x = 100;  // changes original variable
}
int main() {
    int a = 5;
    change(&a);
    printf("%d", a);  // now 100
}
```

## Recursion
A function that calls itself:
```c
int factorial(int n) {
    if(n <= 1) return 1;
    return n * factorial(n-1);
}
```

## Storage Classes
| Class | Default | Scope | Lifetime | Storage |
|-------|---------|-------|----------|---------|
| auto | Yes | Local | Function | Stack |
| static | No | Local | Program | Static memory |
| extern | No | Global | Program | Data segment |
| register | No | Local | Function | CPU register |
