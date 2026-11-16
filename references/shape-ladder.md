# Phase 2 — Choosing the shape

Goal: the simplest design that can do the job, with the reason for every step up written down.

Sources: Anthropic, "Building effective agents" (workflow patterns); Cognition, "Don't Build
Multi-Agents" and its 2026 follow-up; Anthropic's multi-agent research system; HumanLayer's
12-Factor Agents.

## The ladder

| Rung | What it is | Right when | Typical signal to climb |
|---|---|---|---|
| 1. Single LLM call | One call, maybe with retrieved context, examples and structured output | Classify, extract, summarise, draft from given inputs | It needs information it cannot be given up front |
| 2. Fixed workflow | Code decides the path; LLM calls are steps in it | The steps can be listed in advance | The next step depends on results in ways you cannot enumerate |
| 3. One agent, tool loop | The model chooses tools in a loop until done | Open-ended tasks: investigate, fix, research with feedback | One context cannot hold the needed exploration, or a clean-context check is needed |
| 4. Multiple agents | A lead agent plus helpers | Wide parallel reading or research; independent review | Rarely needed beyond this |

Most production systems are **hybrids**: a workflow on the outside with an agent loop inside one
step. Successful agents are mostly ordinary software with LLM decisions at a few points.

## Workflow patterns (rung 2)

- **Prompt chaining:** fixed sequence of steps, with code checks between them. Use when the task
  splits cleanly.
- **Routing:** classify the input, send it to a specialised path. Use for distinct input types
  (refund vs. bug report).
- **Parallelisation:** split into independent parts (sectioning) or run the same task several
  times and vote. Use for speed or confidence.
- **Orchestrator-workers:** an LLM splits the task at run time and hands parts to workers. Use
  when the subtasks are not known in advance (multi-file changes).
- **Evaluator-optimizer:** one LLM produces, another critiques against criteria, repeat. Use when
  clear criteria exist and iteration measurably helps.

## Rules for multi-agent designs

- **One writer.** Only one agent changes state or produces the final artefact. Helpers search,
  read or review and return a short summary. Parallel writers make conflicting decisions because
  they do not share context.
- **Count the cost.** Anthropic's multi-agent research system used roughly 15× the tokens of a
  normal chat. It paid off for breadth-first research, not for most tasks.
- **Clean-context review works.** A reviewer that starts fresh, without the builder's
  accumulated reasoning, catches more.
- **Pass full context to helpers.** A helper given only a one-line task drifts. Give it the goal,
  constraints and what "done" means.

## Decision questions

Answer these in `docs/design.md`:

1. Can the steps be listed in advance? If yes, rung 1 or 2.
2. Does the next step depend on tool results in ways you cannot predict? If yes, rung 3.
3. Does the task need wide, independent exploration that will not fit one context? Only then
   consider rung 4.
4. Would a clean-context second opinion measurably improve results? That is an evaluator or
   reviewer, not a swarm.
5. What does each rung cost per task in tokens and seconds? Estimate it.

## Models per role

Use a strong model where judgement matters (the lead, the planner, the judge) and a cheaper,
faster one for routine steps (classification, extraction, helper searches). Keep model IDs in
configuration. If the user requires local models, check the shape still works at that capability
level: small local models handle rung 1–2 far better than open-ended tool loops.

## What to write

In `docs/design.md`, section *Shape*:

- the chosen rung (and pattern, if a workflow)
- for each lower rung, one or two sentences on why it fails, pointing at the spec or examples
- models per role
- a cost and latency estimate per task
