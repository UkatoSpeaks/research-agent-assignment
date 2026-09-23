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

    def execute_step(
        self,
        step: PlanStep,
    ) -> ToolResult:
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
                error=str(exc),
                execution_time_ms=round(
                    execution_time,
                    2,
                ),
            )

    def _build_tool_input(self, step: PlanStep) -> Any:
        """
        Convert a plan step into the input expected by its tool.

        The planner currently produces natural-language step
        descriptions, so the executor derives the tool input
        from the step description.
        """

        if step.tool in {
            "web_search",
            "page_fetcher",
            "calculator",
        }:
            return step.description

        raise ValueError(
            f"Cannot build input for tool: {step.tool}"
        )