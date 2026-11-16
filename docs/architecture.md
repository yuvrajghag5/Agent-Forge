# Architecture — how the pieces fit

> Status: **skill v0 written; scripts partly smoke-tested.** See `phase.md` for what has been
> exercised. For the *why* see `design.md`.

## 1. The skill's layout

The repository root is the skill itself.

```
agent-forge/
  README.md                      front door: what is where
  requirements.txt               no dependencies
  docs/                          project write-ups (not used by the skill at run time)
    research.md  agent-lifecycle.md  design.md  architecture.md  phase.md  tech.md  changes.md
  SKILL.md                       trigger description, principles, 11-phase flow, checkpoints
  references/                    loaded one at a time, when the phase is reached
    intake.md                    phase 1: blocking vs defaultable questions, spec, checkpoint 1
    shape-ladder.md              phase 2: single call -> workflow -> agent -> multi-agent
    evals.md                     phases 3 + 9: categories, case format, graders, metrics, build loop
    security.md                  phase 4: tool classes, Rule of Two, OWASP agentic checklist
    frameworks.md                phase 5: selection procedure, options table, defaults
    environment.md               phase 6: interpreter, pinned requirements, venv, smoke check
    tools.md                     phase 7: tool design (agent-computer interface)
    harness.md                   phase 8: loop, state, context engineering, long runs
    ops.md                       phase 10: tracing, metrics, reliability, red-team
    readiness-gate.md            phase 11a: tier checks
    handover.md                  phase 11b: AGENTS.md, rollout plan, handover report
  assets/templates/              copied into the target project by forge.py init
    spec.md  design.md  threat-model.md  rollout.md  progress.md
    AGENTS.md  READINESS.md  tools.json  eval_config.json  cases.jsonl
  scripts/                       Python 3.9+, standard library only
    forge.py                     init | status | approve | advance | goto
    run_evals.py                 run | summarize | validate
    setup_env.py                 phase 6: .venv, install, pip check, lock file, environment.json
    readiness_check.py           tier gate -> forge/readiness.json, exit 0/1
  evals/                         test cases for the skill itself (claude plugin eval layout)
    vague-idea-asks-before-building/
    support-triage-design-choices/
    simple-report-not-an-agent/
```

## 2. Phase flow

| # | Phase | Produces in the target project | Gate |
|---|---|---|---|
| 0 | Trusted workspace (every use) | `forge/state.json` → `workspace` | user named or confirmed the folder |
| 1 | Intake and spec | `docs/spec.md` | **Checkpoint 1: spec approved** |
| 2 | Shape | `docs/design.md` §Shape | no simpler rung works |
| 3 | Evals first | `evals/cases.jsonl` | tier's case minimums |
| 4 | Threat model | `docs/threat-model.md`, `forge/tools.json` | Rule of Two holds |
| 5 | Framework | `docs/design.md` §Framework | **Checkpoint 2: design approved** |
| 6 | Environment setup | `.venv/`, `requirements*.txt`, `requirements.lock.txt`, `.env.example`, `forge/environment.json` | installs cleanly; smoke call to the model works |
| 7 | Tools | tool code + unit tests | tools pass tests |
| 8 | Harness | loop, state, context code | survives kill and resume |
| 9 | Build against evals | agent + `evals/results/` | tier threshold reached |
| 10 | Observability and ops | tracing, limits, red-team fixes | runs explainable |
| 11 | Gate and handover | `READINESS.md`, `AGENTS.md`, `docs/rollout.md` | **Checkpoint 3: accepted** |

`forge.py advance` refuses to leave phases 1, 5 and 11 until the matching checkpoint is approved.

## 3. Target project layout (created by `forge.py init`)

```
<project>/
  docs/spec.md  docs/design.md  docs/threat-model.md  docs/rollout.md
  forge/state.json      phase, checkpoints, decisions, features
  forge/progress.md     session log for resuming
  forge/tools.json      tool manifest (side-effect class, timeout, approval)
  forge/eval_config.json
  forge/readiness.json  written by the gate
  forge/environment.json  written by setup_env.py
  .venv/  requirements.txt  requirements-dev.txt  requirements.lock.txt  .env.example
  evals/cases.jsonl     evals/results/run-*.json, latest.json
  AGENTS.md  READINESS.md  README.md (written by the agent)
  src/...               depends on the chosen framework
```

## 4. Interfaces

**Eval contract.** `run_evals.py` runs `forge/eval_config.json`'s `command` once per case and
trial, passing the input on stdin (or as the last argument), with `FORGE_EVAL=1` and
`FORGE_CASE_ID` set. In `json` mode the last stdout line must be
`{"output": ..., "tool_calls": [{"name", "args"}], "usage": {...}}`. Graders: `contains`,
`not_contains`, `regex`, `equals`, `json_field`, `tool_called`, `tool_not_called`,
`max_tool_calls`, `exit_code`, `judge` (pending until graded, then `summarize`). Metrics: pass@1,
pass@k, pass^k, overall and per category. Partial runs (`--only`, `--category`) never update
`latest.json`.

**Gate.** `readiness_check.py` reads state, cases, `latest.json`, `tools.json` and
`READINESS.md`. Thresholds:

| Tier | Cases (normal / edge / adversarial / refusal) | Scores |
|---|---|---|
| prototype | 5 total | pass@1 ≥ 0.6 |
| pilot | 20 total (5 / 3 / 3 / 2) | pass@1 ≥ 0.8; adversarial and refusal pass@1 = 1.0 |
| production | 50 total (15 / 8 / 8 / 5) | ≥ 3 trials; pass@1 ≥ 0.9; pass^k ≥ 0.8; adversarial and refusal pass^k = 1.0 |

Plus file, checkpoint, secret-scan, environment (pinned deps, lock file, venv ignored),
tool-manifest, Rule-of-Two, tests, container, CI and
review-checklist checks per tier. The same numbers appear in `references/evals.md` and
`references/readiness-gate.md`; keep the three in sync.
