# ResearchPilot — Design Write-up

## What it does

ResearchPilot takes a high-level natural-language goal, plans it into a
sequence of tool-calling steps, executes those steps against live tools
(web search, page fetching, calculation), validates each result, retries
and recovers from failures, and produces a structured Markdown/JSON
report with findings, sources, metrics, and stated limitations.

## Design decisions

**LangGraph as the control loop, not a single ReAct prompt.** Planning,
execution, validation, recovery, and reporting are separate nodes with
explicit typed state (`AgentState`) passed between them. This makes the
failure-handling path (validator → recovery → retry, capped at 2
attempts) a first-class, testable part of the graph rather than
something buried in a prompt, and it makes the "visible planning trace"
requirement trivial — the plan is a discrete artifact produced before
any tool runs, not reconstructed after the fact.

**Plan-then-execute, with data resolved at execution time.** The
planner (Groq/`gpt-oss-120b`) commits to an `ExecutionPlan` up front —
it cannot know concrete URLs before `web_search` has run. So
`page_fetcher` steps carry a natural-language description ("fetch the
first selected article...") and the executor resolves the actual URL
at run time by scanning prior `web_search` results, skipping URLs
already fetched successfully. This was the single largest source of
real failures during testing (see Limitations) and fixing it — rather
than asking the planner to hallucinate URLs — was the most important
correctness decision in the system.

**Two independent tools, chosen for genuinely different failure modes.**
`web_search` (Tavily) and `page_fetcher` (httpx + BeautifulSoup) cover
discovery vs. verification and can fail for unrelated reasons (rate
limits vs. HTTP errors vs. paywalls). `calculator` (a restricted `ast`
evaluator, no `eval`) is a third tool used only when arithmetic is
explicitly required, so the plan doesn't force calculator use on
research-only goals.

**Deliberate failure injection is explicit, not hidden.** `--force-failure`
fails the first tool call on purpose with a labeled error so the
recovery path can be demonstrated on demand (see `docs/samples/02_*`),
separate from the real failures the agent also has to handle
day-to-day (HTTP errors, empty pages, rate limits — all handled by the
same validator/recovery path).

**No prompt-level trust in tool output.** The reporter is instructed to
use only information present in `tool_results` and to say explicitly
when something is unavailable, rather than filling gaps. This shows up
in the sample reports as honest "no third distinct development found"
/ "behind a paywall" statements instead of fabricated content.

## Assumptions / simulated data

No dataset was provided or needed — all data is sourced live via
Tavily search and direct HTTP fetches at run time. The only "mock" is
`--force-failure`, an explicit CLI flag that fails the first tool call
to make the recovery path demonstrable without waiting for a real
transient error.

## Limitations

- **Fixed retry budget (2 attempts)** with the same recovery action per
  tool; there's no differentiation between a transient network blip
  (worth retrying immediately) and a systemic issue like an invalid
  plan input (won't be fixed by retrying at all).
- **Page text is hard-truncated at 4,000 characters** to stay under the
  LLM provider's token-per-minute limit on the free tier. This is a
  real constraint discovered while building this: fetching three full
  articles into the reporter call previously exceeded Groq's 8K TPM
  limit outright. Truncation avoids the crash but can cut off relevant
  content on long pages.
- **No parallel tool execution** — steps run strictly in sequence even
  when independent (e.g. three unrelated `page_fetcher` calls), which
  is simple but slower than it needs to be.
- **Single LLM provider (Groq)** for both planning and reporting; no
  fallback if the provider is down or rate-limited beyond retries.
- **No persistent memory across runs** — every invocation starts from
  zero; there's no caching of search results or fetched pages.

## What I'd do differently with more time

- Make retries adaptive: classify the error (timeout vs. 4xx vs.
  parse failure) and choose a recovery action accordingly, instead of
  always "retry the same call."
- Parallelize independent steps in the executor rather than a purely
  sequential walk over `plan.steps`.
- Add a lightweight eval harness that runs a fixed set of synthetic
  goals (calculation, research, comparison, deliberately-broken input)
  on every change and checks the report against expected properties,
  instead of relying on the three sample transcripts checked in here.
- Summarize/chunk long pages instead of hard truncation, so length
  limits don't silently drop the most relevant part of an article.
