# Array Practice - Levels 1 to 6

Work in order. Do not skip levels. After each level, update confidence in
`02-PROGRESS.md`.

## Level 1 - Basic (understand the syntax)

1. Declare `int marks[5]` and initialize it with `{10,20,30,40,50}`. Print
   every element.
2. Read 3 numbers into an array and print them in the order entered.
3. Print the first and last element of an array of size 5.
4. Fix the type/specifier: print `double` values with the right format.
5. Write the `sizeof` length formula for an array `int a[7]` and print the
   result. Expected: 7.

## Level 2 - Logic (reasoning)

1. Given `int a[5]={1,2,3,4,5};` and `int b[5]={5,4,3,2,1};`, what is printed
   by `a[2]+b[3]`? Answer: 3+2 = 5.
2. An array has 10 elements. What is the valid index range? What happens if
   the code uses index 10?
3. `int x[4]; for(i=0;i<=4;i++) scanf("%d",&x[i]);` - what is wrong and what
   can happen at runtime?
4. Trace `int a[4]={2,4,6,8}; for(i=0;i<4;i++) a[i]+=a[i];` - what is `a[2]`
   at the end? Answer: 12.
5. Which loop prints the array backwards? Write it for `int a[5]={1,2,3,4,5};`.

## Level 3 - Coding (complete C programs)

1. Read N numbers, print their sum and average.
2. Find the smallest element (this is the missing topic - do it yourself).
3. Count how many elements are above the average.
4. Swap the 2nd and 4th element of an array.
5. Check whether an array is sorted ascending (print Yes/No).
6. Print all even values from an array.
7. Remove a value at a given position (not by value - by index).
8. Read two arrays of equal size and print the element-wise sum.

## Level 4 - Debugging (find and fix)

1. `for(i=0;i<=n;i++) printf("%d",arr[i]);` - boundary bug. Fix.
2. Reverse loop `for(i=n;i>=0;i--)` - reads `arr[n]`. Fix.
3. Insert code that shifts `i` from `n` down to `position` but uses
   `arr[i-1]=arr[i]` (wrong direction). Fix and explain.
4. Delete code that shifts with `i<position` instead of `i<n-1`. Fix.
5. `int arr[3]; arr[0]=1; arr[1]=2; arr[2]=3; printf("%d",arr[3]);` - what
   prints and why is it wrong?
6. Search code that prints "not found" even when found (missing flag). Fix.

## Level 5 - Interview / Viva

1. What is the difference between `sizeof(arr)` on an array vs inside a
   function that receives it? (decay to pointer)
2. Why does C not check array bounds? What is the consequence?
3. Explain insertion vs deletion - why does insertion shift right and deletion
   shift left?
4. What does "garbage value" mean for an uninitialized array?
5. How is a 2D array stored in memory? Give the address formula for `a[i][j]`.
6. When is linear search better than binary search? (You have not learned
   binary search yet - answer about linear search only.)
7. What is the role of `break` in linear search?

## Level 6 - Challenge (multiple concepts)

1. Shift an array left by k positions (a real rotation, no printing trick).
2. Remove all duplicates from an array and print the unique elements.
3. Given marks of N students in 5 subjects (2D array), print each student's
   total, average, and grade (use the Day-2 grade ladder).
4. Merge two sorted arrays into one sorted array.
5. Write a menu-driven "Student Marks Manager" (add marks, show all, search by
   roll number) using only arrays, loops, and switch - no structs, no functions
   yet (those come later). A starting version is in `16-MINI-PROJECTS/`.
