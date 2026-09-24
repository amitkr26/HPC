#include <iostream>
#include <thread>
#include <chrono>

void thread1_fn() {
    for (int i = 1; i <= 10; i++) {
        std::cout << "th1: " << i << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}

void thread2_fn() {
    for (int i = 1; i <= 10; i++) {
        std::cout << "th2: " << i << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}

int main() {
    std::thread th1(thread1_fn);
    std::thread th2(thread2_fn);

    for (int i = 1; i <= 10; i++) {
        std::cout << "main: " << i << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    th1.join();
    th2.join();

    return 0;
}
