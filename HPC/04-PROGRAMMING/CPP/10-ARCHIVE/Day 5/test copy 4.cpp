#include <iostream>
using namespace std;

class Distance
{
private:
    int feet;
    int inches;

public:
    friend istream &operator>>(istream &input, Distance &d);
    friend ostream &operator<<(ostream &output, Distance &d);
    Distance operator+(Distance d)
    {
        Distance temp;
        temp.feet = this->feet + d.feet;
        temp.inches = this->inches + d.inches;
        if (temp.inches > 11)
        {
            temp.feet++;
            temp.inches -= 12;
        }
        return temp;
    }

    bool operator>(Distance d) {
    if (this->feet > d.feet)
    {return true;}
    if (this->feet == d.feet && this->inches > d.inches)
    {return true;}
    return false;}
};
istream &operator>>(istream &input, Distance &d)
{
    cout << "Enter feet and inches: ";
    input >> d.feet >> d.inches;
    return input;
}

ostream &operator<<(ostream &output, Distance &d)
{
    output << d.feet << " feet " << d.inches << " inches " <<endl;
    return output;
}
int main()
{
    Distance d1, d2, d3;
    cin >> d1;
    cin >> d2;
    d3 = d1 + d2;
    cout << d3;

    if (d1 > d2)
    {
        cout << "d1 is greater";
    }
    else
    {
        cout << "d2 is greater";
    }
    return 0;
}