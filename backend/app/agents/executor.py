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

    def execute_step(
        self,
        step: PlanStep,
        tool_results: list[ToolResult] | None = None,
    ) -> ToolResult:
        """Execute a single plan step.

        ``tool_results`` is the history of results produced so far in
        this run. It is used to resolve inputs that depend on earlier
        steps, e.g. picking a real URL for ``page_fetcher`` out of a
        prior ``web_search`` result, since the planner cannot know
        concrete URLs ahead of time.
        """

        start_time = time.perf_counter()

        try:
            tool = self.tools.get(step.tool)

            if tool is None:
                raise ValueError(
                    f"Unsupported tool: {step.tool}"
                )

            tool_input = self._build_tool_input(
                step, tool_results or []
            )

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
        tool_results: list[ToolResult],
    ) -> Any:
        """Build the input required by the selected tool."""

        if step.tool == "calculator":
            return self._extract_calculation(
                step.description
            )

        if step.tool == "web_search":
            return step.description

        if step.tool == "page_fetcher":
            return self._resolve_page_fetcher_url(
                step, tool_results
            )

        raise ValueError(
            f"Cannot build input for tool: {step.tool}"
        )

    def _resolve_page_fetcher_url(
        self,
        step: PlanStep,
        tool_results: list[ToolResult],
    ) -> str:
        """
        Determine the URL a page_fetcher step should fetch.

        The planner writes step descriptions in natural language
        (e.g. "Fetch the first selected article...") since it cannot
        know real URLs ahead of time. If the description already
        contains a literal URL, use it directly. Otherwise, pick the
        next not-yet-fetched URL out of the most recent successful
        web_search results.
        """

        url_match = re.search(
            r"https?://\S+",
            step.description,
        )

        if url_match:
            return url_match.group(0).rstrip(
                ").,;:!?\"'"
            )

        candidate_urls = self._collect_search_urls(
            tool_results
        )

        if not candidate_urls:
            raise ValueError(
                "No URL was found in the step description and no "
                "prior web_search results are available to select "
                "one from."
            )

        already_fetched = {
            result.output.get("url")
            for result in tool_results
            if result.tool_name == "page_fetcher"
            and result.success
            and isinstance(result.output, dict)
        }

        for url in candidate_urls:
            if url not in already_fetched:
                return url

        return candidate_urls[0]

    def _collect_search_urls(
        self,
        tool_results: list[ToolResult],
    ) -> list[str]:
        """Collect candidate URLs from prior web_search results, in order."""

        urls: list[str] = []

        for result in tool_results:
            if (
                result.tool_name != "web_search"
                or not result.success
                or not isinstance(result.output, dict)
            ):
                continue

            for item in result.output.get("results", []):
                url = (
                    item.get("url")
                    if isinstance(item, dict)
                    else None
                )

                if url and url not in urls:
                    urls.append(url)

        return urls

    def _extract_calculation(
        self,
        description: str,
    ) -> str:
        """
        Convert natural-language arithmetic into a
        calculator-compatible mathematical expression.

        Examples:

        '125 * 0.8'
            -> '125 * 0.8'

        'Calculate 125 times 0.8'
            -> '125 * 0.8'

        'Calculate the result of 125 multiplied by 0.8'
            -> '125 * 0.8'

        'Compute the product of 125 and 0.8'
            -> '125 * 0.8'

        '125 plus 25'
            -> '125 + 25'
        """

        original = description.strip()
        expression = original.lower()

        # -------------------------------------------------
        # 1. Remove trailing punctuation
        # -------------------------------------------------

        expression = re.sub(
            r"[.,!?;:]+$",
            "",
            expression.strip(),
        )

        # -------------------------------------------------
        # 2. Check whether it is already an expression
        # -------------------------------------------------

        direct_expression = expression

        direct_expression = re.sub(
            r"[^0-9+\-*/().%\s]",
            "",
            direct_expression,
        )

        direct_expression = " ".join(
            direct_expression.split()
        )

        if (
            direct_expression
            and re.fullmatch(
                r"[\d\s+\-*/().%]+",
                direct_expression,
            )
            and re.search(
                r"[+\-*/%]",
                direct_expression,
            )
        ):
            return direct_expression

        # -------------------------------------------------
        # 3. Detect the mathematical operation
        # -------------------------------------------------

        # Stems (not full phrases) so word order between the
        # keyword and the operands does not matter, e.g. both
        # "multiplied by" and "Multiply 125 by 0.8" should match.
        multiplication_patterns = [
            "multipl",
            "times",
            "product",
        ]

        division_patterns = [
            "divid",
            "quotient",
        ]

        addition_patterns = [
            "plus",
            "sum",
            "added",
        ]

        subtraction_patterns = [
            "minus",
            "subtract",
            "difference",
        ]

        operator = None

        if any(
            pattern in expression
            for pattern in multiplication_patterns
        ):
            operator = "*"

        elif any(
            pattern in expression
            for pattern in division_patterns
        ):
            operator = "/"

        elif any(
            pattern in expression
            for pattern in addition_patterns
        ):
            operator = "+"

        elif any(
            pattern in expression
            for pattern in subtraction_patterns
        ):
            operator = "-"

        # -------------------------------------------------
        # 4. If no natural-language operator was found,
        #    try to detect a mathematical operator.
        # -------------------------------------------------

        if operator is None:
            if "*" in expression:
                operator = "*"
            elif "/" in expression:
                operator = "/"
            elif "+" in expression:
                operator = "+"
            elif "-" in expression:
                operator = "-"
            elif "%" in expression:
                operator = "%"

        if operator is None:
            raise ValueError(
                "Could not determine the mathematical "
                f"operation from: {original}"
            )

        # -------------------------------------------------
        # 5. Extract numeric operands
        # -------------------------------------------------

        numbers = re.findall(
            r"-?\d+(?:\.\d+)?",
            expression,
        )

        if len(numbers) < 2:
            raise ValueError(
                "Could not extract two numeric operands "
                f"from: {original}"
            )

        # Use the first two operands for this simple
        # calculator tool.
        left = numbers[0]
        right = numbers[1]

        # -------------------------------------------------
        # 6. Build the calculator expression
        # -------------------------------------------------

        result = f"{left} {operator} {right}"

        # -------------------------------------------------
        # 7. Final safety validation
        # -------------------------------------------------

        if not re.fullmatch(
            r"-?\d+(?:\.\d+)?\s*[+\-*/%]\s*"
            r"-?\d+(?:\.\d+)?",
            result,
        ):
            raise ValueError(
                f"Invalid calculator expression: {result}"
            )

        return result