---
tags: [agent-forge, design]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash, WebSearch, WebFetch]
---

I need an agent for our support team. It should read new Zendesk tickets, look up the customer's order in our Postgres database (read only, we have a replica), classify the ticket as refund, shipping, bug or other, and draft a reply. A human support agent always reviews and sends the reply - the agent must never send anything itself. We're a Python shop on AWS and we use Claude through Amazon Bedrock. Around 2,000 tickets a day. Pilot quality is fine.

Use the current folder as the trusted workspace. Treat the spec as approved if it matches what I just said. Go ahead with the design: shape, framework, threat model and the eval cases. Don't write the agent code yet, I want to review the design first.
