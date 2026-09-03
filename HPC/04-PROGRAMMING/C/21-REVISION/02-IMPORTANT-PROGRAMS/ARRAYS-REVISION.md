# Arrays Revision

Revision pack: 10 quick + 10 output + 10 find-the-error + 10 coding + 10 MCQ
+ 5 viva + 1 mini project. Many items come from the Day-3 assignment
(`C/Assignmenmt/Amit_Kumar_Lab3_Day3_Assignment.docx`) - reuse, don't recreate.

## 10 quick questions

1. What is the first index of an array? (0)
2. Write the syntax to declare an array of 50 integers. (`int a[50];`)
3. How do you find the number of elements? (`sizeof(a)/sizeof(a[0])`)
4. What is stored in `a[4]` if `int a[5]={1,2,3};`? (0 - partial init zero-fills)
5. What does an uninitialized local array contain? (garbage)
6. Name two things insertion must do. (shift right, then place value, then n++)
7. In which direction does deletion shift elements? (left)
8. What does linear search return? (index of first match, or "not found")
9. What is the last valid index of `int a[10];`? (9)
10. Is `a[10]` for `int a[10]` valid? (No - out of bounds, undefined behaviour)

## 10 output questions

1. `int a[]={10,20,30,40};` print `a[1], a[3]` -> `20 40`
2. `int a[2][2]={{1,2},{3,4}};` print `a[0][1], a[1][0]` -> `2 3`
3. 3D `a[2][2][2]={{...}}` print `a[0][1][1], a[1][0][0]` -> `4 5`
4. `int a[]={10,20,30,40,50};` reverse loop `i=4..0` -> `50 40 30 20 10`
5. `int a[4]={5,10,15,20}; sum+=a[i]; break at i==2` -> `30`
6. `int a[]={2,4,6,8,10};` print only when `i%2==0` -> `2 6 10`
7. `int a[]={1,2,3,4,5};` double each element, print `a[3]` -> `8`
8. `int a[5]={1,2,3};` print `a[4]` -> `0`
9. `int a[3][3]={{1,2},{3},{4,5,6}};` print `a[0][2], a[1][1], a[1][2]` -> `0 0 0`
10. `int arr[2][2][2]={1..8};` print `arr[1][0][1]` -> `6`

## 10 find-the-error questions

1. `int a[3]={10,20,30}; printf("%d", a[3]);` (out of bounds, valid is a[2])
2. `for(i=0;i<=5;i++) scanf("%d",&a[i]);` (i=5 out of bounds, use `<5`)
3. `for(i=n;i>=0;i--) printf(...);` (reads a[n], start at n-1)
4. `int n=5; int a[n]={1,2,3,4,5};` (cannot size by a runtime variable AND
   init together - only VLA without init, or use a constant)
5. `scanf("%d", a[i]);` (missing `&`)
6. Insert loop shifting left instead of right.
7. Delete loop never reducing `n`.
8. `if(a[i]=value)` in a search (assignment, not comparison).
9. `printf("%d", a[5]);` where `int a[5];` (out of bounds).
10. Using `sizeof(a)` after passing `a` to a function (decayed pointer).

## 10 coding problems

1. Sum and average of N numbers.
2. Smallest element.
3. Second largest element.
4. Count positive/negative/zero.
5. Reverse array in place (swap ends).
6. Insert at index, delete by index - both from scratch.
7. Check two arrays are identical (write it, then compare with Day-3 q08).
8. Replace all negatives with 0 (compare with Day-3 q10).
9. Count even/odd (compare with `count_even_odd_array.c`).
10. Print a 2D matrix and its transpose.

## 10 MCQs (answers: 1-b 2-c 3-b 4-c 5-b 6-b 7-b 8-b 9-b 10-b)

1. `int arr[5]={1,2,3}; printf("%d",arr[4]);` a)garbage b)3 c)0 d)error -> c
2. Element count of `arr`? a)length(arr) b)arr.length c)`sizeof(arr)/sizeof(arr[0])` d)count(arr) -> c
3. `int arr[3][2]={{1,2},{3,4},{5,6}}; arr[2][1]` a)5 b)6 c)4 d)2 -> b
4. Uninitialized local arrays contain a)0 b)1 c)garbage d)NULL -> c
5. `int arr[]={10,20,30,40,50}; for(i=4;i>=0;i--)` a)10..50 b)50..10 c)error d)40..0 -> b
6. Correct deletion at index 2 -> b (shift-left + size--)
7. `int arr[4]={5,10,15,20}; sum, break at i==2` a)50 b)30 c)15 d)45 -> b
8. Partially filled 2D `arr[0][2],arr[1][1],arr[1][2]` -> b (0 0 0)
9. `arr[i]=arr[4-i]` loop, print arr[0],arr[2],arr[4] -> b (5 3 5)
10. 3D `arr[1][0][1]` in `{1..8}` -> b (6)

## 5 viva questions

1. Differentiate compile-time vs run-time array initialization (Lab-3 Explain 1).
2. How is array length found without a built-in function? (Lab-3 Explain 2)
3. Explain 2D array memory storage and the address formula (Lab-3 Explain 3).
4. What happens on out-of-bounds access? (Lab-3 Explain 6)
5. Why does an insertion shift right but deletion shift left?

## 1 mini project

**Student Marks Manager** (arrays only, no structs/functions yet): menu to
(a) add N students' marks in 5 subjects, (b) show all with total + average +
grade, (c) search a student by roll number, (d) statistics (highest, lowest,
pass/fail count). Starting version: `16-MINI-PROJECTS/code/02_student_marks_manager.c`.
