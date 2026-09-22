from typing import Literal

from pydantic import BaseModel, Field


ToolName = Literal[
    "web_search",
    "page_fetcher",
    "calculator",
]


class PlanStep(BaseModel):
    step_id: int = Field(
        ...,
        ge=1,
        description="Sequential step number.",
    )

    description: str = Field(
        ...,
        min_length=5,
        description="What this step should accomplish.",
    )

    tool: ToolName = Field(
        ...,
        description="Tool required to complete this step.",
    )

    expected_output: str = Field(
        ...,
        min_length=5,
        description="Expected result from this step.",
    )


class ExecutionPlan(BaseModel):
    goal: str = Field(
        ...,
        min_length=10,
    )

    steps: list[PlanStep] = Field(
        ...,
        min_length=1,
        max_length=10,
    )

    reasoning_summary: str = Field(
        ...,
        min_length=10,
        description="Brief explanation of why these steps are needed.",
    )