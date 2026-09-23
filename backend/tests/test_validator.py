from app.agents.validator import ValidatorAgent
from app.schemas import ToolResult


def test_validator_accepts_success():
    validator = ValidatorAgent()

    result = ToolResult(
        tool_name="calculator",
        success=True,
        output={"result": 100},
    )

    assert validator.validate(result) is True


def test_validator_rejects_failure():
    validator = ValidatorAgent()

    result = ToolResult(
        tool_name="calculator",
        success=False,
        error="Invalid expression",
    )

    assert validator.validate(result) is False


def test_validator_rejects_empty_output():
    validator = ValidatorAgent()

    result = ToolResult(
        tool_name="calculator",
        success=True,
        output=None,
    )

    assert validator.validate(result) is False