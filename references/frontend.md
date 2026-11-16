# Phase 12 — Frontend

Goal: give the finished agent an interface people want to use: distinctive, specific to what the
agent does, honest about what the agent is doing, and safe with the untrusted content it shows.

This phase comes last on purpose. The interface should present a working, measured agent; a
polished screen on top of an unverified agent hides problems instead of showing them.

## Contents

1. Decide what the interface is for
2. Choose the stack
3. Plan the look (tokens, wireframe, signature)
4. Critique the plan before building
5. Build: what every agent interface needs
6. Safety rules for agent interfaces
7. Quality floor
8. Writing the interface copy
9. Verify and hand over (Checkpoint 4)

## 1. Decide what the interface is for

Write three lines in `docs/frontend.md` before anything else:

- **Who uses it, where:** for example "one researcher, on a laptop, watching a run unfold".
- **The screen's single job:** for example "start a research run and see the evidence come together".
- **What the agent produces that people need to see:** progress, decisions, intermediate evidence,
  approvals, the final artefact, failures.

Ask the user at most two questions, each with a default, if these are unclear: who uses it, and
any brand or visual constraints. Otherwise decide and record the choice.

## 2. Choose the stack

Prefer the smallest stack that does the job, and keep it inside the agent's project:

| Situation | Default |
|---|---|
| Local, single user, Python agent | a small server inside the agent's package (standard library or the agent's existing web framework) serving one HTML page, one CSS file and one JS file; no build step |
| Several users, or an existing web app | the team's framework; the agent behind an API |
| Chat-style product | a chat UI that still shows tool steps, sources and approvals, not just bubbles |

Any new dependency follows Phase 6: pinned, installed with `setup_env.py`, recorded in the lock
file. Stream progress with Server-Sent Events or polling; avoid WebSockets unless the agent needs
two-way messages mid-run.

## 3. Plan the look

Ground every choice in the agent's subject: its materials, instruments, artefacts and vocabulary.
A research agent, a support-ticket agent and a coding agent should not look alike.

Write the plan in `docs/frontend.md`:

- **Palette:** 4–6 named colours with hex values, each with a job (background, surface, text,
  accent, a colour reserved for warnings or conflicts).
- **Type:** a characterful display face used sparingly, a body face chosen for the main reading
  task, and a utility face for data, logs or code. Set a clear scale.
- **Layout:** one sentence plus an ASCII wireframe; compare two options and pick one.
- **Signature:** the one element people will remember, and it must show something true about the
  agent (how it works, what it found), not decoration.
- **Motion:** where movement explains something (a step completing, evidence arriving), and nowhere
  else.

Structure must encode meaning. Numbering is for real sequences (agent steps); colour, line style
or position can encode real properties (credibility, status, conflict). If a device does not encode
something true, remove it.

## 4. Critique the plan before building

Generated designs cluster around a few looks that appear whatever the subject is, for example: a
warm cream page with a heavy serif and a terracotta accent; a near-black page with one acid-bright
accent; a broadsheet of hairline rules and dense columns. They are fine when the user asks for
them; otherwise they are defaults, not choices.

Check each part of the plan: would you have produced it for any similar agent? If yes, change it
and write down what changed and why. Then spend the boldness in one place (the signature) and keep
everything else quiet and disciplined. Before finishing, remove one decorative element.

## 5. Build: what every agent interface needs

- **Start:** the main input the agent needs, with a clear action label.
- **Live progress:** the current step, budgets used, and the agent's decisions as they happen,
  readable by a person (action, short reason, result). This is where the trace pays off.
- **Intermediate evidence:** what the agent has collected so far (sources, notes, files changed).
- **Approvals:** if the agent has approval steps, show exactly what will happen (recipient,
  amount, diff), with "Approve" and "Reject" and nothing pre-selected.
- **Result:** the final artefact, rendered for reading, with its status (complete / partial /
  declined) stated plainly, and the limitations visible rather than hidden.
- **Failure:** what went wrong, what was kept, and the next step (resume, retry, change input).
- **History:** past runs, reopenable.
- **Stop:** a way to stop a running agent; it should stop cleanly and keep what it has.

## 6. Safety rules for agent interfaces

Agent output often contains text from untrusted sources (web pages, emails, documents). Treat it
like user input on a public website.

- **Never insert untrusted text as raw HTML.** Escape everything; render Markdown with a renderer
  that escapes first and only allows a small set of elements. Links: `http`/`https` only, opened
  with `rel="noopener noreferrer"`.
- **Content Security Policy:** scripts and styles from the app's own origin (plus named font hosts
  if used); no inline scripts.
- **Local servers:** bind to `127.0.0.1`; check the `Host` header (blocks DNS rebinding); require a
  per-start random token on every API call (blocks other websites from driving the agent).
- **No secrets in the browser:** keys stay on the server side.
- **Approvals in the UI** must post the exact action ID that was shown, so an approval cannot be
  replayed onto a different action.
- Add tests for the escaping, the token and the host check.

## 7. Quality floor

Build to it without announcing it:

- works from 360 px wide to large screens, with no horizontal scrolling;
- visible keyboard focus and full keyboard use;
- `prefers-reduced-motion` turns animation off;
- colour contrast that passes WCAG AA for text; meaning never carried by colour alone (pair it
  with line style, a label or an icon);
- empty, loading, error and finished states all designed, not left blank.

## 8. Writing the interface copy

- Name things by what the user controls and recognises, not by how the system is built.
- Buttons say what happens ("Start research", "Stop run"), and the same action keeps the same name
  everywhere.
- Plain verbs, sentence case, active voice, no filler.
- Empty states invite action and say what will happen; errors say what went wrong and what to do,
  without apologising.

## 9. Verify and hand over (Checkpoint 4)

1. Run the interface (in `human_runs` mode, hand over the command) and look at it in a real browser:
   take screenshots if the environment allows, at desktop and phone width.
2. Walk through: start, live progress, a finished result, a declined or failed run, history, stop.
3. Check the quality floor and the safety rules above.
4. Record the plan, the critique and the result in `docs/frontend.md`, and tick the frontend items
   in `READINESS.md`.
5. Show the user and ask for acceptance; record it with `forge.py approve ui`.
