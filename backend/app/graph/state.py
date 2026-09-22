from typing import Any, TypedDict

from app.schemas import (
    ExecutionPlan,
    FinalReport,
    RecoveryEvent,
    ToolResult,
)


class AgentState(TypedDict, total=False):
    goal: str

    plan: ExecutionPlan
    current_step: int

    tool_results: list[ToolResult]

    errors: list[str]
    recovery_events: list[RecoveryEvent]
    retry_count: int

    execution_log: list[dict[str, Any]]

    final_report: FinalReport

    status: str