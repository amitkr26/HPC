# Day 1 - Practice (Levels 1-6)

Work a level only after honestly passing the previous one.

## Level 1 - Basic (copy and run)

1. Run `hello_world.cpp` and confirm the output.
2. Modify the message to print your own name, compile, run.
3. Print your name, age, and city on three lines using `endl`.

## Level 2 - Logic

4. Write a program that reads two numbers and prints their **product**.
5. Write a program that reads a number and prints it twice on one line.
6. Write a program that reads three numbers and prints their **average**.

## Level 3 - Coding

7. Write a program that reads a radius and prints `Area = <value>` using
   `3.14159 * r * r` (like the C Day-1 program, but with `cout`).
8. Write a program that reads a number of seconds and prints
   `Minutes = ...` and `Remaining seconds = ...`.
9. Write a program that swaps two integers entered by the user and prints
   the values before and after the swap.

## Level 4 - Debugging

10. What is wrong here?

```cpp
#include <iostream>
using namespace std;
int main()
{
    cout << "Hello" end;
    return 0;
}
```

11. What is wrong here?

```cpp
#include <iostream>
using namespace std;
int main()
{
    int num;
    cin >> num;
    cout << "Value: " num << endl;
    return 0;
}
```

12. What is wrong here?

```cpp
#include <iostream>
int main()
{
    cout << "No namespace here" << endl;
    return 0;
}
```

## Level 5 - Interview / Viva

13. Why does `cin` not need `&` (unlike `scanf`)?
14. What does `using namespace std;` do? What happens without it?
15. What is the difference between `endl` and `"\n"`?
16. Which compiler command compiles a `.cpp` file?

## Level 6 - Challenge

17. Write a program that reads a 3-digit number and prints each digit on a
    separate line using `/` and `%` (no loops yet).
18. Write a program that reads a character and prints it 5 times separated by
    spaces using only one `cout` statement.