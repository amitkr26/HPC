# MCQ: Functions

1. What is a function prototype?
   - A) The function body
   - B) A declaration that tells compiler about function
   - C) A function call
   - D) A variable declaration

2. What does a void function return?
   - A) 0
   - B) NULL
   - C) Nothing
   - D) undefined

3. In call by value, what is passed to the function?
   - A) Address of variable
   - B) Copy of the value
   - C) The variable itself
   - D) Nothing

4. What is the output of:
   ```c
   void change(int x) { x = 100; }
   int main() { int a=5; change(a); printf("%d",a); }
   ```
   - A) 100
   - B) 5
   - C) 0
   - D) Error

5. What is recursion?
   - A) Function calling another function
   - B) Function calling itself
   - C) Loop inside function
   - D) Nested functions

6. Which is the base case in factorial?
   - A) return n * factorial(n-1)
   - B) if(n<=1) return 1
   - C) factorial(0)
   - D) return 0

7. What is a static variable in a function?
   - A) Variable that resets each call
   - B) Variable that retains value between calls
   - C) Global variable
   - D) Constant variable

8. What happens if a non-void function doesn't return a value?
   - A) Returns 0
   - B) Undefined behavior
   - C) Returns NULL
   - D) Compilation error

9. Which storage class has the longest lifetime?
   - A) auto
   - B) register
   - C) static
   - D) All same

10. What is the correct function call for: int add(int, int)?
    - A) add[5,3]
    - B) add(5,3)
    - C) add{5,3}
    - D) add<5,3>

### Answers
1-B, 2-C, 3-B, 4-B, 5-B, 6-B, 7-B, 8-B, 9-C, 10-B
