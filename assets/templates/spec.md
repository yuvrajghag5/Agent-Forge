# {{AGENT_NAME}} — spec

> Created {{DATE}} by agent-forge. Tier: **{{TIER}}**. Remove every `TODO(forge)` marker before
> asking for approval.

## 1. The job

TODO(forge): one sentence — "An agent that <does what> for <whom> so that <outcome>."

## 2. Why an agent (and not plain code)

TODO(forge): what part needs an LLM and why; what stays deterministic code. If plain code would do,
say so here.

## 3. Users and usage

TODO(forge): who uses it, how (chat UI, API, scheduled job, CLI, inside another tool), how often,
expected volume.

## 4. Inputs and outputs

TODO(forge): what comes in (formats, sources, which are untrusted) and what goes out.

## 5. Systems, data and actions

TODO(forge): systems it reads, systems it changes, private data it can reach. For each action: may it
act alone, or does a human approve?

## 6. Success

TODO(forge): what a good result looks like; target scores; can it retry (pass@k) or must it be right
every time (pass^k)?

### Examples

TODO(forge): real examples (input → good output). Mark any you wrote yourself as **synthetic**.

## 7. Non-goals

TODO(forge): what it must not do or will not handle in v1. Each becomes a refusal eval case.

## 8. Constraints and budgets

TODO(forge): language, where it runs, allowed model providers, cost per task, latency, data residency.

## 9. v1 scope and features

TODO(forge): the smallest end-to-end version, split into features F1, F2, ... (also recorded in
`forge/state.json`). List what is deferred to later.

## 10. Assumptions

TODO(forge): numbered, so the user can say "change 3". Each one a guess made because it was not
specified.

## 11. Open questions

TODO(forge): anything still undecided, or "none".
