# ResearchPilot

An autonomous research agent: give it a high-level goal, it plans a
sequence of steps, executes them with real tools (web search, page
fetching, calculation), self-corrects when a step fails, and returns a
structured report with findings, sources, metrics, and limitations.

Built for the Agentic AI Engineer Intern take-home assignment. See
[`docs/WRITEUP.md`](docs/WRITEUP.md) for design decisions and
limitations, [`docs/architecture.svg`](docs/architecture.svg) for the
architecture diagram, and [`docs/samples/`](docs/samples) for sample
run transcripts.

## How it works

```
CLI goal -> Planner (LLM) -> ExecutionPlan
                                  |
                                  v
                    +--------- Executor --------+
                    |     (runs step.tool)      |
                    v          v          v
               web_search  page_fetcher  calculator
                    |
                    v
                Validator --(ok)--> Advance --> next step
                    |
              (failed)
                    v
                Recovery --(retry < 2)--> back to Executor
                    |
             (all steps done / retries exhausted)
                    v
                 Reporter (LLM) -> FinalReport (JSON / Markdown)
```

The graph is built with LangGraph (`app/graph/workflow.py`); each box
above is a node operating on a single typed `AgentState`
(`app/graph/state.py`). See `docs/architecture.svg` for the full
diagram including the shared-state fields and color legend.

**Agents** (`app/agents/`):
- `PlannerAgent` — turns the goal into a structured `ExecutionPlan`
  (Groq LLM, structured output).
- `ExecutorAgent` — runs the tool for the current step; resolves
  natural-language calculator expressions into safe arithmetic, and
  resolves real URLs for `page_fetcher` steps out of prior
  `web_search` results (the planner can't know URLs ahead of time).
- `ValidatorAgent` — checks a tool result succeeded and produced output.
- `RecoveryAgent` — logs a `RecoveryEvent` and decides whether to retry
  (capped at 2 retries per step).
- `ReporterAgent` — turns the full run (results + recovery events +
  metrics) into a `FinalReport` (Groq LLM, structured output), using
  only information actually present in the tool results.

**Tools** (`app/tools/`):
- `web_search` — Tavily live web search.
- `page_fetcher` — fetches a URL and extracts readable text (httpx +
  BeautifulSoup), capped at `MAX_PAGE_TEXT_CHARS` to stay under the
  LLM provider's token-rate limit.
- `calculator` — arithmetic via a restricted `ast` evaluator (no
  `eval`).

## Setup

Requires Python 3.12+ and [`uv`](https://docs.astral.sh/uv/).

```bash
cd backend
uv sync
```

Create `backend/.env` with your API keys:

```
GROQ_API_KEY=your-groq-key
TAVILY_API_KEY=your-tavily-key
```

Both are free-tier services: https://console.groq.com and
https://tavily.com.

## Running it

```bash
# Basic run
uv run python -m app.main "Research and summarize the top 3 developments in AI coding assistants from the last week."

# Demonstrate the recovery path (forces the first tool call to fail)
uv run python -m app.main "Calculate 125 times 0.8" --force-failure

# Save the final report and a full console transcript
uv run python -m app.main "Plan a 3-day budget trip to Lisbon" \
  --output report.json \
  --markdown report.md \
  --transcript transcript.txt
```

On Windows, if you see a `UnicodeEncodeError` from the legacy console,
prefix the command with UTF-8 mode:

```bash
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run python -m app.main "..."
```

`uv run research-pilot "..."` also works after `uv sync` (it's
registered as a console script).

### CLI options

| Flag | Description |
|---|---|
| `--force-failure` | Fail the first tool call deliberately, to demonstrate the validator → recovery → retry path. |
| `-o, --output PATH` | Write the final report as JSON. |
| `-m, --markdown PATH` | Write the final report as Markdown. |
| `-t, --transcript PATH` | Write the full console trace (plan, execution log, recovery events, report) as plain text. |

## Testing

```bash
uv run pytest
```

19 tests covering schemas, tools, agents, graph state/routing, and two
full end-to-end workflow runs (`test_workflow.py`,
`test_recovery_workflow.py`) against the live Groq/Tavily APIs — these
require valid API keys in `.env` since no mocked dataset is used
anywhere in this project (see `docs/WRITEUP.md` for why).

## Project structure

```
backend/
  app/
    agents/       planner, executor, validator, recovery, reporter
    graph/        LangGraph state, nodes, routing, workflow assembly
    tools/        web_search, page_fetcher, calculator
    schemas/      pydantic models (goal, plan, tool result, report)
    config/       settings (.env-backed)
    main.py       CLI entry point
  tests/          pytest suite (schemas, tools, agents, graph, e2e)
  docs/
    WRITEUP.md        design decisions / limitations / next steps
    architecture.svg  architecture diagram
    samples/           3 sample run transcripts + reports
```

## Assumptions and simulated data

No dataset was provided or used. All information is sourced live via
Tavily search and direct HTTP page fetches at run time. The only
simulated element is `--force-failure`, an explicit CLI flag that
deliberately fails the first tool call so the recovery path can be
demonstrated on demand — it is separate from (and in addition to) the
real failure handling the agent also does for genuine tool errors
(HTTP failures, rate limits, unparsable pages, etc.), which the
`docs/samples/01_*` and `03_*` transcripts also incidentally exercise.
