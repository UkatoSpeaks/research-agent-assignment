from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    tool_name: Literal[
        "web_search",
        "page_fetcher",
        "calculator",
    ]

    input: dict[str, Any] = Field(
        default_factory=dict,
    )


class ToolResult(BaseModel):
    tool_name: str

    success: bool

    output: Any = None

    error: str | None = None

    execution_time_ms: float | None = None