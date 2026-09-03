# MCQ: Structures

1. Which keyword is used to declare a structure?
   - A) class
   - B) struct
   - C) union
   - D) type

2. Which operator accesses structure members?
   - A) ->
   - B) .
   - C) *
   - D) ::

3. Which operator accesses members via pointer?
   - A) .
   - B) *
   - C) ->
   - D) ::

4. What is the size of a struct with int (4) + char (1)?
   - A) 5
   - B) 8 (with padding)
   - C) 4
   - D) 1

5. Can a structure contain another structure?
   - A) No
   - B) Yes (nested)
   - C) Only in C++
   - D) Only with typedef

6. What is typedef with struct used for?
   - A) Create struct
   - B) Create alias name
   - C) Delete struct
   - D) Copy struct

7. How do you initialize a struct variable?
   - A) struct S s = {1, "Amit"};
   - B) S s(1, "Amit");
   - C) S s = new(1, "Amit");
   - D) struct s = {1, "Amit"};

8. What is a union?
   - A) Members share memory
   - B) Members have separate memory
   - C) Like struct
   - D) Array of structs

9. Size of union is:
   - A) Sum of all members
   - B) Size of largest member
   - C) Size of smallest member
   - D) Always 4 bytes

10. What is the output of struct assignment?
    ```c
    struct S a = {1, 2};
    struct S b = a;
    printf("%d", b.a);
    ```
    - A) 0
    - B) 1
    - C) 2
    - D) Error

### Answers
1-B, 2-B, 3-C, 4-B, 5-B, 6-B, 7-A, 8-A, 9-B, 10-B
