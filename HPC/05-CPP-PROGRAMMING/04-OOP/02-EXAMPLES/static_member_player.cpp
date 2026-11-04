#include <iostream>
using namespace std;

class Player {
public:
    static int playerCount;

    Player() {
        playerCount++;
    }

    ~Player() {
        playerCount--;
    }

    static int getPlayerCount() {
        return playerCount;
    }
};

int Player::playerCount = 0;

int main() {
    Player p1;
    Player p2;

    cout << "Number of players: "
         << Player::getPlayerCount() << endl;

    Player* p3 = new Player();

    cout << "Number of players: "
         << Player::playerCount << endl;

    delete p3;

    cout << "Number of players: "
         << Player::getPlayerCount() << endl;

    return 0;
}