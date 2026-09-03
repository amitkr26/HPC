#include <iostream>
 namespace Project::Graphics{
    void draw(){
        std::cout<<"Drawing Graphics."<<std::endl;
    }
 }
 namespace Project::Audio{
    void play(){
        std::cout<<"Playing audio."<<std::endl;
    }
 }
int main() {
    Project::Graphics::draw();
    Project::Audio::play();

    return 0;
}