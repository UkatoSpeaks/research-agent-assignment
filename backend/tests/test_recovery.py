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
    assert event.recovered is False
    assert event.error == "Search failed"
    assert event.recovery_action