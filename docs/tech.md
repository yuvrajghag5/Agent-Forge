# Technology choices

## Chosen

| Choice | Reason |
|---|---|
| **Agent Skills format** (`SKILL.md` + `references/` + `scripts/` + `assets/`) | Open standard loaded by Claude Code and Codex; progressive disclosure keeps context small (only the current phase's reference is read). |
| **Python 3.9+, standard library only** for the skill's scripts | Runs anywhere Python exists, with nothing to install; behaves the same under any coding agent. |
| **JSON / JSONL** for machine-read files (`state.json`, `tools.json`, `eval_config.json`, `cases.jsonl`) | Parsable with the standard library (YAML needs a package). JSON lists are also less likely to be rewritten by a model than Markdown lists. |
| **Markdown** for human-facing docs (spec, design, threat model, rollout, READINESS) | Readable and diffable; `TODO(forge)` markers let the gate check completeness. |
| **Framework chosen by the skill per project** | Any framework is possible; `references/frameworks.md` gives the procedure, an options table and defaults, and requires checking current docs before coding. |
| **Pilot as the default tier** | Serious enough for real users at small scale without enterprise overhead. |
| **Per-project `.venv` with `==`-pinned requirements and a generated lock file** (target agents) | Reproducible builds; the lock file feeds the container; `pip check` and a smoke call catch environment problems before the build. Standard `venv` + `pip` works everywhere; projects already on uv, Poetry or PDM keep their tool. |
| **`claude plugin eval` case layout** for the skill's own tests | Plain files that can be run by subagents or by the Claude Code CLI. |

## Deliberately not used

| Not used | Why |
|---|---|
| Fixed "stack packs" per framework | They go stale, and any framework should be possible. |
| Hard-coded framework API examples | APIs change every few months; the skill requires checking current docs instead. |
| Multi-agent by default | Over-engineering; only reachable through the shape ladder with the one-writer rule. |
| Claude-only features as requirements (subagents, hooks) | Would break portability to Codex and others. |
| A vendor eval or tracing platform | Lock-in; a small JSONL runner and OpenTelemetry-compatible tracing are enough. |
| Third-party Python packages in the scripts | Install friction; the standard library covers it. |
