# Changes / build log

Per phase: 1. what was built, 2. issues faced, 3. how they were solved.

## Phase 0 — Research and design (Nov 2026)

**1. Built**
- Researched how production agents are built (Anthropic, OpenAI, Cognition, HumanLayer, Manus,
  Shopify, OWASP, Meta, Gartner, LangChain survey, Claude Code docs): `research.md`.
- Turned the research into a 10-phase lifecycle for building any agent, each phase with a
  "done when" gate: `agent-lifecycle.md`.
- Design decisions recorded in `design.md`.

**2. Issues faced**
- "One prompt" and "production-grade" contradict each other: production needs facts a prompt
  does not contain.
- Risk of being yet another scaffolder in a crowded space.
- Many research sources were only available as summaries, so some figures are unverified.

**3. How they were solved**
- Intake asks at most five blocking questions and labels every other guess as an assumption.
- The differentiator is agent-specific judgment: shape ladder, evals first, tiered gate, threat
  model.
- `research.md` carries a source caveat at the top.

## Phase 1 — Write the skill v0 (Nov 2026)

**1. Built**
- `SKILL.md`: trigger description, principles, orientation and resume rules, phase table with
  three checkpoints, unattended-run and existing-prototype handling.
- One reference per phase, templates copied into target projects (with `TODO(forge)` markers the
  gate can detect), and standard-library scripts: `forge.py` (state and checkpoints),
  `run_evals.py` (runner, graders, pass@1 / pass@k / pass^k), `readiness_check.py` (tier gate,
  secret scan, Rule of Two).
- Three draft test cases in the `claude plugin eval` layout.

**2. Issues faced**
- Fixed per-framework "stack packs" would go stale and limit the choice of framework.
- YAML would need a third-party package in the scripts.

**3. How they were solved**
- Framework choice became a procedure (constraints → needs → prefer less → compare → check
  current docs → record the version) with an options table and defaults.
- Machine-read files use JSON / JSONL.

## Phase 2 — Smoke test, cleanup and restructure (Nov 2026)

**1. Tested**
- `forge.py init` / `status`, `run_evals.py validate` and `readiness_check.py` ran cleanly on an
  empty scratch project; the gate reported exactly the failures expected for it.

**2. Issues found**
- The gate labelled existence-only checks as "complete".
- `forge.py goto` would crash on an unknown phase in `state.json`.
- The project folder and the skill had different names, and docs were scattered at the top level.

**3. How they were solved**
- Existence-only checks now read "<file> exists"; `goto` exits with a clear message.
- One folder named `agent-forge` that *is* the skill; project write-ups moved into `docs/`.

## Phase 2b — Environment setup phase (Nov 2026)

**1. Built**
- New **Phase 6 Environment setup** between Framework (Checkpoint 2) and Tools; the skill now has
  11 phases.
- `references/environment.md`: interpreter choice, `==`-pinned `requirements.txt` /
  `requirements-dev.txt`, `.venv`, `.env.example`, a smoke call to the model, rules for later
  dependency changes, equivalents for Node, Go, .NET and Java.
- `scripts/setup_env.py`: refuses unpinned requirements, builds `.venv`, installs, runs
  `pip check`, writes `requirements.lock.txt` and `forge/environment.json`, git-ignores `.venv/`
  and `.env`.
- Gate: environment checks (pins, lock file, `.venv` ignored, Node lock file).

**2. Issues faced**
- Renumbering touched `SKILL.md`, `forge.py`, reference headings, templates and docs.
- The newest Python release is not always supported by every package (native and GPU builds lag).
- First smoke run: the venv was created and pip upgraded, but the package install did not
  complete, so no lock file was written. Cause not yet known.

**3. How they were solved / status**
- Renumbered everywhere and searched for stale phase numbers afterwards.
- `environment.md` tells the agent to choose an interpreter every package supports and to ask the
  user to install a missing version rather than installing it itself.
- The `setup_env.py` failure needs a re-run with its output captured (open).

## Phase 2c — Trusted workspace question (Nov 2026)

**1. Built**
- Every use of the skill now starts by asking which folder is the trusted workspace for the
  project (default: a new folder named after the agent inside the current folder). It is asked
  together with the intake questions and does not count toward their limit of five.
- All files, the virtual environment, eval runs and commands stay inside that folder; anything
  outside needs the user's OK. Unattended runs use the current folder and record it as an
  assumption.
- `forge.py init` records the absolute path as `workspace` in `forge/state.json`;
  `forge.py status` prints it and warns when run from a different folder.
- Test cases: the vague-idea case checks the workspace question is asked; the two design cases
  name the workspace in the prompt, and one checks that every file stays inside it.

**2. Issues faced**
- The vague-idea test limited the response to five questions in total, which the new question
  would break.

**3. How they were solved**
- The limit now applies to intake questions only; the workspace question is checked separately.
- Removed the leftover smoke-test folder.

## Phase 2d — Frontend phase (Nov 2026)

**1. Built**
- New **Phase 12 Frontend** after the gate; the skill now has 12 phases and 4 checkpoints
  (Checkpoint 4: the user accepts the interface, `forge.py approve ui`).
- `references/frontend.md`: decide what the interface is for; choose the smallest stack; plan
  palette, type roles, wireframe and one signature element grounded in the agent's subject;
  critique the plan against common generated-design defaults; what every agent interface needs
  (start, live progress, evidence, approvals, result, failure, history, stop); safety rules for
  untrusted content and local servers; quality floor; interface copy; verification.
- `READINESS.md` template: a frontend review checklist (not part of the tier gate).

**2. Issues faced**
- A generic design method does not cover what is specific to agents: decisions in progress,
  approvals, and text from untrusted sources shown in a browser.
- Building the interface early would put polish on an unverified agent.

**3. How they were solved**
- Agent-specific sections (live decisions, approval screens, XSS and CSRF-style protections for
  local servers) added to the method.
- The phase is placed last, after the readiness gate.
