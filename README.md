# agent-forge

A skill for coding agents (Claude Code, Codex and others) that turns a project idea into an
end-to-end AI agent at a chosen readiness tier — **prototype, pilot or production** — by going
through a spec, a design, evals, a threat model, a pinned environment and a readiness gate
instead of jumping straight to code.

> **Status: v0, early.** The scripts are partly smoke-tested and the skill has not yet been
> evaluated on real agent ideas. Expect changes.

## What it does

The coding agent takes the idea through eleven phases, with three human checkpoints:

| # | Phase | Output |
|---|---|---|
| 1 | Intake and spec | `docs/spec.md` (at most five questions, each with a default) — **checkpoint** |
| 2 | Shape | simplest design that works: single call → workflow → agent → multi-agent |
| 3 | Evals first | test cases written before any code |
| 4 | Threat model | every tool classified; Rule of Two enforced |
| 5 | Framework | chosen by the skill, checked against current docs — **checkpoint** |
| 6 | Environment setup | pinned requirements, `.venv`, lock file, smoke call to the model |
| 7 | Tools | small, well-described, tested tools |
| 8 | Harness | loop, state, context, verification |
| 9 | Build against evals | baseline, then fix failure clusters one change at a time |
| 10 | Observability and ops | tracing, limits, red-team pass |
| 11 | Gate and handover | readiness report, AGENTS.md, rollout plan — **checkpoint** |

## Layout

| Path | What it is |
|---|---|
| [SKILL.md](SKILL.md) | the skill: trigger description, principles, phase flow |
| [references/](references/) | one guide per phase, read only when that phase is reached |
| [assets/templates/](assets/templates/) | files copied into the agent project being built |
| [scripts/](scripts/) | `forge.py`, `setup_env.py`, `run_evals.py`, `readiness_check.py` (Python 3.9+, standard library only) |
| [evals/](evals/) | test cases for the skill itself |
| [docs/](docs/) | research, design, architecture and build log for the skill |

## Install

Copy or clone this folder into your coding agent's skills directory, keeping the folder name
`agent-forge`. For Claude Code that is `~/.claude/skills/agent-forge/` (personal) or
`.claude/skills/agent-forge/` inside a project. For other agents, see their documentation on
Agent Skills.

```bash
git clone https://github.com/yuvrajghag5/Agent-Forge.git ~/.claude/skills/agent-forge
```

Then ask your coding agent to build an agent, for example "build me an agent that triages our
support tickets". The skill starts with a few questions.

## Docs

| Doc | Read it for |
|---|---|
| [docs/research.md](docs/research.md) | how production agents are built: types, approach, decisions, sources |
| [docs/agent-lifecycle.md](docs/agent-lifecycle.md) | the lifecycle for building any agent, phase by phase |
| [docs/design.md](docs/design.md) | the problems the skill addresses and the decisions behind it |
| [docs/architecture.md](docs/architecture.md) | layouts, phase flow, interfaces, gate thresholds |
| [docs/phase.md](docs/phase.md) | build plan and status |
| [docs/tech.md](docs/tech.md) | technology choices |
| [docs/changes.md](docs/changes.md) | build log |

## License

MIT — see [LICENSE](LICENSE).
