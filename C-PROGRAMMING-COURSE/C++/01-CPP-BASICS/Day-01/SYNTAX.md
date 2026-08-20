# Day 1 - Syntax: iostream basics

## Minimum program

```cpp
#include <iostream>
using namespace std;

int main()
{
    return 0;
}
```

## Output with cout

```cpp
#include <iostream>
using namespace std;

int main()
{
    cout << "Hello World" << endl;
    cout << "C++ is fun" << endl;
    cout << "Sum = " << 10 + 5 << endl;
    return 0;
}
```

## Input with cin

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

## Rules / gotchas

- Always `#include <iostream>` before using `cout`/`cin`.
- `using namespace std;` goes after the includes, before `main`.
- `<<` pushes data **into cout** (output).
- `>>` pulls data **out of cin** into a variable (input).
- No `&` needed with `cin >>` (unlike `scanf`).
- Chain as many `<<` pieces as you like.
- End lines with `endl` or `"\n"`.
- Every statement ends with `;`.