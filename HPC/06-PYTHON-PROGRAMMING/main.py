# Importing ONLY specific functions from math_tools
from math_tools import add, multiply

def main():
    print("--- Running main.py ---")
    
    num1, num2 = 10, 5
    
    # Using the imported functions
    sum_result = add(num1, num2)
    prod_result = multiply(num1, num2)
    
    print(f"Addition ({num1} + {num2}) = {sum_result}")
    print(f"Multiplication ({num1} * {num2}) = {prod_result}")

if __name__ == '__main__':
    main()