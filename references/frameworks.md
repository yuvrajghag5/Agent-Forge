# Phase 5 — Choosing the framework

Goal: pick the lightest framework that meets the design's needs and the user's constraints,
justify it, and build on current documentation, not memory.

> The landscape below reflects late 2026 and **will drift**. Treat it as a map for shortlisting,
> then confirm every candidate against its official docs before deciding.

## 1. Procedure

1. **Hard constraints first** (from the spec; ask if unknown and they matter):
   - programming language the team uses (Python, TypeScript, Go, Java, .NET)
   - where it runs (a specific cloud, on-prem, a laptop, serverless, inside an existing app)
   - allowed model providers, including "local models only"
   - licence and data-residency requirements
2. **Needs from the design:**
   - durable state: resume after a crash, runs lasting minutes to days
   - human approval pauses in the middle of a run
   - multi-agent coordination
   - file system, shell or browser access (the agent works like a coding agent)
   - streaming to a web UI
   - strict structured output and typing
3. **Prefer less.** Single calls and fixed workflows rarely need a framework: the provider's SDK
   plus your own code is clearer and easier to debug. Add a framework when it supplies something
   you would otherwise build: durability, interrupts, multi-agent plumbing, a hosted runtime.
4. **Shortlist two or three,** compare them in `docs/design.md` against the constraints and
   needs, choose one, and list each rejected option with its reason.
5. **Verify before coding.** Look up the official docs, the latest stable version, and the
   current quickstart. Record the exact version in `docs/design.md`; Phase 6 pins it in the
   requirements file and installs it in an isolated environment. Framework APIs change every
   few months, and code written from memory often targets an API that no longer exists. If you
   cannot reach the docs, say so and choose the option whose API you can confirm locally (for
   example, from installed package source).

If the language and runtime are known and nothing else blocks the decision, decide without asking.

## 2. The options

| Option | Languages | Pick it when | Watch out for |
|---|---|---|---|
| **Plain code + provider SDK** | any | Rungs 1–2; small tool loops; maximum control and transparency | You build retries, state and tracing yourself; keep it small |
| **LangGraph** | Python, TypeScript | Graph-shaped workflows or agents needing checkpoints, crash recovery and human-approval interrupts; any model provider, including local via Ollama | Steeper learning curve; keep graphs small and explicit |
| **OpenAI Agents SDK** | Python, TypeScript | Lightweight agents with handoffs, guardrails and built-in tracing, especially on OpenAI models | Durability is your job; check current support for other providers |
| **Claude Agent SDK** | Python, TypeScript | Agents that work like Claude Code: files, shell, code, subagents, context compaction, MCP, permission hooks | Built around Claude models; consider where file and shell access is sandboxed |
| **Google ADK** | Python, plus other languages (check current list) | Multi-agent apps on Google Cloud; deployment to Google's agent runtime | Best fit inside the Google ecosystem |
| **Microsoft Agent Framework** | .NET, Python | Microsoft and Azure shops; graph workflows; successor to Semantic Kernel and AutoGen | Confirm current maturity of the parts you need |
| **Pydantic AI** | Python | Typed, structured outputs and dependency injection; provider-agnostic | Check its durable-execution integrations if you need long runs |
| **Vercel AI SDK / Mastra** | TypeScript | Agents inside web apps with streaming UIs | Server runtime limits on long runs |
| **CrewAI** | Python | Quick role-based prototypes | Less control over the loop; check production features |
| **LlamaIndex** | Python, TypeScript | Agents centred on retrieval over your documents | Use its workflow layer for control flow |

**Durable execution engines** (Temporal, DBOS, Restate, Inngest and similar) are not agent
frameworks but can wrap any of the above, or plain code, when runs must survive crashes, wait
days for approvals, or retry steps exactly once. Consider them for long-running background
agents at production tier.

**Managed runtimes** (for example Anthropic's Managed Agents, which separate the harness from
the sandbox and keep credentials outside it, or cloud vendors' agent engines) take on hosting,
sandboxing and session storage. Consider them when the user does not want to operate that
infrastructure.

## 3. Defaults when the user leaves it open

- Language: whatever the user's existing code uses; otherwise Python.
- Rungs 1–2: plain code with the provider's SDK behind one model-calling module.
- Rung 3 with approval pauses or long runs: LangGraph (Python or TypeScript).
- Rung 3 working on files, code or a shell: Claude Agent SDK, in a sandbox.
- Rung 4: the framework with the clearest single-writer pattern for the use case; justify it
  carefully.
- Local models only: plain code or LangGraph against an OpenAI-compatible local endpoint (for
  example Ollama), and keep the shape at rungs 1–3.

## 4. Keep the model provider swappable

Put every model call behind one module (`llm.py` or equivalent) that takes the model ID from
configuration. Then switching provider, or moving to a local model, is a configuration change and
the evals tell you whether quality held. Vendor agent SDKs make this harder; if you choose one,
note the lock-in in `docs/design.md`.

## 5. What to write

In `docs/design.md`, section *Framework*:

- the constraints and needs that drove the choice
- the shortlist with a short comparison
- the choice, the pinned version, and the docs page you checked (with the date)
- rejected options with reasons
- lock-in notes and how to swap later
