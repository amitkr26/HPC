# Syntax: Structures and Unions

## Declaration
```c
struct tag {
    type member1;
    type member2;
};
```

## Variable Creation
```c
struct tag var1;              // declaration
struct tag var2 = {val1, val2}; // initialization
```

## Member Access
```c
var.member = value;           // dot operator
ptr->member = value;          // arrow operator (pointer)
```

## Array of Structures
```c
struct tag arr[N];
arr[i].member = value;
```

## Function with Structure
```c
void func(struct tag s) {         // by value
    s.member = value;             // changes copy only
}
void funcPtr(struct tag *s) {     // by reference
    s->member = value;            // changes original
}
```

## typedef
```c
typedef struct tag Alias;
Alias var1;
```

## Union
```c
union tag {
    type member1;
    type member2;
};
```

## Enum
```c
enum Color { RED, GREEN, BLUE };
enum Color c = RED;
```
