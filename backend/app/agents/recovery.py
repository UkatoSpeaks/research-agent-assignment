from app.schemas import RecoveryEvent, ToolResult


class RecoveryAgent:
    """Handles failed tool executions."""

    def create_recovery_event(
        self,
        step_id: int,
        result: ToolResult,
    ) -> RecoveryEvent:
        error = result.error or "Unknown tool failure"

        return RecoveryEvent(
            step_id=step_id,
            error=error,
            recovery_action=self._get_recovery_action(
                result.tool_name
            ),
            recovered=False,
        )

    def _get_recovery_action(self, tool_name: str) -> str:
        actions = {
            "web_search": (
                "Retry the search with a broader query."
            ),
            "page_fetcher": (
                "Retry the URL request before marking the "
                "step as failed."
            ),
            "calculator": (
                "Validate the expression and retry "
                "with a corrected expression."
            ),
        }

        return actions.get(
            tool_name,
            "Retry the failed tool execution.",
        )