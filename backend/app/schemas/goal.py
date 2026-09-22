from pydantic import BaseModel,Field


class GoalInput(BaseModel):
    goal:str=Field(
        ...,
        min_length=10,
        max_length=2000,
        description="High-level goal provided by the user."
    )