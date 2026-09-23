"""ResearchPilot CLI entry point.

Runs the LangGraph agent end-to-end on a natural-language goal and
prints a visible planning trace, step-by-step execution/recovery
trace, and the final structured report.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.graph.workflow import build_workflow
from app.schemas import ExecutionPlan, FinalReport

app = typer.Typer(
    name="research-pilot",
    help="ResearchPilot: an autonomous research agent that plans, "
    "uses tools, and self-corrects to answer a high-level goal.",
    add_completion=False,
)


def _print_plan(console: Console, plan: ExecutionPlan) -> None:
    console.rule("[bold cyan]Planning")

    console.print(
        Panel(
            plan.reasoning_summary,
            title="Reasoning",
            border_style="cyan",
        )
    )

    table = Table(title="Execution Plan", show_lines=True)
    table.add_column("#", justify="right")
    table.add_column("Tool", style="magenta")
    table.add_column("Description")
    table.add_column("Expected Output")

    for step in plan.steps:
        table.add_row(
            str(step.step_id),
            step.tool,
            step.description,
            step.expected_output,
        )

    console.print(table)


def _print_execution_entry(
    console: Console,
    entry: dict,
    total_steps: int,
) -> None:
    status = (
        "[bold green]SUCCESS[/bold green]"
        if entry["success"]
        else "[bold red]FAILED[/bold red]"
    )

    console.print(
        f"[bold]Step {entry['step_id']}/{total_steps}[/bold] "
        f"([magenta]{entry['tool']}[/magenta]) "
        f"attempt #{entry['retry_count'] + 1} -> {status} "
        f"({entry['execution_time_ms']} ms)"
    )

    console.print(f"  [dim]{entry['description']}[/dim]")


def _print_recovery_event(console: Console, event) -> None:
    recovered = (
        "[green]recovered[/green]"
        if event.recovered
        else "[red]not recovered[/red]"
    )

    console.print(
        Panel(
            f"Error: {event.error}\n"
            f"Action: {event.recovery_action}\n"
            f"Outcome: {recovered}",
            title=f"Recovery - Step {event.step_id}",
            border_style="yellow",
        )
    )


def _report_to_markdown(report: FinalReport) -> str:
    lines = [
        "# ResearchPilot Report",
        "",
        f"**Goal:** {report.goal}",
        f"**Status:** {report.status}",
        "",
        "## Summary",
        report.summary,
        "",
    ]

    if report.findings:
        lines.append("## Findings")
        for finding in report.findings:
            lines.append(f"### {finding.title}")
            lines.append(finding.summary)
            if finding.source_urls:
                lines.append("")
                lines.append(
                    "Sources: "
                    + ", ".join(finding.source_urls)
                )
            lines.append("")

    if report.sources:
        lines.append("## Sources")
        for source in report.sources:
            lines.append(f"- {source}")
        lines.append("")

    if report.recovery_events:
        lines.append("## Recovery Events")
        for event in report.recovery_events:
            lines.append(
                f"- Step {event.step_id}: {event.error} -> "
                f"{event.recovery_action} "
                f"(recovered={event.recovered})"
            )
        lines.append("")

    if report.limitations:
        lines.append("## Limitations")
        for limitation in report.limitations:
            lines.append(f"- {limitation}")
        lines.append("")

    metrics = report.metrics
    lines.append("## Metrics")
    lines.append(f"- Total steps: {metrics.total_steps}")
    lines.append(f"- Completed steps: {metrics.completed_steps}")
    lines.append(f"- Tool calls: {metrics.tool_calls}")
    lines.append(f"- Failed tool calls: {metrics.failed_tool_calls}")
    lines.append(
        f"- Recovery attempts: {metrics.recovery_attempts}"
    )

    return "\n".join(lines)


def _print_report(console: Console, report: FinalReport) -> None:
    console.rule("[bold green]Final Report")

    console.print(
        Panel(
            f"[bold]{report.status.upper()}[/bold]\n\n"
            f"{report.summary}",
            title="ResearchPilot Report",
            border_style="green",
        )
    )

    if report.findings:
        table = Table(title="Findings", show_lines=True)
        table.add_column("Title")
        table.add_column("Summary")
        table.add_column("Sources")

        for finding in report.findings:
            table.add_row(
                finding.title,
                finding.summary,
                "\n".join(finding.source_urls) or "-",
            )

        console.print(table)

    metrics = report.metrics
    metrics_table = Table(title="Execution Metrics")
    metrics_table.add_column("Metric")
    metrics_table.add_column("Value", justify="right")
    metrics_table.add_row("Total steps", str(metrics.total_steps))
    metrics_table.add_row(
        "Completed steps", str(metrics.completed_steps)
    )
    metrics_table.add_row("Tool calls", str(metrics.tool_calls))
    metrics_table.add_row(
        "Failed tool calls", str(metrics.failed_tool_calls)
    )
    metrics_table.add_row(
        "Recovery attempts", str(metrics.recovery_attempts)
    )
    console.print(metrics_table)

    if report.limitations:
        console.print(
            Panel(
                "\n".join(f"- {item}" for item in report.limitations),
                title="Limitations",
                border_style="red",
            )
        )


@app.command()
def run(
    goal: str = typer.Argument(
        ...,
        help="High-level natural-language goal for the agent.",
    ),
    force_failure: bool = typer.Option(
        False,
        "--force-failure",
        help=(
            "Deliberately fail the first tool call to demonstrate "
            "the recovery/retry path."
        ),
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Write the final report as JSON to this path.",
    ),
    markdown_output: Optional[Path] = typer.Option(
        None,
        "--markdown",
        "-m",
        help="Write the final report as Markdown to this path.",
    ),
    transcript: Optional[Path] = typer.Option(
        None,
        "--transcript",
        "-t",
        help="Write the full console transcript to this path.",
    ),
) -> None:
    """Run ResearchPilot end-to-end on a natural-language goal."""

    console = Console(record=transcript is not None)

    console.rule("[bold cyan]ResearchPilot")
    console.print(f"[bold]Goal:[/bold] {goal}")

    if force_failure:
        console.print(
            "[yellow]Failure injection enabled: the first tool "
            "call will be forced to fail to demonstrate "
            "recovery.[/yellow]"
        )

    workflow = build_workflow()

    final_state: dict = {}
    total_steps = 0
    seen_recovery_events = 0

    try:
        for update in workflow.stream(
            {
                "goal": goal,
                "force_failure": force_failure,
            },
            stream_mode="updates",
        ):
            for node_name, state_update in update.items():
                final_state.update(state_update)

                if node_name == "planner":
                    plan: ExecutionPlan = state_update["plan"]
                    total_steps = len(plan.steps)
                    _print_plan(console, plan)
                    console.rule("[bold cyan]Execution")

                elif node_name == "executor":
                    entry = state_update["execution_log"][-1]
                    _print_execution_entry(
                        console, entry, total_steps
                    )

                elif node_name == "recovery":
                    events = state_update["recovery_events"]
                    for event in events[seen_recovery_events:]:
                        _print_recovery_event(console, event)
                    seen_recovery_events = len(events)

                elif node_name == "reporter":
                    _print_report(
                        console, state_update["final_report"]
                    )

    except Exception as exc:  # noqa: BLE001 - surfaced to the user
        console.print(
            f"[bold red]ResearchPilot failed:[/bold red] {exc}"
        )
        raise typer.Exit(code=1) from exc

    final_report: Optional[FinalReport] = final_state.get(
        "final_report"
    )

    if final_report is None:
        console.print(
            "[bold red]No final report was produced.[/bold red]"
        )
        raise typer.Exit(code=1)

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(final_report.model_dump(), indent=2),
            encoding="utf-8",
        )
        console.print(f"[dim]JSON report written to {output}[/dim]")

    if markdown_output is not None:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(
            _report_to_markdown(final_report),
            encoding="utf-8",
        )
        console.print(
            f"[dim]Markdown report written to {markdown_output}[/dim]"
        )

    if transcript is not None:
        transcript.parent.mkdir(parents=True, exist_ok=True)
        transcript.write_text(
            console.export_text(),
            encoding="utf-8",
        )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
