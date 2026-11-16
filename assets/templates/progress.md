# {{AGENT_NAME}} — progress log

Newest entry at the bottom. Every session appends one entry before it ends; the next session reads
this file first.

Entry format:

```
## <date> — phase <n> <name>
- Done:
- Eval score (if run):
- Issues hit and how they were solved:
- Next:
- Open questions:
```

## {{DATE}} — phase 1 intake

- Done: project initialised by agent-forge at tier {{TIER}}.
- Next: write docs/spec.md and ask the blocking questions.
