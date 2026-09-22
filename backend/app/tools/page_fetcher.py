import time

import httpx
from bs4 import BeautifulSoup

from app.config.settings import settings
from app.schemas import ToolResult


class PageFetcherTool:
    """Fetch a web page and extract readable text."""

    def __init__(self) -> None:
        self.timeout = settings.REQUEST_TIMEOUT

    def run(self, url: str) -> ToolResult:
        start_time = time.perf_counter()

        try:
            if not url.strip():
                raise ValueError("URL cannot be empty.")

            response = httpx.get(
                url,
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "ResearchPilot/1.0 "
                        "(Agentic Research Assistant)"
                    )
                },
            )

            response.raise_for_status()

            content_type = response.headers.get(
                "content-type", ""
            ).lower()

            if "text/html" not in content_type:
                raise ValueError(
                    f"Unsupported content type: {content_type}"
                )

            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

            for element in soup(
                ["script", "style", "noscript", "svg"]
            ):
                element.decompose()

            text = soup.get_text(
                separator=" ",
                strip=True,
            )

            if not text:
                raise ValueError(
                    "The page returned no readable text."
                )

            execution_time = (
                time.perf_counter() - start_time
            ) * 1000

            return ToolResult(
                tool_name="page_fetcher",
                success=True,
                output={
                    "url": str(response.url),
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "text": text,
                },
                execution_time_ms=round(
                    execution_time,
                    2,
                ),
            )

        except httpx.TimeoutException:
            execution_time = (
                time.perf_counter() - start_time
            ) * 1000

            return ToolResult(
                tool_name="page_fetcher",
                success=False,
                error=(
                    f"Request timed out after "
                    f"{self.timeout} seconds."
                ),
                execution_time_ms=round(
                    execution_time,
                    2,
                ),
            )

        except httpx.HTTPStatusError as exc:
            execution_time = (
                time.perf_counter() - start_time
            ) * 1000

            return ToolResult(
                tool_name="page_fetcher",
                success=False,
                error=(
                    f"HTTP {exc.response.status_code}: "
                    f"{exc.response.reason_phrase}"
                ),
                execution_time_ms=round(
                    execution_time,
                    2,
                ),
            )

        except httpx.RequestError as exc:
            execution_time = (
                time.perf_counter() - start_time
            ) * 1000

            return ToolResult(
                tool_name="page_fetcher",
                success=False,
                error=f"Request failed: {str(exc)}",
                execution_time_ms=round(
                    execution_time,
                    2,
                ),
            )

        except Exception as exc:
            execution_time = (
                time.perf_counter() - start_time
            ) * 1000

            return ToolResult(
                tool_name="page_fetcher",
                success=False,
                error=str(exc),
                execution_time_ms=round(
                    execution_time,
                    2,
                ),
            )