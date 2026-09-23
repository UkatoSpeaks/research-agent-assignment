from app.schemas import RecoveryEvent, ToolResult


class RecoveryAgent:
    """Handles failed tool executions and determines recovery actions."""

    MAX_RETRIES = 2

    def should_retry(self, retry_count: int) -> bool:
        return retry_count < self.MAX_RETRIES

    def create_recovery_event(
        self,
        step_id: int,
        result: ToolResult,
        retry_count: int = 0,
    ) -> RecoveryEvent:
        error = result.error or "Unknown tool failure"

        action = self._get_recovery_action(
            result.tool_name
        )

        recovered = self.should_retry(retry_count)

        return RecoveryEvent(
            step_id=step_id,
            error=error,
            recovery_action=action,
            recovered=recovered,
        )

    def _get_recovery_action(
        self,
        tool_name: str,
    ) -> str:
        actions = {
            "web_search": (
                "Retry the search with a broader query."
            ),
            "page_fetcher": (
                "Retry the URL request."
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