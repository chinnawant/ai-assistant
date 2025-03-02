from typing import Any, Sequence, Dict, Optional, List
import operator
from functools import reduce

from langchain_core.tools import Tool
from loguru import logger

from langflow.base.langchain_utilities.model import LCToolComponent
from langflow.inputs import DropdownInput, IntInput, FloatInput, BoolInput


class CalculatorComponent(LCToolComponent):
    display_name: str = "Calculator Tools"
    description: str = "Use Calculator tools to perform mathematical operations with your agent"
    name = "CalculatorTools"
    icon = "Calculator"
    documentation: str = "https://docs.langflow.org"

    inputs = [
        DropdownInput(
            name="operations",
            display_name="Operations",
            options=["add", "subtract", "multiply", "divide", "power", "sqrt", "all"],
            value="all",
            info="The mathematical operations to make available",
        ),
        FloatInput(
            name="precision",
            display_name="Decimal Precision",
            value=2,
            info="Number of decimal places for rounding results",
        ),
        BoolInput(
            name="scientific_notation",
            display_name="Scientific Notation",
            value=False,
            info="Display large numbers in scientific notation",
        ),
        IntInput(
            name="max_value",
            display_name="Maximum Value",
            value=1000000,
            info="Maximum allowed value for calculation results",
            advanced=True,
        ),
    ]

    def _add_numbers(self, numbers: List[float]) -> float:
        """Add a list of numbers together."""
        return sum(numbers)

    def _subtract_numbers(self, numbers: List[float]) -> float:
        """Subtract all numbers from the first number."""
        if not numbers:
            return 0
        return reduce(lambda x, y: x - y, numbers)

    def _multiply_numbers(self, numbers: List[float]) -> float:
        """Multiply a list of numbers together."""
        if not numbers:
            return 0
        return reduce(operator.mul, numbers, 1)

    def _divide_numbers(self, numbers: List[float]) -> float:
        """Divide the first number by all subsequent numbers."""
        if not numbers:
            return 0
        if any(x == 0 for x in numbers[1:]):
            raise ValueError("Cannot divide by zero")
        return reduce(lambda x, y: x / y, numbers)

    def _power(self, base: float, exponent: float) -> float:
        """Raise a number to the power of another number."""
        return base ** exponent

    def _sqrt(self, number: float) -> float:
        """Calculate the square root of a number."""
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return number ** 0.5

    def _format_result(self, result: float) -> str:
        """Format the calculation result based on component settings."""
        # Check if result exceeds max value
        if abs(result) > self.max_value:
            raise ValueError(f"Result exceeds maximum allowed value of {self.max_value}")

        # Round to specified precision
        rounded_result = round(result, int(self.precision))

        # Format using scientific notation if required
        if self.scientific_notation and (abs(rounded_result) >= 1000 or (0 < abs(rounded_result) < 0.001)):
            return f"{rounded_result:.{int(self.precision)}e}"
        else:
            return str(rounded_result)

    def build_tool(self) -> Sequence[Tool]:
        """Build and return calculator tools based on selected operations."""
        tools = []

        if self.operations in ["add", "all"]:
            tools.append(
                Tool(
                    name="Calculator_Add",
                    description="Add multiple numbers together. Input should be a comma-separated list of numbers.",
                    func=lambda input_str: self._format_result(
                        self._add_numbers([float(x.strip()) for x in input_str.split(",")])
                    ),
                )
            )

        if self.operations in ["subtract", "all"]:
            tools.append(
                Tool(
                    name="Calculator_Subtract",
                    description="Subtract subsequent numbers from the first number. Input should be a comma-separated list of numbers.",
                    func=lambda input_str: self._format_result(
                        self._subtract_numbers([float(x.strip()) for x in input_str.split(",")])
                    ),
                )
            )

        if self.operations in ["multiply", "all"]:
            tools.append(
                Tool(
                    name="Calculator_Multiply",
                    description="Multiply multiple numbers together. Input should be a comma-separated list of numbers.",
                    func=lambda input_str: self._format_result(
                        self._multiply_numbers([float(x.strip()) for x in input_str.split(",")])
                    ),
                )
            )

        if self.operations in ["divide", "all"]:
            tools.append(
                Tool(
                    name="Calculator_Divide",
                    description="Divide the first number by all subsequent numbers. Input should be a comma-separated list of numbers.",
                    func=lambda input_str: self._format_result(
                        self._divide_numbers([float(x.strip()) for x in input_str.split(",")])
                    ),
                )
            )

        if self.operations in ["power", "all"]:
            tools.append(
                Tool(
                    name="Calculator_Power",
                    description="Raise a number to the power of another number. Input should be two numbers separated by comma: base,exponent.",
                    func=lambda input_str: self._format_result(
                        self._power(*[float(x.strip()) for x in input_str.split(",", 1)])
                    ),
                )
            )

        if self.operations in ["sqrt", "all"]:
            tools.append(
                Tool(
                    name="Calculator_SquareRoot",
                    description="Calculate the square root of a number. Input should be a single number.",
                    func=lambda input_str: self._format_result(
                        self._sqrt(float(input_str.strip()))
                    ),
                )
            )

        return tools

    def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None) -> dict:
        """Update build configuration based on field changes."""
        # No dynamic updates needed for this simple component
        return build_config