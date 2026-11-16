# {{AGENT_NAME}} — threat model

> Created {{DATE}} by agent-forge. Remove every `TODO(forge)` marker when complete.

## 1. Private data and systems (A)

TODO(forge): what sensitive data or systems the agent can reach, and with which credentials.

## 2. Untrusted inputs (B)

TODO(forge): every channel where content not written by the operator enters: web pages, emails,
tickets, uploads, third-party tool outputs, retrieved documents, other agents.

## 3. Tools

| Tool | Class | Touches | Approval | Control |
|---|---|---|---|---|
| TODO(forge) | read_only / reversible_write / irreversible / external_comm | | yes / no | |

The machine-readable version is `forge/tools.json`; keep both in sync.

## 4. Rule of Two

TODO(forge): does one session combine A (private data), B (untrusted input) and C (state change or
outbound communication)? If yes, how it is contained: approvals on every C action, split sessions,
or dropping one property.

## 5. Controls

TODO(forge): credentials (scope, where held), sandbox, approval design, handling of untrusted
content, memory safeguards, output restrictions (links, images).

## 6. OWASP Agentic Top 10

| Risk | Applies? | Control |
|---|---|---|
| Agent goal hijack | TODO(forge) | |
| Tool misuse and exploitation | | |
| Identity and privilege abuse | | |
| Unexpected code execution | | |
| Insecure inter-agent communication | | |
| Human-agent trust exploitation | | |
| Agentic supply chain | | |
| Memory and context poisoning | | |
| Cascading failures | | |
| Rogue agents | | |

## 7. Adversarial eval cases

TODO(forge): list the attack cases added to `evals/cases.jsonl` (IDs) per untrusted channel.

## 8. Red-team findings

TODO(forge): filled in Phase 10 — what was tried, what broke, how it was fixed, which case covers it.
