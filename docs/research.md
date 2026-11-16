# Research — how industry-level agents are built

> Researched 16 Nov 2026. **Source caveat:** the Claude Code docs were read directly; most other
> articles were seen through search summaries, so exact figures should be checked against the
> original before being quoted (e.g. in a report or post).

---

## 1. The short answer

An industry agent is **a model plus a "harness"**. The harness is the code around the model:
tools, what it sees (context), memory, permissions, checks, and logs. The model is mostly bought
in; the engineering goes into the harness.

- Claude Code docs: Claude Code is "the layer around the model that provides the tools and
  manages the context the model sees" — the *agentic harness*.
- OpenAI (Feb 2026) named the discipline **harness engineering**:
  - context engineering = *what the agent should see*
  - harness engineering = *what the system should prevent, measure and correct*

Second finding: **most production "agents" are not very autonomous.** HumanLayer's
"12-Factor Agents": successful agents are mostly normal software with an LLM deciding at a few
key points.

## 2. Types of agents

### By who controls the flow (Anthropic, "Building effective agents")

| Type | What it is | When it's used |
|---|---|---|
| Single LLM call | One call + retrieval + examples | Enough for many apps; recommended start |
| **Workflows** (code decides the path) | Prompt chain, routing, parallel/voting, orchestrator–workers, evaluator–optimizer | Well-defined tasks; predictable, cheap |
| **Agent** (model decides the path) | LLM runs a loop choosing tools until done | Open-ended tasks where steps can't be known in advance |

### By how many agents

- **One agent with a loop** — the default. Claude Code, Codex, Devin at their core.
- **Lead agent + helper agents** — Anthropic's research system: lead sends search work to
  parallel helpers. ~90% better than a single agent on their internal research test, but
  ~15× the tokens of a normal chat.
- **Many agents writing at once** — mostly advised against. Cognition, "Don't Build
  Multi-Agents" (2025): parallel agents make conflicting decisions because they don't share
  context. Their April 2026 follow-up: multi-agent works **when only one agent writes** and the
  others read or review; a reviewer with a clean context works best.

### By product shape

- copilots inside an app (Shopify Sidekick)
- coding agents (Claude Code, Codex, Devin, Cursor)
- research agents
- long-running background agents
- browser / computer-use agents
- voice agents

## 3. The approach industry follows

1. **Start from value, not "let's build an agent".** Gartner (Jun 2025) predicts >40% of
   agentic AI projects cancelled by end of 2027 — cost, unclear value, weak risk controls. Also
   coined "agent washing" (old chatbots relabelled as agents).
2. **Simplest design that works.** Single call → workflow → agent → multi-agent; climb only
   when the simpler one fails.
3. **Tools are a product.** Few tools, clear boundaries, clear descriptions, token-efficient
   outputs. Anthropic tests and improves its tools with Claude. Shopify: Sidekick got worse as
   tools grew from a handful to dozens.
4. **Context engineering.** Anthropic: "the smallest possible set of high-signal tokens".
   - summarise long history when context fills (compaction)
   - keep notes outside the context (e.g. to-do list)
   - helper agents explore in their own context, return only a summary
   - **prompt caching** (Manus): cached input ~10× cheaper → keep the prompt start stable,
     append-only context, don't add/remove tools mid-task
5. **Evals early.** Anthropic grades with code checks, LLM judges and humans. Two metrics:
   - **pass@k** — succeeds at least once in k tries
   - **pass^k** — succeeds every time in k tries (use when the agent can't retry)

   Shopify tests changes against simulated conversations built from real ones and tunes its
   LLM judge until it agrees with humans.
6. **Secure by design** (main threat: prompt injection).
   - **Lethal trifecta** (Willison): private data + untrusted input + a way to send data out =
     data can leak.
   - **Rule of Two** (Meta, Oct 2025): in one session an agent gets at most two of those three
     (Meta's third property also covers changing state) unless a human checks.
   - **OWASP Top 10 for Agentic Applications** (Dec 2025): goal hijack, tool misuse, identity /
     privilege abuse, unexpected code execution, insecure inter-agent communication,
     human-agent trust exploitation, supply chain, memory/context poisoning, cascading
     failures, rogue agents.
   - In practice: sandbox tools, keep credentials outside the sandbox, human approval before
     anything irreversible.
7. **State and long runs.** Pause, resume, recover after a crash. Anthropic's long-running
   harness:
   - first session writes a **feature list as JSON** (the model tends to rewrite Markdown),
     a **progress file**, and a first **git commit**
   - each later session reads those, makes one small step, commits, updates the progress file
8. **Observe, then improve from real data.** Tracing, ideally in OpenTelemetry GenAI format
   (still "Development", not stable). Secondary source: ~89% of teams trace agents, only
   ~52% test them.

## 4. Key decisions

| Decision | What industry tends to choose |
|---|---|
| Workflow or agent? | Workflow unless steps truly can't be known in advance |
| Single or multi-agent? | Single; add read-only helpers; one writer |
| Framework | LangGraph when crash recovery + human approval matter; OpenAI Agents SDK for simplicity; Google ADK in Google environments; Claude Agent SDK for Claude Code's harness |
| Tools | Few, well described; MCP for outside systems; load definitions only when needed; agent writes code that calls tools (Anthropic best case 150k → 2k tokens) |
| Memory | Files / database outside the context + compaction |
| Autonomy | Read-only runs freely; irreversible needs a human |
| Model mix | Strong model leads, cheaper models do helper work |
| Hosting | Own loop, or managed runtime (Claude Managed Agents self-hosted private beta, 12 Nov 2026) |

## 5. Claude Code as a worked example

From the official docs and what is visible inside a session (not internal source code).

- **Simple loop:** *gather context → act → verify*, repeated until done; the user can
  interrupt any time. No complicated orchestration graph — the model picks each next step from
  the last result.
- **Five tool groups:** files, search, running commands, web, code intelligence. Plus helper
  agents and asking the user questions.
- **Context discipline:**
  - `CLAUDE.md` / `AGENTS.md` and the memory index load at session start
  - skills show only descriptions until used (progressive disclosure)
  - most tool definitions are deferred and loaded on demand (tool search)
  - helper agents work in their own context and return a summary
  - old conversation is summarised when context fills → lasting rules belong in CLAUDE.md
- **Safety:** file snapshots before edits (undo); permission modes (manual, accept-edits, plan,
  auto with a background classifier). External effects (databases, deployments) can't be
  undone, so permissions protect them.
- **State:** sessions saved as plain JSONL files, resumable and forkable; memory notes outside
  the context carry learnings between sessions.
- **One harness everywhere:** terminal, desktop, web, CI. The Claude Agent SDK exposes the same
  harness to developers.

**Lesson:** the model stays simple; reliability comes from the harness (memory, permissions,
checks, context limits, undo).

## 6. Where the industry stands (late 2026)

- LangChain survey (1,300+ respondents): ~57% have agents in production; **quality**, not
  cost, is the top blocker (32%).
- Standards settling: MCP and AGENTS.md under the Linux Foundation's Agentic AI Foundation
  (Dec 2025). **Agent Skills** (SKILL.md) is an open standard; Codex docs confirm support and
  progressive loading.
- Focus has moved: prompt engineering → context engineering → harness engineering.

## 7. Implications for this skill

Confirms the direction in `design.md`: spec first, simplest design first, evals first, threat
model. Things the skill should also teach:

- harness engineering, not only code generation
- tool design rules
- context and caching discipline
- pass^k for agents that can't retry
- simulated tests built from real conversations
- the Rule of Two as a concrete security check
- the long-run pattern: JSON feature list + progress file + git commits

---

## Sources

- [Anthropic – Building effective agents](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic – Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Anthropic – Effective context engineering (summary)](https://agentic-ai.readthedocs.io/en/latest/ContextEngineering/anthropic/)
- [Anthropic – Writing effective tools for agents](https://anthropic.com/engineering/writing-tools-for-agents)
- [Anthropic – Demystifying evals for AI agents](https://anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Anthropic – Effective harnesses for long-running agents](https://anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Anthropic – Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [Anthropic – Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk)
- [Claude Code docs – How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)
- [Claude Managed Agents – self-hosted update](https://claude.com/blog/claude-managed-agents-updates)
- [Help Net Security – self-hosted Managed Agents](https://www.helpnetsecurity.com/2026/11/12/anthropic-self-hosted-claude-managed-agents/)
- [OpenAI – A practical guide to building agents (PDF)](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)
- [OpenAI – Harness engineering](https://openai.com/index/harness-engineering/)
- [InfoQ – OpenAI harness engineering](https://www.infoq.com/news/2026/02/openai-harness-engineering-codex)
- [Cognition – Don't Build Multi-Agents](https://cognition.ai/blog/dont-build-multi-agents)
- [Cognition – Multi-Agents: What's Actually Working](https://cognition.com/blog/multi-agents-working)
- [HumanLayer – 12-Factor Agents](https://www.humanlayer.dev/12-factor-agents)
- [Manus – Context engineering lessons](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
- [Shopify – Lessons from Sidekick](https://shopify.engineering/building-production-ready-agentic-systems)
- [Simon Willison – Rule of Two & prompt injection papers](https://simonwillison.net/2025/Nov/2/new-prompt-injection-papers/)
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [Agentic AI Foundation (WorkOS summary)](https://workos.com/blog/the-linux-foundation-launches-the-aaif)
- [OpenAI Codex – Agent Skills](https://developers.openai.com/codex/skills.md)
- [OpenTelemetry GenAI conventions (Greptime)](https://www.greptime.com/blogs/2026-05-09-opentelemetry-genai-semantic-conventions)
- [LangChain – State of Agent Engineering](https://langchain.com/state-of-agent-engineering)
- [Gartner – 40% of agentic projects cancelled by 2027](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027)
- [Agent framework comparison 2026 (Diagrid)](https://www.diagrid.io/blog/ai-agent-frameworks)
