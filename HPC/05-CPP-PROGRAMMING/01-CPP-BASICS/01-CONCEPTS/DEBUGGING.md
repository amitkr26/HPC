# Day 1 - Debugging: common mistakes

## Mistake 1: missing `#include <iostream>`

```cpp
using namespace std;

int main()
{
    cout << "Hi" << endl;   // ERROR: cout not declared
    return 0;
}
```

Fix: add `#include <iostream>` at the top.

## Mistake 2: forgetting the namespace

```cpp
#include <iostream>

int main()
{
    cout << "Hi" << endl;   // ERROR: cout not in global namespace
    return 0;
}
```

Fix: add `using namespace std;`, or write `std::cout` / `std::endl`.

## Mistake 3: wrong operator for cout/cin

```cpp
int x = 5;
cin << x;      // WRONG: << is output
cout >> x;     // WRONG: >> is input

cin >> x;      // RIGHT
cout << x;     // RIGHT
```

## Mistake 4: `endl` written as `end`

```cpp
cout << "Hi" end;   // ERROR: 'end' was not declared
```

Fix: it is `endl` (el-en-dee-el).

## Mistake 5: missing `;` or `<<` between values

```cpp
cout << "Value: " num << endl;   // ERROR: missing << before num
```

Fix: every piece needs its own `<<`.

## Mistake 6: using printf-style thinking

```cpp
printf("Sum = %d", sum);   // works only with <stdio.h>, not idiomatic C++
```

C++ way: `cout << "Sum = " << sum << endl;` (no format specifiers).

## Find-the-error drills

1.

```cpp
#include <iostream>
using namespace std;
int main()
{
    cout "Hello" << endl;
    return 0;
}
```

2.

```cpp
#include <iostream>
using namespace std;
int main()
{
    int num;
    cin >> num;
    cout << "You typed " << num
    return 0;
}
```

3.

```cpp
#include <iostream>
using namespace std;
int main()
{
    cout << "A" << endl << "B" << end;
    return 0;
}
```

4.

```cpp
#include <iostream>
int main()
{
    std::cout << "ok" << std::endl;
    return 0;
}
```
(Is this one correct? Yes - fully qualified names work without `using`.)