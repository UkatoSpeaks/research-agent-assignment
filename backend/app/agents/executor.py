import re
import time
from typing import Any

from app.schemas import PlanStep, ToolResult
from app.tools import (
    CalculatorTool,
    PageFetcherTool,
    WebSearchTool,
)


class ExecutorAgent:
    """Executes individual plan steps using the appropriate tool."""

    def __init__(self) -> None:
        self.tools = {
            "web_search": WebSearchTool(),
            "page_fetcher": PageFetcherTool(),
            "calculator": CalculatorTool(),
        }

    def execute_step(self, step: PlanStep) -> ToolResult:
        """Execute a single plan step."""

        start_time = time.perf_counter()

        try:
            tool = self.tools.get(step.tool)

            if tool is None:
                raise ValueError(
                    f"Unsupported tool: {step.tool}"
                )

            tool_input = self._build_tool_input(step)

            result = tool.run(tool_input)

            return result

        except Exception as exc:
            execution_time = (
                time.perf_counter() - start_time
            ) * 1000

            return ToolResult(
                tool_name=step.tool,
                success=False,
                output=None,
                error=str(exc),
                execution_time_ms=round(
                    execution_time,
                    2,
                ),
            )

    def _build_tool_input(
        self,
        step: PlanStep,
    ) -> Any:
        """Build the input required by the selected tool."""

        if step.tool == "calculator":
            return self._extract_calculation(
                step.description
            )

        if step.tool in {
            "web_search",
            "page_fetcher",
        }:
            return step.description

        raise ValueError(
            f"Cannot build input for tool: {step.tool}"
        )

    def _extract_calculation(
        self,
        description: str,
    ) -> str:
        """
        Convert simple natural-language arithmetic
        into a calculator-compatible expression.
        """

        expression = description.strip().lower()

        # -------------------------------------------------
        # 1. Remove common natural-language prefixes
        # -------------------------------------------------

        prefixes = [
            "calculate the result of",
            "calculate result of",
            "calculate",
            "the result of",
        ]

        for prefix in prefixes:
            expression = expression.replace(
                prefix,
                "",
            )

        # -------------------------------------------------
        # 2. Convert natural-language operators
        # -------------------------------------------------

        replacements = {
            "multiplied by": "*",
            "multiply by": "*",
            "times": "*",
            "divided by": "/",
            "divide by": "/",
            "plus": "+",
            "minus": "-",
        }

        for phrase, operator in replacements.items():
            expression = expression.replace(
                phrase,
                operator,
            )

        # -------------------------------------------------
        # 3. Remove common punctuation
        # -------------------------------------------------

        expression = expression.replace(
            "?",
            "",
        )

        expression = expression.replace(
            "=",
            "",
        )

        # Remove trailing sentence punctuation.
        expression = re.sub(
            r"[.,!?;:]+$",
            "",
            expression.strip(),
        )

        # -------------------------------------------------
        # 4. Keep only valid calculator characters
        # -------------------------------------------------

        expression = re.sub(
            r"[^0-9+\-*/().%\s]",
            "",
            expression,
        )

        # -------------------------------------------------
        # 5. Normalize whitespace
        # -------------------------------------------------

        expression = " ".join(
            expression.split()
        )

        if not expression:
            raise ValueError(
                "Could not extract a calculation from: "
                f"{description}"
            )

        # -------------------------------------------------
        # 6. Validate final expression
        # -------------------------------------------------

        if not re.fullmatch(
            r"[\d\s+\-*/().%]+",
            expression,
        ):
            raise ValueError(
                f"Invalid calculator expression: "
                f"{expression}"
            )

        return expression