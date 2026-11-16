# Design — what agent-forge is and why

## 1. The goal

A skill that a coding agent (Claude Code, Codex and others) loads so that, from **a project idea**,
it can produce an **end-to-end, production-grade AI agent**, and prove it works.

## 2. The problems a naive version would have

| # | Problem | Why it matters |
|---|---|---|
| P1 | **"One prompt" and "production" pull against each other.** | Production depends on facts only the user knows: what data, which APIs, who the users are, what an action may cost, what must never happen. A prompt does not contain them. If the skill guesses silently, the agent is production-shaped but wrong. |
| P2 | **Coding agents say "done" when it only looks done.** | The main failure of generated projects is code that has never been shown to do the task. Without evals, "production-grade" is a claim, not a property. |
| P3 | **Over-engineering by default.** | Asked to "build an agent", models reach for multi-agent graphs. Most ideas are better as a workflow or a single agent with a few tools. Extra agents add cost, latency and failure modes. |
| P4 | **Framework churn.** | Agent SDKs change their APIs every few months. A skill that hard-codes API calls is out of date by the time it is shared. |
| P5 | **Tools are an attack surface.** | An agent that reads web pages or email and can call tools is open to prompt injection. "Production" without a threat model is unsafe. |
| P6 | **Broken environments.** | Unpinned dependencies, the wrong interpreter version or a missing key surface late, in the middle of the build, where they are expensive to diagnose. |
| P7 | **Context budget.** | One giant instruction file would eat the coding agent's context before it writes a line. |
| P8 | **The space is crowded.** | Spec-driven kits and framework starters already exist. Generic scaffolding is not a reason for this to exist. |

## 3. Key decisions

### D1. Idea → spec → code, never idea → code  *(P1)*
The first job is to turn the idea into a spec: goal, users, inputs, tools, side effects, success
criteria, non-goals, budgets, deployment target. The skill asks **at most five blocking
questions**, each with a suggested default; every other guess is written into the spec as a
labelled assumption. The spec is the **first human checkpoint**.

### D2. The simplest shape that works  *(P3)*
Before any framework, the skill picks a shape from a ladder and writes down why each lower rung
is not enough: single LLM call → fixed workflow → one agent with tools → multiple agents. If
several agents are used, only one writes or acts.

### D3. "Production" is a gate with tiers  *(P2)*
Three tiers — **prototype, pilot (default), production** — each with case counts, score
thresholds and checklists. Part of the gate is machine-checked by `readiness_check.py`; the rest
is a review checklist that must be ticked with evidence.

### D4. Evals before code  *(P2)*
Eval cases (normal, edge, adversarial, refusal, tool choice) are written from the spec before any
agent code. The build loop is: baseline → run evals → read failing traces → fix the largest
failure cluster → re-run. Metrics: pass@1, pass@k, and pass^k for agents that act once and must
be right.

### D5. Threat model as a design step  *(P5)*
Every tool gets a side-effect class (read-only, reversible write, irreversible, external
communication) and a control. The **Rule of Two** is enforced: one session may combine at most two
of private data, untrusted input, and the ability to change state or send data out, unless a human
approves each such action. The gate checks this from `forge/tools.json`.

### D6. The skill chooses the framework  *(P4)*
No fixed framework. The skill selects one per project from the user's constraints (language,
runtime, model provider) and the design's needs (durability, approval pauses, multi-agent, file or
shell access), preferring the lightest option. It asks when the deciding facts are missing,
compares at least two candidates, and **must check current documentation** and record the exact
version before writing code.

### D7. A pinned, isolated environment before any code  *(P6)*
After the user approves the design (stack included) and before any agent code, the skill writes
`==`-pinned requirements, builds a `.venv` with an interpreter every package supports, runs
`pip check`, writes a lock file, lists secrets in `.env.example`, and proves the stack with one
tiny model call (`setup_env.py`).

### D8. Progressive disclosure  *(P7)*
`SKILL.md` holds the phase flow and the rules. Each phase has its own reference file, read only
when that phase is reached. Templates and checks are files and scripts, not prose in context.

### D9. Deterministic work goes in scripts
Project setup, state and checkpoints, environment setup, eval runs and the readiness gate are
standard-library Python scripts, so the skill behaves the same under any coding agent.

### D10. Resumable phases
`forge/state.json` (phase, checkpoints, decisions, feature list) and `forge/progress.md` (session
log) let any later session, or a different coding agent, continue where the last one stopped.
Features are built and verified one at a time.

### D11. Two execution modes
`agent_runs` (default): the coding agent runs commands itself. `human_runs`: it writes each
command, stops, and waits for the user to paste the output. Chosen from the user's instructions.

### D12. Provider-agnostic models
Generated agents call models through one module, so switching provider, or moving to a local
model, is a configuration change checked by the evals.

### D13. A trusted workspace, asked every time
Every use of the skill starts by asking the user which folder is the trusted workspace for the
project (with a default). All files, the virtual environment, eval runs and commands stay inside
it; anything outside needs the user's OK. The path is recorded in `forge/state.json`, confirmed
on resume, and `forge.py status` warns when it is run from a different folder. Building an agent
creates files, installs packages and runs code, so one explicit boundary keeps that work away from
unrelated files and makes each action easy to review.

## 4. What makes it different

Not scaffolding. The value is **agent-specific judgment made repeatable**: the shape ladder
(including when *not* to build an agent), evals before code with a threshold, a tiered gate that
is partly machine-checked, a tool threat model, and a verified environment before the build.

## 5. How it will be validated

Agent ideas of varied difficulty are built **with and without** the skill by the same coding
agent and compared on: gate pass rate at the requested tier, eval pass rate on held-out cases,
over-engineering (shape chosen vs. what a reviewer would choose), and cost and number of human
interventions. The skill's own test cases live in `evals/`.

## 6. Settled choices

| Choice | Decision |
|---|---|
| Name | `agent-forge` |
| Frameworks | any; chosen by the skill per project |
| Default tier | pilot |
| Environment | per-project `.venv`, `==` pins, lock file, smoke call |
| Machine-read files | JSON / JSONL (no third-party packages needed) |
