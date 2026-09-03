#include <iostream>

namespace a_very_long_and_complex_namespace_name {
    void do_work() {
        std::cout << "Working in a very long namespace." << std::endl;
    }
}

int main() {
    namespace MyShortName = a_very_long_and_complex_namespace_name;

    MyShortName::do_work();

    return 0;
}