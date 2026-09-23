from app.graph.workflow import build_workflow


def test_workflow_runs():
    workflow = build_workflow()

    result = workflow.invoke(
        {
            "goal": (
                "Calculate the result of 125 multiplied by 0.8."
            )
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

    final_result = result["tool_results"][-1]

    assert final_result.success is True
    assert final_result.output["result"] == 100.0