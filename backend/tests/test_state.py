from app.graph import AgentState


def test_agent_state():
    state: AgentState = {
        "goal": "Research AI coding assistants",
        "current_step": 0,
        "tool_results": [],
        "errors": [],
        "recovery_events": [],
        "retry_count": 0,
        "execution_log": [],
        "status": "initialized",
    }

    assert state["goal"] == "Research AI coding assistants"
    assert state["current_step"] == 0
    assert state["retry_count"] == 0
    assert state["status"] == "initialized"