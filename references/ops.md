# Phase 10 — Observability, operations and red-team

Goal: answer "why did it do that?" for any run, keep it within limits, and break it yourself
before users or attackers do.

Sources: OpenTelemetry GenAI semantic conventions; Anthropic's multi-agent research system
(custom tracing was needed to debug agents); Manus (cache hit rate as a key metric); LangChain
survey (many teams trace, far fewer test).

## 1. Tracing

Trace every run as a tree of spans:

- one span per agent run (the root)
- one per model call: model ID, input and output tokens, cost, latency, finish reason
- one per tool call: tool name, redacted arguments, duration, success or error
- for multi-agent designs, helper runs as child spans of the step that started them

Use the **OpenTelemetry GenAI semantic conventions** where the framework supports them (span
operations such as `invoke_agent` and `execute_tool`). They are still marked *Development*, so pin
the version you use. Any OpenTelemetry-compatible backend works; at prototype tier, structured
JSON logs with a run ID are enough.

**Content capture off by default.** Prompts and outputs can contain personal data. Record
metadata always; record content only when explicitly enabled, with redaction, and for a limited
retention period.

Every trace records the versions in use: model IDs, prompt version, tool versions, app version.

## 2. Metrics to watch

| Metric | Why |
|---|---|
| task success (evals, user feedback, approval rate) | the outcome that matters |
| cost per task | budgets drift as prompts and contexts grow |
| latency p50 / p95 | users feel the tail |
| steps per run | rising counts signal loops or confusion |
| tool error rate per tool | bad descriptions or failing backends |
| escalation / approval rate | how much humans still carry |
| prompt cache hit rate | drives cost and latency |

## 3. Reliability

- Timeouts on every model and tool call.
- Retries with exponential backoff and jitter, only for idempotent operations.
- Rate limits per user and globally.
- A fallback model or a graceful "try again later" when the provider is down.
- A **kill switch**: one configuration flag that stops the agent from taking actions (or from
  running at all), tested.
- Circuit breakers on flaky dependencies.

## 4. Version pinning and change control

Pin the model ID (not a moving alias), prompt files, tool definitions and dependencies. Any change
to them goes through the full eval set before release, because model and prompt changes are
behaviour changes even when no code changed.

## 5. Red-team pass

Before real users touch it:

1. For each untrusted input channel in `docs/threat-model.md`, try to:
   - inject instructions that redirect the agent
   - make it call an irreversible or external tool
   - make it reveal private data, including through links or image URLs
   - make it loop or burn budget
2. Try tool misuse with legitimate-looking requests (bulk deletes, sending to new recipients).
3. Try approval fatigue: many similar approval requests in a row.
4. Fix each finding in the design (permissions, Rule of Two, validation), not only in the prompt.
5. Add each attack as an `adversarial` eval case so it stays fixed.

## 6. Deployment basics by tier

- **Prototype:** runs from the README on a fresh machine.
- **Pilot:** container or reproducible environment; configuration through environment
  variables; `.env.example`; health check if it is a service.
- **Production:** container image; CI that runs tests and evals on every change and blocks on
  regressions; secrets from a secret manager; staged rollout (see `handover.md`).
