from pydantic import BaseModel, Field


class Finding(BaseModel):
    title: str
    summary: str
    source_urls: list[str] = Field(default_factory=list)


class RecoveryEvent(BaseModel):
    step_id: int
    error: str
    recovery_action: str
    recovered: bool


class ExecutionMetrics(BaseModel):
    total_steps: int = 0
    completed_steps: int = 0
    tool_calls: int = 0
    failed_tool_calls: int = 0
    recovery_attempts: int = 0


class FinalReport(BaseModel):
    goal: str

    status: str

    summary: str

    findings: list[Finding] = Field(
        default_factory=list,
    )

    sources: list[str] = Field(
        default_factory=list,
    )

    recovery_events: list[RecoveryEvent] = Field(
        default_factory=list,
    )

    metrics: ExecutionMetrics

    limitations: list[str] = Field(
        default_factory=list,
    )