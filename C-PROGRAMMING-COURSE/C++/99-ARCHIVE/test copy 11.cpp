#include <iostream>
using namespace std;

class MyClass {
private:
    int private_data;
public:
    MyClass():private_data(10) {}
    friend void friendFunction(MyClass &obj);
    friend class FriendClass;

};

void friendFunction(MyClass &obj){
    cout << "Frined function can access private data: " << obj.private_data << endl;
}

class FriendClass{
    public:
    void accessPrivateData(MyClass &obj){
        cout << "friend class can access provate data: " << obj.private_data << endl;
}
};


int main() {
    MyClass obj;
    friendFunction(obj);

    FriendClass friendObj;
    friendObj.accessPrivateData(obj);

    return 0;
}