#include <iostream>
using namespace std;

class Animal
{
public:
    virtual void makeSound()
    {
        cout << "Animal Sound: " << endl;
    }
};

class Dog : public Animal
{
public:
    void makeSound() override
    {
        cout << "barks" << endl;
    }
};

class Cat : public Animal
{
public:
    void makeSound() override
    {
        cout << "meow" << endl;
    }
};

int main()
{
    Animal *a1;

    Dog d;
    a1 = &d;
    a1->makeSound();

    Cat c;
    a1 = &c;
    a1->makeSound();

    return 0;
}