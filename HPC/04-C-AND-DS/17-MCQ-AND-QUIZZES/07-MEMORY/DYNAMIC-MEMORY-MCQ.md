# MCQ: Dynamic Memory

1. Which header is needed for malloc?
   - A) stdio.h
   - B) stdlib.h
   - C) string.h
   - D) math.h

2. What does malloc return if it fails?
   - A) 0
   - B) NULL
   - C) -1
   - D) Garbage

3. What is the difference between malloc and calloc?
   - A) No difference
   - B) calloc initializes to 0
   - C) malloc is faster
   - D) Both B and C

4. What does free() do?
   - A) Deletes variable
   - B) Returns memory to system
   - C) Sets pointer to NULL
   - D) Both B and C

5. What is a memory leak?
   - A) Memory not allocated
   - B) Forgetting to free allocated memory
   - C) Freeing twice
   - D) Using freed memory

6. What is the correct malloc for 10 ints?
   - A) malloc(10)
   - B) malloc(10 * sizeof(int))
   - C) malloc(sizeof(int))
   - D) malloc(10 * int)

7. What happens if you use a pointer after free?
   - A) Works fine
   - B) Undefined behavior (dangling pointer)
   - C) Compilation error
   - D) Returns NULL

8. What does realloc do?
   - A) Allocate new memory
   - B) Resize existing allocation
   - C) Free memory
   - D) Copy memory

9. Why set pointer to NULL after free?
   - A) Required by C
   - B) Prevents dangling pointer
   - C) Frees memory again
   - D) No reason

10. What is the size of a void pointer?
    - A) 0
    - B) Platform dependent (4 or 8 bytes)
    - C) 1 byte
    - D) Error

### Answers
1-B, 2-B, 3-D, 4-D, 5-B, 6-B, 7-B, 8-B, 9-B, 10-B
