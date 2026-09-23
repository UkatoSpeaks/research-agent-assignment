from app.graph.state import AgentState


def route_after_validation(state: AgentState) -> str:
    status = state.get("status")

    if status == "validated":
        plan = state["plan"]
        current_step = state.get("current_step", 0)

        if current_step + 1 >= len(plan.steps):
            return "complete"

        return "advance"

    if status == "validation_failed":
        retry_count = state.get("retry_count", 0)

        if retry_count < 2:
            return "recover"

        return "complete"

    return "complete"


def route_after_recovery(state: AgentState) -> str:
    retry_count = state.get("retry_count", 0)

    if retry_count <= 2:
        return "retry"

    return "complete"