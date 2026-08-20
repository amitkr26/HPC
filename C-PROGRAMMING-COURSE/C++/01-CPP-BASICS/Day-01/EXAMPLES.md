# Day 1 - Examples with dry runs

## Example 1: Hello World

```cpp
#include <iostream>
using namespace std;

int main()
{
    cout << "Hello World" << endl;
    return 0;
}
```

**Dry run:** `cout` prints `Hello World`, `endl` moves to a new line, `main`
returns 0.

Output:
```
Hello World
```

## Example 2: print_variables.cpp

```cpp
#include <iostream>
using namespace std;

int main()
{
    int age = 20;
    float marks = 85.5;
    char grade = 'A';

    cout << "Age: " << age << endl;
    cout << "Marks: " << marks << endl;
    cout << "Grade: " << grade << endl;
    return 0;
}
```

**Dry run:** no format specifiers - `cout` prints each variable's value in
sequence.

Output:
```
Age: 20
Marks: 85.5
Grade: A
```

## Example 3: input_output.cpp

```cpp
#include <iostream>
using namespace std;

int main()
{
    int num;
    cout << "Enter a number: ";
    cin >> num;
    cout << "You entered: " << num << endl;
    return 0;
}
```

**Dry run (user types 7):**
1. `cout` prints `Enter a number: `
2. `cin` waits for input, stores 7 in `num`
3. `cout` prints `You entered: 7`

Output:
```
Enter a number: 7
You entered: 7
```

## Example 4: add_two_numbers.cpp

```cpp
#include <iostream>
using namespace std;

int main()
{
    int a, b, sum;
    cout << "Enter two numbers: ";
    cin >> a >> b;
    sum = a + b;
    cout << "Sum = " << sum << endl;
    return 0;
}
```

**Dry run (user types 4 9):** `cin >> a >> b` reads 4 into `a` and 9 into
`b`; `sum = 13`; output prints `Sum = 13`.

Output:
```
Enter two numbers: 4 9
Sum = 13
```

## C vs C++ side by side

| Step | C | C++ |
| --- | --- | --- |
| Header | `#include <stdio.h>` | `#include <iostream>` |
| Output | `printf("Sum = %d\n", sum);` | `cout << "Sum = " << sum << endl;` |
| Input | `scanf("%d %d", &a, &b);` | `cin >> a >> b;` |