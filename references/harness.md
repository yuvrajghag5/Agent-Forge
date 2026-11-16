# Phase 8 — The harness: loop, context and state

Goal: the machinery around the model. Most of an agent's reliability comes from here.

Sources: Claude Code docs ("How Claude Code works"); Anthropic, "Effective context engineering"
and "Effective harnesses for long-running agents"; HumanLayer, 12-Factor Agents; Manus, context
engineering lessons; OpenAI, "Harness engineering" (Feb 2026).

## 1. The loop

Gather context → act → verify, repeated until done. Claude Code works this way: a simple
single-threaded loop where the model picks the next step from the last result, with the user able
to interrupt.

Every loop needs explicit stop conditions:

- a final answer or a completed task
- a maximum number of steps
- token, cost and wall-clock budgets (from the spec)
- **repeated-failure detection:** the same tool error, or the same action, three times in a row →
  stop and escalate instead of spinning

When a budget runs out, end with a clear partial result and the reason, never a silent cut-off.

## 2. Own the control flow and the state

- **Own your prompts.** Keep them in versioned files you can read and diff, not hidden inside a
  framework default.
- **State is data.** Hold a run's state (messages, tool results, current step, pending approval)
  in one serializable object. Then a run can pause for human approval, be stored, and resume
  later, even in another process. 12-Factor Agents calls this treating the agent as a stateless
  reducer.
- **Checkpoint after every step,** so a crash loses at most one step.
- **Pause and resume** are first-class: an approval request is a pause, not a blocking call
  inside a tool.

Done-test: kill the process in the middle of a run and resume it from the checkpoint.

## 3. Context engineering

Aim for the smallest set of high-signal tokens that lets the model do the step.

- **System prompt at the right altitude:** clear principles and the reasons behind them, not a
  wall of brittle if-then rules and not vague slogans.
- **Cache-friendly layout** (cached input is roughly 10× cheaper with major providers):
  - keep the start of the prompt stable; no timestamps or per-request values at the top
  - append to the history instead of rewriting it
  - serialize deterministically (stable key order in JSON)
  - do not add or remove tools mid-run; if some tools must be off, mask or refuse them instead
- **Just-in-time context:** give the model ways to fetch what it needs (search, read by ID)
  instead of dumping everything up front.
- **Compaction policy:** decide when to summarise (for example at 70% of the window) and what
  must survive (the goal, decisions, open items, key identifiers). Rules that must never be lost
  live in the system prompt or an instructions file, not in the conversation.
- **Notes outside the context:** a progress file, a to-do list or a memory store the agent
  writes to and re-reads.
- **Helper agents for exploration:** they work in their own context and return a short summary,
  keeping the main context clean.

## 4. Long-running work

For tasks that span many context windows or sessions (Anthropic's long-running harness):

- An initialising step writes a **feature list as JSON** (models tend to rewrite Markdown lists),
  a **progress file**, and a first checkpoint or commit.
- Every later session starts by reading the progress file, the feature list and recent history,
  makes **one** increment, verifies it, records it, and leaves the environment clean.

Agent Forge itself works this way through `forge/state.json` and `forge/progress.md`.

## 5. Verification built into the loop

The agent should check its own work before reporting it:

- schema or type validation of structured outputs
- deterministic validators (totals add up, citations resolve, required fields present)
- running tests when the agent produces code
- a reviewer with a fresh context (evaluator-optimizer) for high-stakes outputs

## 6. Errors

Put tool errors back into the context in compact form so the model can correct itself. Escalate
after repeated failure (section 1). Never swallow an error silently.

## 7. Memory

- **Short-term:** the run's own state and history.
- **Long-term:** a store for facts that should persist across runs. Record where each memory
  came from, validate what gets written, and let a human review and delete entries. Long-term
  memory is a poisoning target (see `security.md`).

## 8. Models and configuration

- One module makes all model calls; model IDs come from configuration.
- Different models per role (see `shape-ladder.md`), with a fallback model for outages.
- Every secret comes from the environment or a secret manager. `.env.example` lists every
  variable with a comment and no real values.
- Budgets, step limits and feature flags (including the kill switch) are configuration, not
  constants buried in code.
