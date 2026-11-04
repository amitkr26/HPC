#include <iostream>
using namespace std;

int main() {
    int N;
    cout << "Enter number of students in the class: ";
    cin >> N;

    if(N <= 0) {
        cout << "Invalid number: ";
        return 1;
    }

    float* grades = new float[N];

    for (int i = 0; i < N; i++) {
        cout << "Enter grade " << (i + 1) << ": ";
        cin >> grades[i];
    }

    cout << "\nAll grades entered:" << endl;
    for (int i = 0; i < N; i++) {
        cout << "Grade " << (i + 1) << ": " << grades[i] << endl;
    }

    float highest = grades[0];
    for (int i = 1; i < N; i++) {
        if (grades[i] > highest) {
            highest = grades[i];
        }
    }

    cout << "\nHighest grade: " << highest << endl;

    delete[] grades;
    return 0;
}