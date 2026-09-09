# Debugging: Structures

## Common Errors

### 1. Comparing structures directly
```c
struct S a = {1, 2};
struct S b = a;
if(a == b) { }  // Error! Can't compare structs
```
**Fix:** Compare member by member: `if(a.x == b.x && a.y == b.y)`

### 2. Assigning strings directly
```c
struct S s;
s.name = "Amit";  // Error! Can't assign string to array
```
**Fix:** Use strcpy: `strcpy(s.name, "Amit");`

### 3. Forgetting struct keyword
```c
Student s1;  // Error!
struct Student s1;  // Correct
```

### 4. Arrow operator on non-pointer
```c
struct S s;
s->x = 10;  // Error! s is not a pointer
```
**Fix:** `s.x = 10;` or use pointer: `struct S *ptr = &s; ptr->x = 10;`

### 5. Passing large structures by value
```c
void func(struct Large s) {  // Copies entire struct (slow)
}
```
**Fix:** Pass by pointer: `void func(struct Large *s)`

### 6. Array of structures initialization
```c
struct S arr[3];
arr[0].x = 1;  // OK
arr[3].x = 1;  // Out of bounds!
```

## Debugging Tips
- Print each member separately
- Check struct size with sizeof
- Verify memory layout with padding
- Use -> for pointers, . for direct access
