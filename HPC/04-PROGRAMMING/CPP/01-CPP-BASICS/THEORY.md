# Day 1 - Theory: C++ Basics

## 1. What is C++?

C++ is C with added object-oriented programming (classes, objects,
inheritance) plus many conveniences (references, function overloading,
`iostream`, `std::string`, the STL). A valid C program is (mostly) a valid
C++ program - C++ is a superset.

## 2. Parts of a C++ program

```cpp
#include <iostream>        // 1. header: pulls in cout, cin
using namespace std;       // 2. lets us write cout instead of std::cout

int main()                 // 3. program entry point
{                          // 4. body: statements end with ;
    cout << "Hello!";      // 5. output statement
    return 0;              // 6. success code
}
```

1. `#include <iostream>` - the header that declares `cout` and `cin`.
2. `using namespace std;` - most C++ names (cout, cin, endl) live in the
   `std` namespace. This line lets us use them without the `std::` prefix.
3. `main()` - execution always starts here, like in C.
4. Statements end with `;` exactly like C.
5. `cout << value;` - the output stream. `<<` pushes data into it.
6. `return 0;` - 0 means success (same as C).

## 3. cout - output

`cout` writes to the console (standard output).

```cpp
cout << "Hello";          // print text
cout << 42;               // print a number
cout << "Age: " << 20;    // chain multiple pieces with <<
cout << endl;             // print a newline
```

Unlike `printf()`, there are **no format specifiers**. `cout` figures out the
type of each value automatically.

## 4. cin - input

`cin` reads from the console (standard input).

```cpp
int age;
cin >> age;               // read an int from the keyboard
```

`>>` is the extraction operator: it pulls data out of the input stream into
the variable. Like `scanf("%d", &age)` but **without the `&`** - C++
handles the address automatically.

## 5. endl - newline

`endl` prints a newline and flushes the output buffer. `"\n"` inside a string
also prints a newline (faster, no flush). Both are used in practice.

## 6. Variables

Variables in C++ look exactly like C:

```cpp
int a = 5;          // int
float f = 2.5;      // float
double d = 3.14;    // double
char c = 'A';       // char
```

One new C++ feature you will meet soon: you can declare a variable anywhere,
not just at the top of a block.

## 7. Compilation

C++ source files use the `.cpp` extension. Compile with `g++`:

```bash
C:\MinGW\bin\g++.exe hello_world.cpp -o hello_world.exe
hello_world.exe
```

Same idea as `gcc`, but the compiler knows C++.