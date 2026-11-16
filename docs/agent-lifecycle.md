# How an ideal agent should be made — phase by phase

> Written 16 Nov 2026, based on the findings in `research.md`. **This is a synthesis, not an
> official industry standard**: no single lifecycle exists. The order is my recommendation from
> what Anthropic, OpenAI, Cognition, HumanLayer, Manus, Shopify, OWASP and Meta describe.
>
> Not to be confused with `phase.md`, which holds *this project's* build phases. This file
> describes the phases of building *any* agent — the lifecycle the skill would guide a coding
> agent through.

Two things run through every phase: **evals** (the test cases the agent is scored on) and
**traces** (the step-by-step records of what the agent did). Most phases either create them or
are judged by them.

---

## Phase 0: Problem and value
**Goal:** prove the task is worth automating before thinking about agents.
- **Define the job:** who uses it, what the task is, how it's done today, and what success is
  worth. Set budgets for cost per task, response time, and how much risk is acceptable.
- **Collect 20–50 real examples:** each with its input and what a good output looks like. These
  later become your test cases.
- **Decide** whether to automate at all. Gartner expects over 40% of agent projects to be
  cancelled, mainly for unclear value.
- **Done when:** success is defined by a number, and you have real examples.
- **Common mistake:** starting from "let's build an agent" instead of from the task.

## Phase 1: Spec and design shape
**Goal:** choose the simplest design that can do the job.
- **Write the spec:** inputs, outputs, the data and tools needed, the side effects each action
  has, what the agent must *not* do, budgets, and where a human steps in.
- **Climb the ladder one rung at a time:** single LLM call → fixed workflow → one agent in a
  loop → multiple agents. Write down why each lower rung isn't enough.
- **If you need several agents:** only one may write; the helpers only read or review
  (Cognition).
- **Choose models per role:** a strong model leads and cheaper ones do the helper work.
- **Done when:** a reviewer agrees there is no simpler design that would work.
- **Common mistake:** going multi-agent by default. It costs far more tokens (about 15× a normal
  chat in Anthropic's research system) and causes agents to make conflicting decisions.

## Phase 2: Evals before code
**Goal:** know what "working" means before building anything.
- **Turn the Phase 0 examples into four kinds of test cases:**
  - normal cases
  - edge cases
  - attack and prompt-injection cases
  - cases the agent must refuse
- **Pick graders, roughly in this order:**
  - code checks first
  - an LLM judge, tuned until it agrees with human labels (Shopify)
  - human review on a sample
- **Pick the metric:**
  - **pass@k** (succeeds at least once in k tries) if retries are acceptable
  - **pass^k** (succeeds every time) if they aren't
- **Measure a baseline:** run the simplest version, a single prompt, through the tests to get a
  score to beat.
- **Done when:** the test suite runs and you have a baseline score.

## Phase 3: Threat model and permissions
**Goal:** settle the security design before any tool exists.
- **Classify every planned tool** as read-only, reversible write, irreversible, or external
  communication.
- **Apply Meta's Rule of Two:** in any one session, the agent may have at most two of these
  three:
  1. access to private data
  2. untrusted input
  3. the ability to send data out or change things

  Allow all three only with a human approval step.
- **Decide the controls:**
  - run tools in a sandbox
  - keep credentials outside the sandbox, added by a proxy
  - give each tool only the access it needs
  - mark untrusted content as data, never as instructions
  - require human approval for anything irreversible
- **Check the OWASP Agentic Top 10:** goal hijacking, tool misuse, memory poisoning, cascading
  failures, and the rest.
- **Done when:** every tool has a class and a control, and no session breaks the Rule of Two
  without a human step.

## Phase 4: Tools
**Goal:** tools the model can use reliably. Anthropic calls this the agent–computer interface.
- **Keep the set small,** with clear boundaries. Shopify saw quality drop as Sidekick's tools
  grew from a handful to dozens.
- **Write names and descriptions for the model, not for humans.**
- **Make outputs efficient and safe:**
  - keep outputs short and paginate or truncate large results
  - return error messages that tell the model how to fix the call
  - set timeouts
  - make actions safe to repeat
- **For outside systems,** use MCP and load tool definitions only when needed. For long chains
  of tool calls, let the agent write code that calls the tools.
- **Test each tool with the model itself,** and improve the descriptions using the evals
  (Anthropic does this with Claude).
- **Done when:** each tool passes its own tests, and the tests that check tool choice pass.

## Phase 5: The harness (loop, context, state)
**Goal:** the machinery around the model. Per the research, most of the reliability comes from
here.
- **Loop:** gather context → act → verify. Set explicit stop conditions, a maximum number of
  steps, and token and cost budgets.
- **Own the prompts and the control flow** (12-Factor Agents). Treat the agent as a stateless
  reducer: all state lives in data, so the agent can pause and resume.
- **Context engineering:**
  - Keep the start of the prompt stable so it stays cached. Cached input is about 10× cheaper
    (Manus).
  - Only append to the context.
  - Don't add or remove tools in the middle of a task.
  - Set a policy for summarising when the context fills up.
  - Keep notes and memory files outside the context.
  - Send exploration to helper agents that return only a summary.
- **Durability:**
  - Save a checkpoint after each step.
  - Resume after a crash.
  - For long tasks, keep a JSON feature list, a progress file, and git commits (Anthropic).
- **Verification:** the agent checks its own work with tests, validators or a fresh-context
  reviewer.
- **Choose the framework now:**

  | Option | Choose it when |
  |---|---|
  | LangGraph | you need checkpoints and human approval steps |
  | OpenAI Agents SDK | simplicity matters most |
  | Google ADK | you're on Google's platform |
  | Claude Agent SDK | you want Claude Code's harness |
  | Plain loop | the agent is small |

- **Done when:** the agent survives being killed and resumed, and the context stays within
  budget on the longest test task.

## Phase 6: Build against the evals
**Goal:** improve the score with evidence, not guesses.
- **Loop:** run the evals → **read the failing traces** → group the failures by cause → fix the
  prompt, tool or harness → run again.
- **Change one thing at a time.** Record the score for each version, and treat any drop in score
  as a blocker.
- **Remove anything that doesn't improve the score.**
- **Done when:** the target pass rate is reached within the cost and time budgets.
- **Common mistake:** changing prompts on gut feeling without reading the traces.

## Phase 7: Observability and readiness for operation
**Goal:** be able to answer "why did it do that?" for any run.
- **Trace every step:**
  - calls to the agent
  - each tool call
  - tokens, cost, timing and errors

  Use the OpenTelemetry GenAI format; it is still marked "Development". Keep content capture
  switched off by default for privacy.
- **Watch the key metrics:** cache hit rate, tool error rate, how often it hands off to a human,
  and cost per task.
- **Pin versions** of the model, prompts and tools.
- **Add the operational basics:** retries, timeouts, fallbacks, rate limits, and a kill switch.
- **Run a red-team pass,** for example prompt-injection attacks, before real users touch it.
- **Done when:** any run can be explained from its trace, and the red-team findings are fixed.

## Phase 8: Rollout in stages
**Goal:** earn autonomy instead of assuming it.
- **Stages:**
  1. **Shadow:** the agent runs, but nobody acts on its output.
  2. **Assistive:** a human approves every action.
  3. **Partial autonomy:** the agent acts alone on low-risk actions only.
  4. **Wider rollout.**
- **Test every change** against simulated conversations built from real ones before shipping
  (Shopify).
- **Set exit criteria for each stage,** for example: approval rate above X% and zero critical
  incidents over N days.
- **Done when:** the agent reaches the autonomy level the spec allows, backed by the data.

## Phase 9: Operate and improve
**Goal:** the agent gets better over time instead of drifting.
- **Turn failures into tests:** sample production traces, label them, and add every failure to
  the test set.
- **When the model is upgraded,** rerun all evals and re-tune the LLM judge.
- **Simplify regularly.** Better models make some of the harness unnecessary, so remove it.
- **Keep the docs current:** AGENTS.md, a runbook, and a change log.
- **This phase never ends.**

---

## Summary

| Phase | Main output | Done when |
|---|---|---|
| 0 Problem and value | Problem brief, real examples | Success has a number |
| 1 Spec and shape | Spec and design choice | No simpler design would work |
| 2 Evals | Test suite and baseline | Baseline score recorded |
| 3 Threat model | Tool classes and controls | Rule of Two holds |
| 4 Tools | Tested tools | Tool-choice tests pass |
| 5 Harness | Loop, context and state design | Survives kill and resume; context in budget |
| 6 Build | Agent that passes the evals | Target pass rate within budget |
| 7 Observability | Traces, metrics, red-team report | Every run explainable |
| 8 Rollout | Staged autonomy | Stage exit criteria met |
| 9 Operate | Growing test set | Never; it's ongoing |

## What this means for the skill

These ten phases are close to what the skill would walk a coding agent through. Phases 0–7 can
be generated or scaffolded. Phases 8–9 happen after launch with real users, so the skill can only
set them up (a rollout plan and a feedback loop).

Sources: see `research.md`.
