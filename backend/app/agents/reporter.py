from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.config.settings import settings
from app.schemas import (
    ExecutionMetrics,
    FinalReport,
    Finding,
    RecoveryEvent,
    ToolResult,
)


MAX_RESULT_OUTPUT_CHARS = 3000


REPORTER_SYSTEM_PROMPT = """
You are the reporting component of ResearchPilot.

Your job is to convert tool execution results into a concise,
structured research report.

RULES:

1. Use ONLY information contained in the provided tool results.
2. Do not invent facts, sources, prices, features, or URLs.
3. Clearly distinguish findings from limitations.
4. Preserve source URLs whenever available.
5. If tool results contain search results, extract useful titles,
   URLs, and relevant content.
6. If information is missing, say that it is unavailable.
7. Do not expose hidden chain-of-thought.
8. Return only the structured FinalReport.
"""


class ReporterAgent:
    """Converts execution results into the final structured report."""

    def __init__(self) -> None:
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", REPORTER_SYSTEM_PROMPT),
                (
                    "human",
                    """
Goal:
{goal}

Execution results:
{results}

Recovery events:
{recovery_events}

Execution metrics:
{metrics}

Create the final structured report.
""",
                ),
            ]
        )

        self.structured_llm = self.llm.with_structured_output(
            FinalReport
        )

        self.chain = self.prompt | self.structured_llm

    def create_report(
        self,
        goal: str,
        tool_results: list[ToolResult],
        recovery_events: list[RecoveryEvent],
        metrics: ExecutionMetrics,
    ) -> FinalReport:
        """Generate the final structured report."""

        results_text = self._serialize_results(tool_results)

        recovery_text = self._serialize_recovery_events(
            recovery_events
        )

        metrics_text = metrics.model_dump_json(
            indent=2
        )

        report = self.chain.invoke(
            {
                "goal": goal,
                "results": results_text,
                "recovery_events": recovery_text,
                "metrics": metrics_text,
            }
        )

        return report

    def _serialize_results(
        self,
        results: list[ToolResult],
    ) -> str:
        """Convert tool results into readable text."""

        serialized: list[str] = []

        for index, result in enumerate(results, start=1):
            output_text = str(result.output)

            if len(output_text) > MAX_RESULT_OUTPUT_CHARS:
                output_text = (
                    output_text[:MAX_RESULT_OUTPUT_CHARS]
                    + " [truncated]"
                )

            serialized.append(
                f"""
Tool Result {index}
Tool: {result.tool_name}
Success: {result.success}
Output: {output_text}
Error: {result.error}
Execution Time: {result.execution_time_ms} ms
"""
            )

        return "\n".join(serialized)

    def _serialize_recovery_events(
        self,
        events: list[RecoveryEvent],
    ) -> str:
        """Convert recovery events into readable text."""

        if not events:
            return "No recovery events."

        serialized: list[str] = []

        for event in events:
            serialized.append(
                f"""
Step: {event.step_id}
Error: {event.error}
Recovery Action: {event.recovery_action}
Recovered: {event.recovered}
"""
            )

        return "\n".join(serialized)