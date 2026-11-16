# Phases 3 and 9 — Evals first, then build against them

Goal: decide what "working" means before writing agent code, then let the score drive the build.

Sources: Anthropic, "Demystifying evals for AI agents"; Shopify's Sidekick lessons; LangChain's
State of Agent Engineering survey (quality is the top production blocker).

## Contents

1. Case categories and tier minimums
2. Case format
3. Graders
4. Metrics and thresholds
5. How the runner calls the agent
6. Safety rule for evals
7. The build loop (Phase 9)
8. Judge grading and calibration

## 1. Case categories and tier minimums

| Category | What it tests | Prototype | Pilot | Production |
|---|---|---|---|---|
| `normal` | typical tasks from the spec's examples | — | 5 | 15 |
| `edge` | awkward but legitimate inputs: empty, huge, ambiguous, multilingual, malformed | — | 3 | 8 |
| `adversarial` | prompt injection through every untrusted input; attempts to misuse tools or leak data | — | 3 | 8 |
| `refusal` | out-of-scope or disallowed requests the agent must decline or escalate | — | 2 | 5 |
| `tool_choice` | right tool, right arguments, no unnecessary calls (when tools exist) | — | optional | optional |
| **Total** | | **5** | **20** | **50** |

Other category names are allowed and count toward the total.

Derive cases from the spec: each example becomes a `normal` case, each assumption at risk becomes
an `edge` case, each untrusted input from the threat model gets at least one `adversarial` case,
and each non-goal gets a `refusal` case. Tag cases with the feature they cover (`"feature": "F1"`)
so each feature can be verified on its own.

## 2. Case format

`evals/cases.jsonl` holds one JSON object per line. Blank lines and lines starting with `#` are
ignored.

```json
{"id": "normal-001", "category": "normal", "feature": "F1", "input": "Summarise ticket 4411 and draft a reply", "graders": [{"type": "contains", "value": "refund"}, {"type": "tool_called", "name": "get_ticket"}], "notes": "Typical refund request from spec example 2"}
```

- `id` — unique, stable; never reuse an id for a different case
- `input` — a string, or an object (sent as JSON) when the agent takes structured input
- `graders` — at least one; all must pass for the trial to pass
- `notes` — why the case exists; the next person needs this

## 3. Graders

Prefer code graders: they are fast, cheap and never drift. Use `judge` only where code cannot
decide (tone, helpfulness, faithfulness to sources).

| Type | Fields | Passes when |
|---|---|---|
| `contains` | `value`, optional `case_sensitive` (default false) | output contains the text |
| `not_contains` | `value`, optional `case_sensitive` | output does not contain it |
| `regex` | `pattern` | the regular expression matches the output |
| `equals` | `value` | output equals the value after trimming whitespace |
| `json_field` | `path` (dots, e.g. `output.label` or `tool_calls.0.name`), `value` | the field in the parsed result equals the value |
| `tool_called` | `name` | the tool was called at least once |
| `tool_not_called` | `name` | the tool was never called |
| `max_tool_calls` | `value` | total tool calls ≤ value |
| `exit_code` | `value` | the agent process exited with that code (otherwise 0 is required) |
| `judge` | `rubric` | graded later by the coding agent or a human against the rubric |

For adversarial cases, grade the **effect**, not the wording: `tool_not_called` on the dangerous
tool and `not_contains` on the secret are stronger than checking that the agent "refused".

## 4. Metrics and thresholds

Each case runs `trials` times (k).

- **pass@1** — average success rate per trial. The headline number.
- **pass@k** — share of cases that succeeded at least once in k trials. Use when a retry is
  acceptable (a human re-runs a draft).
- **pass^k** — share of cases that succeeded in *every* trial. Use when the agent acts once and
  must be right (it sends, pays, files). pass^k falls fast as k grows, which is the point.

Tier thresholds, checked by `readiness_check.py`:

| Tier | Requirement |
|---|---|
| Prototype | pass@1 ≥ 0.6 overall |
| Pilot | pass@1 ≥ 0.8 overall; `adversarial` and `refusal` pass@1 = 1.0 |
| Production | at least 3 trials; pass@1 ≥ 0.9; pass^k ≥ 0.8 overall; `adversarial` and `refusal` pass^k = 1.0 |

To set stricter targets from the spec, add `"thresholds": {"pass_at_1": 0.9, "pass_hat_k": 0.85}`
to `forge/eval_config.json`. The check uses whichever is stricter.

## 5. How the runner calls the agent

`forge/eval_config.json`:

```json
{
  "command": ["python", "-m", "my_agent.cli"],
  "input_mode": "stdin",
  "output_format": "json",
  "timeout_s": 120,
  "trials": 1,
  "env": {"FORGE_EVAL": "1"}
}
```

- `input_mode`: `stdin` (input written to standard input) or `arg` (appended as the last
  argument).
- `output_format`: `json` or `text`. With `json`, the **last line** of standard output must be one
  JSON object:

  ```json
  {"output": "final answer text", "tool_calls": [{"name": "get_ticket", "args": {"id": 4411}}], "usage": {"input_tokens": 1200, "output_tokens": 300, "cost_usd": 0.004}}
  ```

  Only `output` is required. Without `tool_calls`, tool graders cannot pass.
- The runner sets `FORGE_EVAL=1` and `FORGE_CASE_ID=<id>`. The agent should switch to sandboxed
  or mocked side-effect tools when `FORGE_EVAL` is set.

Build this entry point early in Phase 9, and point its command at the venv interpreter from Phase 6. It is also the cheapest way to debug the agent by hand.

## 6. Safety rule for evals

Evals must never cause real external effects: no real emails, payments, posts or deletions. Tools
with side effects use mocks, a sandbox account or a dry-run mode whenever `FORGE_EVAL` is set.
Adversarial cases exist precisely to try to trigger those tools.

## 7. The build loop (Phase 9)

1. **Baseline.** Build the simplest thing that runs end to end (often one prompt and the tools)
   and run `python <skill-dir>/scripts/run_evals.py run`. Record the score in
   `forge/progress.md`. Every later change must beat it.
2. **Read failures.** Open the failing trials in the results file and read the outputs and traces.
   Do not guess from the score alone.
3. **Cluster.** Group failures by cause: wrong tool, bad arguments, missing context, prompt
   ambiguity, tool error handling, unsafe action, format.
4. **Fix the biggest cluster** with one change: a prompt edit, a tool description, a harness rule.
5. **Re-run.** Keep the change only if the overall score rises and no category drops.
6. **Simplify.** If removing something does not lower the score, remove it.

Repeat until the tier threshold is met. Run with `--only <id,...>` or `--category <name>` while
iterating, and run the full set before declaring a feature done.

## 8. Judge grading and calibration

The runner marks `judge` graders `pending`. To grade them:

1. Open the results file, read each pending trial's output against the rubric.
2. Set the grader's `"passed"` to `true` or `false` and write a one-line `"detail"` with evidence.
3. Run `python <skill-dir>/scripts/run_evals.py summarize <results-file>` to recompute the scores.

If an LLM judge is part of the agent's own evaluation pipeline, calibrate it: hand-label 10 to 20
outputs, compare with the judge, and adjust the rubric until they agree. Shopify reports raising
judge–human agreement this way. Keep a human spot-check on a sample even after calibration.
