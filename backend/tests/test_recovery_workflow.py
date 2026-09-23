from app.graph.workflow import build_workflow


def test_workflow_recovers_from_failure():
    workflow = build_workflow()

    result = workflow.invoke(
        {
            "goal": (
                "Calculate the result of 125 multiplied by 0.8."
            ),
            "force_failure": True,
        }
    )

    assert result["plan"]
    assert result["tool_results"]
    assert result["execution_log"]

    assert result["status"] in {
        "validated",
        "completed",
        "ready",
    }

    assert len(result["recovery_events"]) >= 1

    recovery_event = result["recovery_events"][0]

    assert recovery_event.recovered is True

    # First attempt failed, second attempt succeeded.
    assert len(result["tool_results"]) >= 2

    assert result["tool_results"][0].success is False
    assert result["tool_results"][1].success is True