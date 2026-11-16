# AGENTS.md — {{AGENT_NAME}}

Instructions for coding agents (Claude Code, Codex and others) working on this repository.

## What this is

TODO(forge): two sentences on what the agent does. The full spec is `docs/spec.md`; decisions and
their reasons are in `docs/design.md`; risks and controls in `docs/threat-model.md`.

## Run it

TODO(forge): setup, configuration (`.env.example`), and the command to run the agent.

## Test it

TODO(forge): command for the unit tests, and for the evals. Current score: pass@1 ... over ... cases
(see `READINESS.md`).

## Rules

- Run the full eval set before and after any change to prompts, models, tools or the loop. Do not
  merge a change that lowers any category's score.
- Every new tool gets an entry in `forge/tools.json` with a side-effect class, a timeout and an
  approval setting, and is checked against the Rule of Two in `docs/threat-model.md`.
- Never weaken or bypass an approval step to make a test pass.
- Evals must not cause real external effects; side-effect tools use mocks when `FORGE_EVAL` is set.
- Model IDs and prompt files are versioned; record changes in `docs/design.md`'s decision log.
- Work inside the project's `.venv/`; never install into the global Python. A new dependency is
  pinned in `requirements.txt` with a reason, the environment is rebuilt with agent-forge's
  `setup_env.py`, and `requirements.lock.txt` is updated with it.

## Observability

TODO(forge): where traces and logs go and how to find a run.
