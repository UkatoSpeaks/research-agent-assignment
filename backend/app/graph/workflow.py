from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    advance_node,
    execute_node,
    plan_node,
    recovery_node,
    report_node,
    validate_node,
)

from app.graph.router import (
    route_after_recovery,
    route_after_validation,
)

from app.graph.state import AgentState


def build_workflow():
    graph = StateGraph(
        AgentState
    )

    graph.add_node(
        "planner",
        plan_node,
    )

    graph.add_node(
        "executor",
        execute_node,
    )

    graph.add_node(
        "validator",
        validate_node,
    )

    graph.add_node(
        "recovery",
        recovery_node,
    )

    graph.add_node(
        "advance",
        advance_node,
    )

    graph.add_node(
        "reporter",
        report_node,
    )

    graph.add_edge(
        START,
        "planner",
    )

    graph.add_edge(
        "planner",
        "executor",
    )

    graph.add_edge(
        "executor",
        "validator",
    )

    graph.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "advance": "advance",
            "recover": "recovery",
            "complete": "reporter",
        },
    )

    graph.add_conditional_edges(
        "recovery",
        route_after_recovery,
        {
            "retry": "executor",
            "complete": "reporter",
        },
    )

    graph.add_edge(
        "advance",
        "executor",
    )

    graph.add_edge(
        "reporter",
        END,
    )

    return graph.compile()