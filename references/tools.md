# Phase 7 — Tools

Goal: a small set of tools the model uses reliably. Anthropic calls this the agent–computer
interface: it deserves as much design effort as a human user interface.

Sources: Anthropic, "Writing effective tools for agents" and "Code execution with MCP"; Shopify's
Sidekick lessons (quality fell as tools grew from a handful to dozens).

## 1. Shape tools around tasks

- Build tools for what the user's tasks need, not one per API endpoint. `schedule_meeting` beats
  `list_users` + `list_events` + `create_event`, because each extra call is a chance to go wrong
  and costs context.
- Keep the set small with clear boundaries between tools. Two tools that could both answer a
  request will be confused.
- Namespace related tools (`tickets_search`, `tickets_get`) so the model can tell families apart.

## 2. Write for the model

- The description says what the tool does, **when to use it and when not to**, what each
  argument means with its format, and a short example. Write it like onboarding a new colleague.
- Argument names are unambiguous: `customer_email`, not `user`.
- Use enums and strict schemas wherever the valid values are known.

## 3. Inputs and outputs

- Validate inputs and reject bad ones with a clear message.
- Return only what the next step needs. Prefer readable identifiers and names over opaque IDs
  where the model must reason about them.
- Paginate or truncate large results and say so in the output ("showing 20 of 340; use `page`
  for more").
- Offer a `concise` / `detailed` response option when outputs vary a lot in size.

## 4. Errors that teach

An error should tell the model how to recover: "date must be YYYY-MM-DD, got '12/03'", not
"invalid input". The model reads the error and usually fixes the call on the next step.

## 5. Reliability

- A timeout on every tool, recorded in `forge/tools.json`.
- Retries with backoff only for idempotent operations.
- Idempotency keys for writes, so a retried step does not act twice.
- Every tool whose class requires approval goes through one approval wrapper, never around it.

## 6. Many tools, MCP, and code execution

- Use **MCP** to connect to external systems or to expose your tools to other agents. Review and
  pin third-party MCP servers like any other dependency; each runs with the credentials you give
  it.
- With many tools, load definitions on demand (tool search) instead of putting all of them in
  every prompt.
- For long chains of tool calls over large data, let the agent write a short program that calls
  the tools in a sandbox and returns only the result. Anthropic reported large token savings in
  its best case, but it requires a sandbox and is overkill for a handful of tools.

## 7. Test tools

1. **Unit tests** for each tool with mocked backends: valid input, invalid input, empty result,
   large result, timeout.
2. **Tool-choice eval cases** (`tool_choice` category): the right tool is picked, with the right
   arguments, without unnecessary calls.
3. **Improve descriptions from transcripts:** when the model misuses a tool, read the trace,
   rewrite the description or schema, and re-run the tool-choice cases. Anthropic improves its
   own tools this way, with Claude reviewing failing transcripts.

Done when every tool passes its unit tests and the tool-choice cases pass.
