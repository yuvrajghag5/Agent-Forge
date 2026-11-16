# {{AGENT_NAME}} — design

> Created {{DATE}} by agent-forge. Records the decisions and **why**. Remove every `TODO(forge)`
> marker before asking for approval.

## 1. Shape

TODO(forge): the chosen rung (single call / workflow + pattern / one agent / multi-agent) and,
for each lower rung, why it fails — pointing at the spec or examples.

## 2. Models per role

TODO(forge): which model for which role, why, and the fallback. Model IDs live in configuration.

## 3. Cost and latency estimate

TODO(forge): expected tokens, cost and time per task; how they compare with the spec's budgets.

## 4. Framework

TODO(forge): constraints and needs that drove the choice; shortlist and comparison; the choice with
its pinned version and the docs page checked (with date); rejected options and why; lock-in notes.

## 5. Environment

TODO(forge): interpreter / runtime version and why every package supports it; how the environment
is isolated (`.venv/`); the direct dependencies with a one-line reason each; lock file; result of
the smoke call to the model.

## 6. Tools

TODO(forge): the tools (details in `forge/tools.json`), what each is for, and why the set is this
small.

## 7. Harness

TODO(forge): loop and stop conditions; budgets; state and checkpointing; context strategy
(caching, compaction, notes, helpers); verification steps; memory.

## 8. Evaluation plan

TODO(forge): categories and counts, graders, metric (pass@k or pass^k) and target thresholds,
baseline result once measured.

## 9. Observability

TODO(forge): what is traced, where traces go, content capture policy, key metrics.

## 10. Decision log

| Date | Decision | Why | Alternatives rejected |
|---|---|---|---|
| {{DATE}} | Project started at tier {{TIER}} | | |
