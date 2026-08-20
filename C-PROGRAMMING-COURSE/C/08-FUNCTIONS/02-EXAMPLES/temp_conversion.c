#include <stdio.h>

float celsiusToFahrenheit(float c) {
    return (c * 9.0 / 5.0) + 32;
}

float fahrenheitToCelsius(float f) {
    return (f - 32) * 5.0 / 9.0;
}

int main() {
    printf("100C = %.1fF\n", celsiusToFahrenheit(100));
    printf("212F = %.1fC\n", fahrenheitToCelsius(212));
    return 0;
}
