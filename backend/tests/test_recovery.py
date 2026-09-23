from app.agents.recovery import RecoveryAgent
from app.schemas import ToolResult


def test_recovery_event():
    recovery = RecoveryAgent()

    result = ToolResult(
        tool_name="web_search",
        success=False,
        error="Search failed",
    )

    event = recovery.create_recovery_event(
        step_id=2,
        result=result,
    )

    assert event.step_id == 2
    assert event.recovered is True
    assert event.error == "Search failed"
    assert event.recovery_action


def test_recovery_retries():
    recovery = RecoveryAgent()

    assert recovery.should_retry(0) is True
    assert recovery.should_retry(1) is True
    assert recovery.should_retry(2) is False