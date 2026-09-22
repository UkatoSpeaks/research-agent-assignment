from app.schemas import (
    ExecutionPlan,
    FinalReport,
    GoalInput,
    PlanStep,
    ToolResult,
)


def test_goal_input():
    goal = GoalInput(
        goal="Research the competitive landscape of AI coding assistants."
    )

    assert goal.goal.startswith("Research")


def test_execution_plan():
    plan = ExecutionPlan(
        goal="Research AI coding assistants",
        steps=[
            PlanStep(
                step_id=1,
                description="Find major AI coding assistant competitors",
                tool="web_search",
                expected_output="List of relevant competitors",
            )
        ],
        reasoning_summary="Identify competitors before collecting detailed information.",
    )

    assert len(plan.steps) == 1
    assert plan.steps[0].tool == "web_search"


def test_tool_result_success():
    result = ToolResult(
        tool_name="web_search",
        success=True,
        output={"results": []},
    )

    assert result.success is True


def test_tool_result_failure():
    result = ToolResult(
        tool_name="page_fetcher",
        success=False,
        error="HTTP 503 Service Unavailable",
    )

    assert result.success is False
    assert result.error == "HTTP 503 Service Unavailable"