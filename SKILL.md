---
name: agent-forge
description: Builds production-grade AI agents end to end from a project idea. Turns the idea into a spec, picks the simplest design that works (single LLM call, workflow, single agent or multi-agent), chooses the best-suited framework itself, writes evals before code, threat-models every tool, sets up an isolated virtual environment pinned to the approved stack, then builds, verifies and hands over an agent that passes a readiness gate (prototype, pilot or production), and finally gives it a distinctive, safe web interface designed around what the agent does. Use this skill whenever the user wants to build, create, design, plan or scaffold an AI agent, agentic system, LLM-powered assistant, copilot or chatbot that uses tools, a multi-agent system, or any automation where an LLM decides or takes actions, even if they describe the idea in one line ("an agent that triages my support tickets", "build me a research bot") and never say "agent". Also use it to take an existing agent prototype to production (evals, guardrails, tracing, durability). Do not use it for operating an existing agent, apps with no LLM in them, or training ML models.
---

# Agent Forge

Turn an idea into an agent that demonstrably works, is safe to run, and can be operated.

## Why this skill exists

Coding agents asked to "build an agent" fail in three predictable ways: they guess requirements
silently, they over-engineer (multi-agent graphs where a fixed workflow would do), and they call
the work done when the code only *looks* done. Industry practice points the other way:

- Most of an agent's reliability comes from the **harness** around the model — tools, context,
  state, permissions, checks — not from clever prompts or many agents.
- The **simplest design that works** wins on cost, latency and debuggability.
- Nothing counts as working until **evals** say so, measured against a baseline.
- Prompt injection is not solved, so **security is designed in**, by limiting what each session
  can reach and do, not bolted on later.

This skill turns that into twelve phases. Each phase produces a file and passes a gate, so the work
can be checked, resumed in a later session, and trusted.

## Principles to hold throughout

1. **Spec before code.** Every guess is written down as a labelled assumption the user can correct.
2. **Climb, don't leap.** Start at the simplest design; every step up needs a written reason.
3. **A number decides "done".** Eval pass rates against the tier's threshold, not appearance.
4. **Classify before you build.** Every tool gets a side-effect class and a control before it exists.
5. **Read traces, change one thing at a time.** Fix the largest failure cluster first.
6. **Earn autonomy.** Humans approve risky actions until the data says otherwise.
7. **Be honest in the handover.** Report what passed, what did not, and what was never verified.

## Getting oriented (every session)

1. **Ask for the trusted workspace — every time the skill is used.** Before anything else, ask
   the user which folder is the trusted workspace for this project, for example:
   *"Which folder should I use as the trusted workspace for this agent? Everything I create —
   code, docs, the virtual environment, eval runs — will stay inside it. (default: a new folder
   `<agent-slug>` inside the current folder)"*.
   Building an agent means creating files, installing packages and running code; one explicit
   folder keeps that work away from unrelated files and makes every action easy to review.
   From then on, create, edit, install and run things **only inside that folder**. If something
   outside it is needed (a dataset, an existing codebase, a system-wide install), ask first.
   Ask this together with the intake questions if there are any; it does not count toward
   their limit of five. If the user already named the folder in their request, confirm it
   instead of asking again.
2. **Resuming?** If `forge/state.json` exists in the workspace, read it and `forge/progress.md`
   first and continue at the recorded phase. Show the user the workspace recorded there and
   confirm it is still the one to use. Never restart a project that is in progress.
3. **New project:** create the layout and state file inside the workspace:
   `python <skill-dir>/scripts/forge.py init --project <workspace> --name <agent-slug> --tier <tier> --mode <mode>`
   (`<skill-dir>` is the folder this SKILL.md is in; use `py` instead of `python` on Windows if
   needed). It records the workspace's absolute path in `forge/state.json` and copies templates
   without overwriting existing files.
4. **Execution mode — who runs code.** Default `agent_runs`. If the user, or their instruction
   files (CLAUDE.md, AGENTS.md, saved memories), say they run code themselves, use
   `human_runs`: write the exact command, stop, and wait for them to paste the output before
   continuing. This applies to the skill's own scripts too.
5. **Tier.** Use the tier the user names. Otherwise default to **pilot** and record it as an
   assumption. Tiers are defined in `references/readiness-gate.md`.
6. At the end of every working session, append an entry to `forge/progress.md` (what was done,
   what is next, open issues) and update `forge/state.json`. The next session depends on it.

Scripts are Python 3.9+ with the standard library only, so they run anywhere the user has Python.
`python <skill-dir>/scripts/forge.py status` shows where the project stands.

## Project layout this skill creates

All of it lives inside the trusted workspace the user chose.

```
<workspace>/
  docs/spec.md            what the agent does, for whom, assumptions, v1 scope
  docs/design.md          shape, framework, harness decisions and their reasons
  docs/threat-model.md    data, inputs, tool classes, Rule of Two, controls
  docs/rollout.md         staged rollout, operating loop, runbook
  forge/state.json        phase, checkpoints, decisions, feature list (machine-read)
  forge/progress.md       session log for resuming
  forge/tools.json        tool manifest: side-effect class, timeout, approval
  forge/eval_config.json  how the eval runner invokes the agent
  forge/environment.json  interpreter, venv and lock-file details (written in Phase 6)
  evals/cases.jsonl       eval cases; evals/results/ holds runs
  .venv/                  isolated environment for the chosen stack (git-ignored)
  requirements.txt        pinned direct dependencies (+ requirements-dev.txt)
  requirements.lock.txt   full pinned environment, generated
  .env.example            every variable the agent needs, no values
  AGENTS.md               how any coding agent should maintain this agent
  READINESS.md            readiness gate report
  docs/frontend.md        interface plan, critique and result (Phase 12)
  src/ ...                the agent itself (layout depends on the framework), including its UI
```

## The phases

| # | Phase | Read first | Produces | Gate |
|---|---|---|---|---|
| 1 | Intake and spec | `references/intake.md` | `docs/spec.md` | **Checkpoint 1: user approves spec** |
| 2 | Shape | `references/shape-ladder.md` | `docs/design.md` (shape) | No simpler rung would work |
| 3 | Evals first | `references/evals.md` | `evals/cases.jsonl`, `forge/eval_config.json` | Tier's case minimums met |
| 4 | Threat model | `references/security.md` | `docs/threat-model.md`, `forge/tools.json` | Every tool classified; Rule of Two holds |
| 5 | Framework | `references/frameworks.md` | `docs/design.md` (framework) | **Checkpoint 2: user approves design** |
| 6 | Environment setup | `references/environment.md` | `.venv/`, pinned requirements, lock file, `.env.example` | Installs cleanly; smoke call to the model works |
| 7 | Tools | `references/tools.md` | tool code + tests | Tools pass their own tests |
| 8 | Harness | `references/harness.md` | loop, context, state code | Survives kill and resume |
| 9 | Build against evals | `references/evals.md` (loop section) | working agent, eval results | Tier threshold reached |
| 10 | Observability and ops | `references/ops.md` | tracing, limits, red-team fixes | Any run explainable from its trace |
| 11 | Gate and handover | `references/readiness-gate.md`, `references/handover.md` | `READINESS.md`, `AGENTS.md`, `docs/rollout.md`, README | **Checkpoint 3: user accepts** |
| 12 | Frontend | `references/frontend.md` | web interface, `docs/frontend.md` | **Checkpoint 4: user accepts the interface** |

Read each reference when you reach its phase, not before; they are long and only one is needed at
a time. Advance with `python <skill-dir>/scripts/forge.py advance`, which refuses to pass a
checkpoint the user has not approved.

### 1. Intake and spec

Turn the idea into `docs/spec.md`. First check the idea deserves an agent at all: if the task is
deterministic, say so and propose plain code, possibly with one LLM call. That is a successful
outcome, not a failure.

When information is thin, **ask**, but ask well. Send at most five questions, in one batch. Only
ask the ones whose answer would change the architecture or the safety design, and give a
suggested default with each so the user can simply reply "defaults are fine". Everything else
gets a sensible default, written into the spec as a labelled assumption. Collect real examples of
the task; if the user has none, write realistic ones and mark them synthetic. They become eval
seeds.

Present the spec summary (the job, v1 scope, assumptions, open questions) and stop for
approval. Record it with `forge.py approve spec`. Approval costs the user a minute now, and a
wrong spec costs a rebuild later.

### 2. Shape

Choose the lowest rung on the ladder that can do the job: single LLM call → fixed workflow
(chain, routing, parallel, orchestrator-workers, evaluator-optimizer) → one agent in a tool loop
→ multiple agents. For each rung below the chosen one, write *concretely* why it fails, pointing
at the spec. If you go multi-agent, only one agent writes or acts; the others read, search or
review. Choose models per role.

### 3. Evals first

Write the eval cases before any agent code, derived from the spec and its examples. Categories:
`normal`, `edge`, `adversarial` (prompt injection through every untrusted input), `refusal`
(out-of-scope or disallowed), and `tool_choice` when tools exist. Prefer code-checkable graders;
use `judge` graders with a written rubric only where code cannot decide. Choose the metric from
the spec: pass@k if a retry is acceptable, pass^k if it is not. Check the file with
`python <skill-dir>/scripts/run_evals.py validate`. Fill in `forge/eval_config.json` once you know
how the agent will be invoked (Phase 5).

### 4. Threat model

List what private data the agent can reach, which inputs are untrusted, and every tool with its
side-effect class (`read_only`, `reversible_write`, `irreversible`, `external_comm`). Apply the
**Rule of Two**: in one session the agent may combine at most two of private data, untrusted
input, and the ability to change state or send data out, unless a human approves each such
action. Decide the controls: least-privilege credentials kept out of the model's context, a
sandbox for code execution, approval on irreversible and external actions, untrusted content
treated as data. Record tools in `forge/tools.json`. Add the attacks you identify as adversarial
eval cases.

### 5. Framework

Choose the framework yourself, from the design's needs and the user's constraints. Prefer the
lightest option that meets the needs: plain code for single calls and workflows, a framework when
durability, human-approval pauses, multi-agent coordination or a specific runtime demand it.
If the deciding facts are unknown (usually the language, where it runs, and which model provider
is allowed), ask; otherwise decide. Compare at least two candidates in `docs/design.md` and name
the rejected ones with reasons. **Check current documentation before writing code**: agent
frameworks change their APIs every few months, so look up the latest stable version and its
quickstart, and pin the version. Do not write framework calls from memory.

Present the design (shape, framework, threat model, eval plan) and stop for approval
(`forge.py approve design`). This is the last cheap moment to change direction.

### 6. Environment setup

Once the user has approved the design, and **before writing any agent code**, build an isolated
environment for the approved stack. Choose an interpreter version that every package supports,
pin each direct dependency in `requirements.txt` to the version you verified in Phase 5 (test
tools go in `requirements-dev.txt`), then run
`python <skill-dir>/scripts/setup_env.py --python <path-to-interpreter>`. It creates `.venv/`,
installs, runs `pip check`, writes `requirements.lock.txt` and `forge/environment.json`, and
git-ignores `.venv/` and `.env`. Never install into the global Python.

Then list every secret and setting in `.env.example` (the user fills in `.env`; never ask for keys
in chat) and prove the stack works with a small smoke command: import the key packages and make
one tiny call to the model. From here on, run everything, including the evals, with the venv's
interpreter. Environment problems found now cost minutes; found during the build they cost
hours. For stacks other than Python, follow the equivalent steps in the reference.

### 7. Tools

Build a small set of tools shaped around the user's tasks, not one per API endpoint. Write names
and descriptions for the model. Validate inputs, keep outputs short (paginate or truncate with a
hint), return errors that say how to fix the call, set timeouts, and make writes safe to repeat.
Wrap every tool whose class requires approval in an approval step. Unit-test each tool with mocks;
evals must never trigger real external effects.

### 8. Harness

Build the loop as gather → act → verify, with explicit stop conditions: a final answer, a maximum
number of steps, and token, cost and time budgets, plus an escalation when the same error
repeats. Keep run state as serializable data so a run can pause for approval and resume after a
crash. Engineer the context: a stable prompt prefix (cache-friendly), append-only history, no
tool-list changes mid-run, a compaction policy, notes kept outside the context, and helper agents
that return short summaries. Put every model call behind one module so the provider is a
configuration choice. Build in verification: schema checks, validators, tests, or a fresh-context
reviewer for high-stakes output.

### 9. Build against the evals

First get the simplest possible version running and measure the **baseline**:
`python <skill-dir>/scripts/run_evals.py run`. Then loop: run the evals → read the traces of
failures → group failures by cause → fix the largest group (prompt, tool or harness) → run again.
Change one thing per iteration and record each result in `forge/progress.md`. A drop on any
category blocks the change. Remove anything that does not move the score. Build feature by
feature from the list in `forge/state.json`, finishing and verifying one before starting the
next. If the project uses git and the user allows commits, commit after each verified feature.

Grade `judge` cases yourself (or ask the user) by filling in the pending results, then
`run_evals.py summarize <results-file>`.

### 10. Observability and operations

Trace every run: one span per agent run, model call and tool call, with model, tokens, cost,
latency and errors. Keep content capture off by default. Add timeouts, retries with backoff,
rate limits, fallbacks and a kill switch. Pin model IDs, prompt versions and tool versions, and
record them in traces. Run a red-team pass against every untrusted input channel, fix what
breaks, and add each attack as an eval case.

### 11. Gate and handover

Run `python <skill-dir>/scripts/readiness_check.py`. It checks the machine-checkable items for
the tier and lists the review items you must confirm in `READINESS.md` with evidence. Write
`AGENTS.md`, the README, and `docs/rollout.md` (staged rollout from shadow mode to wider use, the
operating loop, a runbook). Then hand over using the report format in `references/handover.md`.

If the gate does not pass, do not call the agent ready. Report what passed, what failed, and what
it would take to close the gap.

### 12. Frontend

Give the agent an interface designed around what it does, not a generic dashboard. Start from the
agent's subject (its materials, instruments and vocabulary), write a compact plan in
`docs/frontend.md` (a 4–6 colour palette with named hex values, display, body and utility
typefaces, an ASCII wireframe, and one signature element that shows something true about how the
agent works), then critique the plan: anything you would have produced for any agent gets
replaced. Spend the boldness on the signature; keep the rest quiet.

Every agent interface needs: a start action, live progress with readable decisions, the evidence
collected so far, approvals (when the agent has them), the result with its status and limitations,
designed failure and empty states, history, and a clean stop. Treat everything the agent read as
untrusted: escape it, render Markdown safely, set a Content Security Policy, bind local servers to
127.0.0.1 with a host check and a per-start token. Build to the quality floor: works on a phone,
visible keyboard focus, reduced motion respected, meaning never carried by colour alone. Keep
new dependencies to a minimum; any you add follow Phase 6. Show the result to the user and record
acceptance with `forge.py approve ui`.

## When the user is not available

In unattended runs (CI, a background job), do not block at checkpoints forever. Use the current
folder as the workspace and record that as an assumption, proceed with defaults, record
`forge.py approve <checkpoint> --by auto`, and list everything that still needs a human decision
at the top of the final report.

## Taking over an existing prototype

Run `forge.py init` in the existing project (it never overwrites files), write the spec from the
code and the user's description, and start at Phase 1 anyway. Most of the value for a prototype
is in Phases 3, 4, 6, 9 and 10: evals, threat model, a reproducible environment, the measured
build loop, and tracing.
