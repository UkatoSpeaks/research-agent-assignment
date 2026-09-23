from app.schemas import ToolResult


class ValidatorAgent:
    """Validates tool results before the workflow continues."""


    def validate(self, result:ToolResult)->bool:
        if not result.success:
            return False

        if result.output is None:
            return False


        return True
    