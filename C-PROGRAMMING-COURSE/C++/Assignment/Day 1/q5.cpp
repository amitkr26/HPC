#include <iostream>
using namespace std;

class SpeakerVolume {
private:
    int level = 0;

public:
    void setLevel(int vol) {
        if (vol >= 0 && vol <= 100) {
            level = vol;
        }
        else {
            cout << "Error: Volume must be between 0 and 100." << endl;
        }
    }

    int getLevel() {
        return level;
    }
};

int main() {
    SpeakerVolume s;

    s.setLevel(123);
    cout << "Current level: " << s.getLevel() << endl;

    s.setLevel(23);
    cout << "Current level: " << s.getLevel() << endl;

    return 0;
}