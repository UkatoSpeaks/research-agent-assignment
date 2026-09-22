import time

from tavily import TavilyClient

from app.config.settings import settings
from app.schemas import ToolResult


class WebSearchTool:
    """Searches the live web using Tavily."""

    def __init__(self) -> None:
        self.client = TavilyClient(
            api_key=settings.TAVILY_API_KEY
        )

    def run(
        self,
        query: str,
        max_results: int | None = None,
    ) -> ToolResult:
        start_time = time.perf_counter()

        try:
            if not query.strip():
                raise ValueError("Search query cannot be empty.")

            results = self.client.search(
                query=query,
                max_results=max_results or settings.MAX_SEARCH_RESULTS,
                search_depth="advanced",
                include_answer=False,
                include_raw_content=False,
            )

            execution_time = (
                time.perf_counter() - start_time
            ) * 1000

            return ToolResult(
                tool_name="web_search",
                success=True,
                output=results,
                execution_time_ms=round(execution_time, 2),
            )

        except Exception as exc:
            execution_time = (
                time.perf_counter() - start_time
            ) * 1000

            return ToolResult(
                tool_name="web_search",
                success=False,
                output=None,
                error=str(exc),
                execution_time_ms=round(execution_time, 2),
            )