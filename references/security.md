# Phase 4 — Threat model and permissions

Goal: decide what the agent can reach and do, and how each risk is contained, before any tool
exists. Prompt injection cannot be reliably detected today, so the design must limit the damage a
hijacked agent can do.

Sources: Simon Willison, "the lethal trifecta" (2025); Meta, "Agents Rule of Two" (Oct 2025);
OWASP Top 10 for Agentic Applications (Dec 2025); Anthropic's Managed Agents architecture
(credentials outside the sandbox).

## 1. Inventory

Fill in `docs/threat-model.md`:

- **Private data** the agent can reach (accounts, databases, files, personal data).
- **Untrusted inputs**: anything not written by the operator. Web pages, emails, tickets, user
  uploads, tool outputs from third-party systems, retrieved documents, other agents' messages.
- **Tools** with what each one touches.

## 2. Classify every tool

| Class | Meaning | Required control |
|---|---|---|
| `read_only` | reads, changes nothing | least-privilege credential; output treated as untrusted if it comes from outside |
| `reversible_write` | changes state that can be undone (draft, label, create a branch) | least privilege; logged; undo path documented |
| `irreversible` | cannot be undone (delete, pay, deploy, merge) | **human approval** of the exact action; idempotency key |
| `external_comm` | sends data outside (email, post, webhook, HTTP to arbitrary hosts) | **human approval**; recipient allow-list where possible |

Record each tool in `forge/tools.json`:

```json
{"name": "send_reply", "side_effect": "external_comm", "timeout_s": 30, "requires_approval": true, "idempotent": true, "touches": ["zendesk"], "untrusted_output": false}
```

`readiness_check.py` (pilot and above) fails if an `irreversible` or `external_comm` tool lacks
`requires_approval: true`, or if a tool has no timeout.

## 3. The Rule of Two

The **lethal trifecta**: an agent with (A) access to private data, (B) exposure to untrusted
input, and (C) a way to send data out can be tricked into leaking that data. Meta generalised it
to the **Rule of Two**: in one session, an agent should combine at most two of:

- **A** — access to private or sensitive data or systems
- **B** — processing untrusted input
- **C** — changing state or communicating externally

If all three are needed, every state-changing or outbound action requires human approval, or the
work is split into separate sessions that each hold at most two.

Record A, B and C in `forge/tools.json` under `agent_properties`. The readiness check derives C
from the tools as well (any tool that is not `read_only`), and when A, B and C all hold it
requires approval on every non-read-only tool.

Common ways to satisfy the rule:

- **Split sessions:** a reader session processes untrusted content with no write tools and returns
  structured data; an actor session acts on that structured data and never sees the raw content.
- **Drop C:** draft-only agents; a human sends.
- **Drop A:** the session that browses the web holds no credentials.

## 4. Controls

- **Credentials:** least privilege, scoped to the task, never placed in the prompt or context.
  Where possible a proxy outside the sandbox adds credentials to outgoing calls, so the agent
  never holds them.
- **Sandbox:** any code the agent writes or runs executes in a sandbox with limited filesystem,
  CPU, time, and network egress restricted to an allow-list.
- **Approval design:** show the human exactly what will happen (recipient, amount, diff); bind
  the approval to those exact arguments; default to deny on timeout; log who approved what.
- **Untrusted content:** wrap it in clear delimiters, label it as data, and never let it choose
  the arguments of high-risk tools without validation against allow-lists or schemas.
- **Memory:** check what gets written to long-term memory; store where each memory came from;
  allow memories to be reviewed and deleted.
- **Outputs:** links and images in output can leak data (an image URL carrying a secret in its
  query string). Restrict or sanitise them when private data is in context.

## 5. OWASP Top 10 for Agentic Applications — checklist

Go through each and write one line in the threat model: does it apply, and what is the control.

- **Agent goal hijack** — injected instructions redirect the agent. *Control:* Rule of Two,
  approvals, untrusted content as data.
- **Tool misuse and exploitation** — legitimate tools used harmfully. *Control:* narrow tools,
  argument validation, approvals.
- **Identity and privilege abuse** — the agent's credentials do more than the task needs.
  *Control:* scoped credentials, per-user delegation.
- **Unexpected code execution** — generated code or commands run unsafely. *Control:* sandbox,
  no shell tools unless required.
- **Insecure inter-agent communication** — messages between agents are trusted blindly.
  *Control:* treat other agents' outputs as untrusted; authenticate channels.
- **Human-agent trust exploitation** — users rubber-stamp convincing but wrong actions.
  *Control:* clear approval screens, show evidence, rate-limit approvals.
- **Agentic supply chain** — compromised tools, MCP servers, packages or prompts. *Control:*
  pin and review dependencies and MCP servers; least privilege per server.
- **Memory and context poisoning** — malicious content persists and steers later runs.
  *Control:* provenance, validation, reviewable memory.
- **Cascading failures** — one error propagates through steps or agents. *Control:* step limits,
  validation between steps, circuit breakers.
- **Rogue agents** — behaviour drifts outside its mandate. *Control:* monitoring, kill switch,
  budgets.

## 6. Feed the evals

Every untrusted input channel gets at least one `adversarial` eval case that tries to:

- make the agent call a dangerous tool (grade with `tool_not_called`)
- leak private data in the output (grade with `not_contains`)
- abandon its task for the attacker's task

These cases must pass at 100% from pilot tier up.
