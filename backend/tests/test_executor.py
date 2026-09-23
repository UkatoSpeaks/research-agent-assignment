from app.agents.executor import ExecutorAgent
from app.schemas import PlanStep


def test_executor_calculator():
    executor = ExecutorAgent()

    step = PlanStep(
        step_id=1,
        description="125 * 0.8",
        tool="calculator",
        expected_output="The result should be 100.",
    )

    result = executor.execute_step(step)

    assert result.success is True
    assert result.output["result"] == 100.0


def test_executor_web_search():
    executor = ExecutorAgent()

    step = PlanStep(
        step_id=1,
        description="official GitHub Copilot pricing",
        tool="web_search",
        expected_output="Relevant pricing sources.",
    )

    result = executor.execute_step(step)

    assert result.success is True
    assert result.output is not None


def test_executor_page_fetcher():
    executor = ExecutorAgent()

    step = PlanStep(
        step_id=1,
        description="https://example.com",
        tool="page_fetcher",
        expected_output="Readable webpage text.",
    )

    result = executor.execute_step(step)

    assert result.success is True
    assert result.output["status_code"] == 200