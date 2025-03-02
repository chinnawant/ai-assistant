#!/usr/bin/env python3
"""
This script demonstrates how to run a Langflow CustomComponent directly from the terminal.
It imports the Calculator component and uses it without needing the Langflow UI.
"""

import sys
import os
from typing import Dict, Any

from custom_component.calculator.Calculator import Calculator

# Ensure the custom_components directory is in the Python path
# Adjust this path to the location of your custom_components directory
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import the Calculator component
def display_menu():
    """Display the calculator menu options"""
    print("\n===== Langflow Calculator =====")
    print("1. Addition")
    print("2. Subtraction")
    print("3. Multiplication")
    print("4. Division")
    print("5. Power")
    print("6. Square Root")
    print("7. Sine")
    print("8. Cosine")
    print("9. Tangent")
    print("10. Logarithm")
    print("11. Custom Expression")
    print("12. Exit")
    return input("Enter your choice (1-12): ")

def get_number(prompt: str) -> float:
    """Get a number input from the user"""
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_custom_expression() -> str:
    """Get a custom expression from the user"""
    print("\nUse 'x' for the first number and 'y' for the second number.")
    print("Example: x * y + 10")
    return input("Enter your expression: ")

def calculate(calculator: Calculator, operation: str, num1: float, num2: float = 0, custom_expr: str = "") -> Dict[str, Any]:
    """Perform the calculation using the Calculator component"""
    return calculator.build(operation, num1, num2, custom_expr)

def main():
    """Main function to run the calculator"""
    # Initialize the Calculator component
    calculator = Calculator()

    while True:
        choice = display_menu()

        if choice == "12":
            print("Exiting calculator. Goodbye!")
            break

        operation_map = {
            "1": "add",
            "2": "subtract",
            "3": "multiply",
            "4": "divide",
            "5": "power",
            "6": "sqrt",
            "7": "sin",
            "8": "cos",
            "9": "tan",
            "10": "log",
            "11": "custom"
        }

        if choice not in operation_map:
            print("Invalid choice. Please try again.")
            continue

        operation = operation_map[choice]

        # Operations that need only one number
        single_operand_operations = ["sqrt", "sin", "cos", "tan"]

        num1 = get_number("Enter the first number: ")

        num2 = 0
        custom_expr = ""

        if operation not in single_operand_operations:
            if operation == "custom":
                custom_expr = get_custom_expression()
                num2 = get_number("Enter the second number: ")
            else:
                num2 = get_number("Enter the second number: ")

        # Perform the calculation
        result = calculate(calculator, operation, num1, num2, custom_expr)

        # Display the result
        print(f"\nResult: {result['result']}")
        input("Press Enter to continue...")

if __name__ == "__main__":
    main()