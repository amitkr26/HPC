#include <iostream>
#include <unistd.h>
#include <pthread.h>
#include <cstring>

class Worker {
public:
    Worker(const std::string& name) : name_(name) {}

    void start() {
        int ret = pthread_create(&thread_, nullptr, &Worker::run, this);
        if (ret != 0)
            std::cerr << "failed to create " << name_ << ": " << std::strerror(ret) << std::endl;
    }

    void join() {
        pthread_join(thread_, nullptr);
    }

private:
    static void* run(void* param) {
        Worker* self = static_cast<Worker*>(param);
        self->loop();
        return nullptr;
    }

    void loop() {
        for (int i = 1; i <= 10; i++) {
            std::cout << name_ << ": " << i << std::endl;
            sleep(1);
        }
    }

    std::string name_;
    pthread_t thread_;
};

int main() {
    Worker w1("th1");
    Worker w2("th2");

    w1.start();
    w2.start();

    for (int i = 1; i <= 10; i++) {
        std::cout << "main: " << i << std::endl;
        sleep(1);
    }

    w1.join();
    w2.join();

    return 0;
}
