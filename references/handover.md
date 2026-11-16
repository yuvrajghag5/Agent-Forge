# Phase 11b — Handover, rollout and operating loop

Goal: someone else (a person or another coding agent) can run, maintain and improve the agent
without you.

## 1. README

How to set up, configure (every environment variable, pointing at `.env.example`), run, and run
the evals. Test it against a fresh checkout if you can.

## 2. AGENTS.md

Instructions for any coding agent that works on this repository later (Claude Code, Codex and
others read `AGENTS.md`). Fill in the template; the essentials:

- what the agent does, in two sentences, and where the spec lives
- how to run the tests and the evals, and the score the agent currently holds
- rules: no prompt, model or tool change without running the evals; no new tool without a
  side-effect class in `forge/tools.json`; never weaken an approval step to pass a test
- where traces and logs go

## 3. docs/rollout.md

Autonomy is earned with data, in stages. Write the plan with concrete exit criteria:

| Stage | What happens | Typical exit criteria |
|---|---|---|
| 1. Shadow | the agent runs on real inputs; nobody acts on its output; outputs are compared with what humans did | agreement with humans ≥ target on N real cases |
| 2. Assistive | a human approves every action | approval rate ≥ target; zero critical incidents over N days |
| 3. Partial autonomy | low-risk actions run alone; high-risk still need approval | error rate within budget; incidents reviewed |
| 4. Wider rollout | more users or more action types | per the owner's agreement |

Before every change ships, test it against conversations or cases built from real ones
(Shopify does this with simulated merchant conversations).

Add the **operating loop**:

- each week (or at a set volume), sample production traces, label them, and add every failure
  as an eval case
- when the model or provider changes, re-run all evals, and re-calibrate any LLM judge
- review cost and latency trends monthly
- simplify: better models make parts of the harness unnecessary; remove what no longer moves the
  score

And a **`## Runbook`** section: how to disable the agent (kill switch), roll back a prompt or model
change, rotate credentials, and handle an incident (who is told, what is logged).

## 4. The handover message

End with this report to the user:

```
## <agent name> — handover

**Verdict:** <tier> gate PASSED / NOT PASSED

**What it does:** <one sentence>

**Design:** <shape> on <framework vX.Y>, models <...>. Why: <one line>.

**Scores:** pass@1 <x> over <n> cases (<k> trials); adversarial <x>; refusal <x>. Baseline was <x>.

**Safety:** <Rule of Two status>; approvals on <tools>; credentials <how held>.

**Not verified:** <honest list>

**Needs your decision:** <checkpoints auto-approved, open questions>

**Next steps:** <rollout stage 1 plan, known gaps>

**Files:** spec, design, threat model, READINESS.md, rollout.md, AGENTS.md
```

Keep it short. The files hold the detail.
