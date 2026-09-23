from app.agents.executor import ExecutorAgent
from app.agents.planner import PlannerAgent
from app.agents.recovery import RecoveryAgent
from app.agents.reporter import ReporterAgent
from app.agents.validator import ValidatorAgent

from app.graph.state import AgentState

from app.schemas import (
    ExecutionMetrics,
    ToolResult,
)


planner = PlannerAgent()
executor = ExecutorAgent()
validator = ValidatorAgent()
recovery = RecoveryAgent()
reporter = ReporterAgent()


def plan_node(state: AgentState) -> AgentState:
    """Create an execution plan."""

    plan = planner.create_plan(
        state["goal"]
    )

    return {
        **state,
        "plan": plan,
        "current_step": 0,
        "tool_results": [],
        "errors": [],
        "recovery_events": [],
        "retry_count": 0,
        "execution_log": [],
        "status": "planned",
        "failure_injected": False,
    }


def execute_node(state: AgentState) -> AgentState:
    """Execute the current plan step."""

    plan = state["plan"]

    current_step = state.get(
        "current_step",
        0,
    )

    retry_count = state.get(
        "retry_count",
        0,
    )

    failure_injected = state.get(
        "failure_injected",
        False,
    )

    if current_step >= len(plan.steps):
        return {
            **state,
            "status": "completed",
        }

    step = plan.steps[current_step]

    if (
        state.get("force_failure", False)
        and not failure_injected
    ):
        result = ToolResult(
            tool_name=step.tool,
            success=False,
            output=None,
            error=(
                "Deliberate test failure "
                "for recovery demonstration."
            ),
            execution_time_ms=0.0,
        )

        failure_injected = True

    else:
        result = executor.execute_step(
            step,
            state.get("tool_results", []),
        )

    return {
        **state,

        "tool_results": [
            *state.get(
                "tool_results",
                [],
            ),
            result,
        ],

        "execution_log": [
            *state.get(
                "execution_log",
                [],
            ),
            {
                "step_id": step.step_id,
                "description": step.description,
                "tool": step.tool,
                "success": result.success,
                "retry_count": retry_count,
                "execution_time_ms": (
                    result.execution_time_ms
                ),
            },
        ],

        "failure_injected": failure_injected,

        "status": "executed",
    }


def validate_node(
    state: AgentState,
) -> AgentState:
    """Validate the latest tool result."""

    results = state.get(
        "tool_results",
        [],
    )

    if not results:
        return {
            **state,
            "status": "failed",
        }

    result = results[-1]

    if validator.validate(result):
        return {
            **state,
            "status": "validated",
        }

    return {
        **state,

        "errors": [
            *state.get(
                "errors",
                [],
            ),
            result.error
            or "Tool validation failed.",
        ],

        "status": "validation_failed",
    }


def recovery_node(
    state: AgentState,
) -> AgentState:
    """Create a recovery event after failure."""

    plan = state["plan"]

    current_step = state.get(
        "current_step",
        0,
    )

    retry_count = state.get(
        "retry_count",
        0,
    )

    results = state.get(
        "tool_results",
        [],
    )

    if not results:
        return {
            **state,
            "status": "failed",
        }

    result = results[-1]

    event = recovery.create_recovery_event(
        step_id=plan.steps[current_step].step_id,
        result=result,
        retry_count=retry_count,
    )

    return {
        **state,

        "recovery_events": [
            *state.get(
                "recovery_events",
                [],
            ),
            event,
        ],

        "retry_count": retry_count + 1,

        "status": "recovering",
    }


def advance_node(
    state: AgentState,
) -> AgentState:
    """Move to the next plan step."""

    current_step = state.get(
        "current_step",
        0,
    )

    return {
        **state,

        "current_step": (
            current_step + 1
        ),

        "retry_count": 0,

        "status": "ready",
    }


def report_node(
    state: AgentState,
) -> AgentState:
    """Generate the final structured report."""

    plan = state["plan"]

    tool_results = state.get(
        "tool_results",
        [],
    )

    recovery_events = state.get(
        "recovery_events",
        [],
    )

    execution_log = state.get(
        "execution_log",
        [],
    )

    completed_steps = sum(
        1
        for log in execution_log
        if log["success"]
    )

    failed_tool_calls = sum(
        1
        for result in tool_results
        if not result.success
    )

    metrics = ExecutionMetrics(
        total_steps=len(plan.steps),
        completed_steps=min(
            completed_steps,
            len(plan.steps),
        ),
        tool_calls=len(tool_results),
        failed_tool_calls=failed_tool_calls,
        recovery_attempts=len(
            recovery_events
        ),
    )

    final_report = reporter.create_report(
        goal=state["goal"],
        tool_results=tool_results,
        recovery_events=recovery_events,
        metrics=metrics,
    )

    return {
        **state,
        "final_report": final_report,
        "status": "completed",
    }