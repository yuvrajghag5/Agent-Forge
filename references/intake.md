# Phase 1 — Intake and spec

Goal: turn a one-line idea into `docs/spec.md` that the user approves, without interrogating them.

## 0. The trusted workspace (always)

The first question, every time the skill is used, is where the project lives:

> Which folder should I use as the trusted workspace for this agent? Everything I create —
> code, docs, the virtual environment, eval runs — will stay inside it.
> *(default: a new folder `<agent-slug>` inside the current folder)*

- Ask it in the same message as the blocking questions below; it does not count toward their
  limit of five. If the user already named a folder, confirm it instead.
- Use an absolute path. If the folder does not exist, create it only after the user confirms.
- Run `forge.py init --project <workspace> ...` there; the path is recorded in
  `forge/state.json`.
- From then on, create, edit, install and run things only inside it. Anything outside (an
  existing codebase to integrate, a dataset, a system-wide install) needs the user's OK first.
- If the workspace is inside a git repository, say so; the user may want the agent in its own
  repository.

## 1. Restate the idea

Write one sentence: *"An agent that <does what> for <whom> so that <outcome>."* If you cannot
fill all three blanks, those blanks are your first questions.

## 2. Check that an agent is warranted

Many "agent" ideas are better solved with plain code. Ask yourself:

- Could the steps be written as a fixed script? If yes, most of it should be code; the LLM
  handles only the fuzzy part (classifying, summarising, drafting).
- Is there a measurable benefit (time saved, volume handled, quality) worth the cost and risk?
- Would a wrong answer or a wrong action be cheap to catch?

If plain code or a single LLM call does the job, say so. Recommending less is a good outcome.
Gartner expects over 40% of agentic AI projects to be cancelled by the end of 2027, mostly for
unclear value or cost.

## 3. Separate blocking unknowns from defaultable ones

A question is **blocking** only if its answer changes the architecture or the safety design. Ask
the blocking ones, at most five, in a single message, each with a suggested default. Everything
else gets a default written into the spec as an assumption.

Pick from this bank only what the user has not already answered:

| # | Question | Why it blocks | Suggested default |
|---|---|---|---|
| 1 | How is it used: chat UI, API, scheduled background job, CLI, inside an existing tool (Slack, email, IDE)? | Decides the runtime, state handling and latency budget | CLI plus a Python/TS function API |
| 2 | Which systems and data must it read or act on? Any private or personal data? | Decides tools, credentials and the threat model | Only the systems named in the idea; no personal data stored |
| 3 | What may it do on its own, and what needs a human's OK? Anything irreversible (send, pay, delete, deploy, post)? | Decides approval steps and the Rule of Two | Read freely; every write or outbound message needs approval |
| 4 | What does a good result look like? Two or three real examples, if possible. Can it retry, or must it be right first time? | Defines the evals and the metric (pass@k vs pass^k) | I write realistic examples and mark them synthetic; retries allowed |
| 5 | Constraints: language, where it runs (cloud, on-prem, local), allowed model providers (or local-only), budget per task, speed | Decides the framework and model choice | Python; runs locally or in a container; provider-agnostic; ≤ $0.10 and ≤ 60 s per task |
| 6 | Who uses it and how much: one person, a team, customers? Tasks per day? | Decides scaling, auth and the tier | One team, under 1,000 tasks/day |
| 7 | How production-ready: demo (prototype), real users at small scale (pilot), or others depend on it (production)? | Decides the readiness gate | Pilot |

Write the questions in plain language. Example of a good batch:

> Before I design this, five quick questions. If a default is fine, just say "defaults".
> 1. Where will people use it — Slack, a web page, or a script you run? *(default: a script)*
> 2. Should it only draft replies, or also send them? *(default: draft only; a human sends)*
> ...

If the user cannot or will not answer, proceed on the defaults. The point is to make the guesses
visible, not to block.

## 4. Get examples

Real examples are the most valuable input you can get: each one becomes an eval case. Ask for
them in question 4. If none exist, write 10 to 20 realistic examples yourself, covering typical
and awkward cases, and mark them `synthetic` in the spec.

## 5. Define v1 scope

Big ideas need a first slice. Split the work into **v1** (the smallest version that delivers the
core job end to end) and **later**. Break v1 into features (`F1`, `F2`, ...), each small enough to
build and verify on its own, and record them in `forge/state.json` under `features` with
`"status": "todo"`. Agents that try to build everything at once fail; agents that finish one
verified feature at a time succeed.

## 6. Write the spec

Fill in `docs/spec.md` from the template. Every section must be filled or explicitly marked "not
applicable". Remove all `TODO(forge)` markers; the readiness check looks for them.

Record assumptions and open questions in both `docs/spec.md` and `forge/state.json`.

## 7. Checkpoint 1

Show the user a short summary, not the whole file:

- the one-sentence job and who it is for
- v1 scope and features
- the assumptions you made (numbered, so they can say "change 3")
- open questions, if any
- the tier
- the trusted workspace (absolute path)

Ask for approval. On approval run `forge.py approve spec`. If they change something, update the
spec first, then record approval.
