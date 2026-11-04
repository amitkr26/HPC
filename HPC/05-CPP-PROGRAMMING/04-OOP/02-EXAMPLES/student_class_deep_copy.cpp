#include <iostream>
using namespace std;

class student {
    private:
        int rollNo;
        int *marks;
        int numSubjects;

    public:
        student(int r, int n) {
            rollNo = r;
            numSubjects = n;
            marks = new int[n];
            for (int i = 0; i < n; i++) {
                marks[i] = 0;
            }
        }

        student(const student &s) {
            rollNo = s.rollNo;
            numSubjects = s.numSubjects;
            marks = new int[numSubjects];
            for (int i = 0; i < numSubjects; i++) {
                marks[i] = s.marks[i];
            }
        }

        ~student() {
            delete[] marks;
        }

        void setMarks(int index, int value) {
            if (index >= 0 && index < numSubjects) {
                marks[index] = value;
            }
        }

        int getMarks(int index) const {
            if (index >= 0 && index < numSubjects) {
                return marks[index];
            }
            return 0;
        }

        void display() const {
            cout << "Roll No: " << rollNo << endl;
            cout << "Marks (" << numSubjects << " subjects):" << endl;
            for (int i = 0; i < numSubjects; i++) {
                cout << "  Subject " << (i + 1) << ": " << marks[i] << endl;
            }
            cout << "  Marks array address: " << (void*)marks << endl;
        }
};

int main() {
    student s1(101, 4);
    s1.setMarks(0, 85);
    s1.setMarks(1, 92);
    s1.setMarks(2, 78);
    s1.setMarks(3, 90);

    student s2 = s1;

    cout << "Student 1:" << endl;
    s1.display();

    cout << "\nStudent 2 (copy):" << endl;
    s2.display();

    s1.setMarks(1, 100);

    cout << "\nAfter modifying Student 1's mark 1 to 100:" << endl;
    cout << "Student 1 mark 1: " << s1.getMarks(1) << endl;
    cout << "Student 2 mark 1 (should be unchanged 92): " << s2.getMarks(1) << endl;

    return 0;
}