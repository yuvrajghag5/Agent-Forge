# Phase 11a — The readiness gate

Goal: a clear, honest verdict on whether the agent meets its tier.

Run `python <skill-dir>/scripts/readiness_check.py` (add `--tier <tier>` to check a different tier
than the one in `forge/state.json`, `--json` for machine output). It writes `forge/readiness.json`
and exits with 0 on pass and 1 on fail.

## Tiers

| Tier | Meant for |
|---|---|
| **Prototype** | demos, hackathons, testing an idea |
| **Pilot** (default) | real users at small scale; a team relies on it with supervision |
| **Production** | others depend on it; it runs without someone watching every run |

Each tier includes everything in the tiers below it.

## Automatic checks

| Tier | Check |
|---|---|
| Prototype | `docs/spec.md`, `docs/design.md`, `README.md`, `evals/cases.jsonl`, `forge/eval_config.json`, `forge/state.json` exist |
| Prototype | no `TODO(forge)` markers left in the spec and design |
| Prototype | spec and design checkpoints recorded as approved |
| Prototype | eval cases are valid (unique IDs, an input, at least one known grader) and meet the tier's counts per category |
| Prototype | a latest eval result exists, has no pending judge grades, and meets the tier's thresholds |
| Prototype | no hard-coded secrets in the project; `.env` is git-ignored if it exists |
| Prototype | environment (Phase 6): Python dependencies declared and pinned with `==`, a lock file present, `.venv/` git-ignored; Node projects have a lock file |
| Pilot | `docs/threat-model.md` and `AGENTS.md` exist without `TODO(forge)` markers |
| Pilot | `forge/tools.json` is valid: every tool has a side-effect class and a timeout; `irreversible` and `external_comm` tools require approval |
| Pilot | the Rule of Two holds, or every state-changing tool requires approval |
| Pilot | `.env.example` exists; automated tests exist |
| Production | a `Dockerfile` or `Containerfile` exists |
| Production | a CI configuration exists and runs the evals |
| Production | `docs/rollout.md` exists without `TODO(forge)` markers and contains a `## Runbook` section |

Case counts and score thresholds per tier are in `evals.md` sections 1 and 4.

The check also warns (without failing) when source files are newer than the latest eval results,
meaning the results may be stale. Re-run the evals before the gate.

## Review checks

Some things a script cannot judge. `READINESS.md` has a checklist per tier. Tick each item with
evidence, for example:

```
- [x] Kill switch tested — evidence: `AGENT_DISABLED=1` run in progress.md, 14 Nov
- [x] N/A: no approval steps (agent is read-only) — see threat-model.md
```

The gate fails while any item for the current tier or below is unticked. Never tick an item you
did not verify. "N/A" with a reason is fine; a false tick is not.

## Reporting

Copy the script's summary into `READINESS.md`, together with:

- the eval scores (overall and per category, with the number of trials)
- what failed and why, with the causes from the failure clusters
- what was never verified (for example, "not load-tested", "approval UI not tested with real
  users")

If the gate fails, say so plainly in the handover and list what would close each gap.
