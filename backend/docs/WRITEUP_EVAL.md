# ResearchPilot — Evaluation Write-up

*(Approach, precision/recall, production-readiness)*

## A note on "precision/recall"

ResearchPilot is a planning-and-tool-use agent, not a classifier — it
doesn't predict labels over a fixed set of classes, so precision and
recall in their literal (true/false positive) sense don't apply. What
they're really standing in for here is: *how often does the agent do
the right thing, and how often does it fail to do something it should
have done?* The closest honest analogues, computed from the 3 real
CLI runs in `docs/samples/` and the 19-test pytest suite (raw numbers
in `docs/monitoring_report.html` and `docs/test_traces.csv`), are:

| Proxy metric | Result | What it stands in for |
|---|---|---|
| Plan step completion rate | 14/14 = **100%** | "Recall" — did every planned step get executed to completion (directly or via recovery)? |
| Tool call success rate | 14/15 = **93.3%** | Reliability of individual tool invocations. |
| Recovery success rate | 1/1 = **100%** | Of the failures actually encountered, how many were self-corrected without operator intervention. |
| Automated test pass rate | 19/19 = **100%** | Regression coverage across schemas, tools, agents, and 2 full live end-to-end graph runs. |

The one failure across all 15 tool calls in the 3 sample runs was
deliberately injected (`--force-failure`), not organic — so the
current honest read is "zero uncaught failures observed in real
usage," which is a small sample, not a claim of general robustness.
Three runs is enough to demonstrate the mechanism works, not enough to
bound a real failure rate — see Production-readiness below.

## Approach

1. **Plan.** An LLM (Groq) converts the goal into a structured,
   typed `ExecutionPlan` — a list of steps, each with a tool
   assignment and an expected output. This plan is the "visible
   reasoning trace" surfaced to the user before any tool runs.
2. **Execute.** Each step is run against its assigned tool
   (`web_search`, `page_fetcher`, `calculator`). Inputs are resolved
   at execution time, not baked into the plan — e.g. `page_fetcher`
   URLs are pulled from the most recent successful `web_search`
   result, since the planner cannot know real URLs in advance.
3. **Validate.** Every tool result is checked for success and
   non-empty output before the graph is allowed to advance.
4. **Recover.** A failed validation routes to a `RecoveryAgent`,
   which logs a `RecoveryEvent` and retries the same step, capped at
   2 retries. Only after retries are exhausted does the run give up
   on that step and move to reporting anyway (partial results still
   produce a report, with the gap disclosed in "limitations").
5. **Report.** A second LLM call turns the accumulated tool results,
   recovery events, and metrics into a structured `FinalReport`,
   explicitly instructed to use only information present in the tool
   outputs and to say "unavailable" rather than fill gaps.

## Production-readiness

**What's solid enough to build on:**
- The plan → execute → validate → recover → report loop is a real
  state machine (LangGraph), not a single long prompt — each stage is
  independently testable and the 19-test suite exercises unit-level
  and full live end-to-end paths.
- Failure handling is structural, not incidental: any tool failure
  (not just the injected one) goes through the same validator/recovery
  path, and the 3 sample transcripts include organic failures caught
  during development (missing URLs, oversized page text hitting the
  LLM provider's rate limit) that got fixed in the tool/executor layer
  rather than papered over.
- The reporter is explicitly constrained to cite only real tool
  output, which is the main lever against hallucinated findings.

**What would block calling this production-ready today:**
- **Sample size.** 3 manual runs and a fixed retry cap of 2 is not a
  statistically meaningful reliability bound. Before shipping, this
  needs a larger, repeated batch of goals run automatically (not by
  hand) with pass/fail tracked over time, so the 93.3%/100% figures
  above become trend lines instead of single data points.
- **Fixed, undifferentiated retry policy.** Every tool gets the same
  "retry twice" treatment regardless of whether the failure was
  transient (network blip — worth retrying) or structural (a
  malformed step the planner produced — retrying won't fix it). A
  production version should classify the failure and choose the
  recovery action accordingly, and give up faster on non-transient
  errors instead of burning both retries.
- **Single LLM provider, no fallback.** Planning and reporting both
  depend on Groq; a provider outage or rate-limit event (already
  observed once during development — see `docs/WRITEUP.md`) takes
  down the whole agent with no fallback path.
- **No caching/dedup across runs.** Identical or overlapping goals
  re-fetch and re-search from scratch every time, which is both slower
  and more exposed to rate limits than necessary.
- **Sequential execution only.** Independent steps (e.g. multiple
  unrelated `page_fetcher` calls in run 03) run one at a time; this is
  simple and easy to reason about but not latency-efficient at scale.
- **No monitoring/alerting in the running system** — the metrics in
  this report are computed after the fact from saved JSON reports,
  not tracked live. A production deployment would need these emitted
  as real metrics (e.g. to a metrics backend) per run, not just
  bundled into each report's `ExecutionMetrics` block.

**Bottom line:** the control loop and failure-handling architecture
are sound and demonstrated working end-to-end against live APIs, but
this is evaluation-stage, not production-stage — the main gap is
breadth of testing (more goals, run automatically, over time) and
differentiated failure handling, not the core design.
