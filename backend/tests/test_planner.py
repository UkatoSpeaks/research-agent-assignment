from app.agents.planner import PlannerAgent


def test_planner_creates_plan():
    planner = PlannerAgent()

    plan = planner.create_plan(
        "Research the competitive landscape of AI coding assistants "
        "including features and pricing."
    )

    assert plan.goal
    assert len(plan.steps) > 0
    assert plan.reasoning_summary

    for step in plan.steps:
        assert step.step_id > 0
        assert step.description
        assert step.tool
        assert step.expected_output