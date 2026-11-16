# Phases

The build plan for agent-forge itself (not the phases the skill walks through; those are in
`SKILL.md` and `architecture.md`).

| Phase | Produces | Done means | Status |
|---|---|---|---|
| 0. Research and design | `research.md`, `agent-lifecycle.md`, `design.md`, `architecture.md` | approach agreed | **Done** (Nov 2026) |
| 1. Write the skill (v0) | `SKILL.md`, 11 references, 10 templates, 4 scripts, 3 draft test cases | all files written | **Done** (Nov 2026) |
| 2. Smoke-test the scripts | each script run on a scratch project | scripts run without errors and report sensibly | **Partly done**: `forge.py init/status/advance`, `run_evals.py validate` and the gate ran cleanly. `setup_env.py` did not finish its first run and needs a re-test. Not yet exercised: `run_evals.py run/summarize`, `approve`/`goto`, pilot and production checks |
| 3. Test the skill on real agent ideas | test cases per idea; runs with and without the skill | results reviewed | Not started |
| 4. Iterate | revised skill from test feedback | feedback addressed; no regressions | Not started |
| 5. Description tuning | trigger eval set and an optimised description | triggers on agent-building requests, not on near-misses | Not started |
| 6. Release | installed and checked in Claude Code and Codex; packaged | works from a fresh session | Not started |
