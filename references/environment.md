# Phase 6 — Environment setup

Goal: an isolated, reproducible environment that matches the approved stack, created and verified
**before any agent code is written**.

Why at this point: the stack is fixed only once the design is approved (Checkpoint 2), so
installing earlier risks installing the wrong things. Starting code before the environment works
means writing against APIs you have not confirmed. Most first-run failures of generated agents are
environment problems: the wrong Python version, packages that conflict, missing keys, a model ID
that does not exist. Found now they cost minutes; found in the build loop they cost hours.

## 1. Choose the interpreter version

- Pick a version that **every** chosen package supports. Check the framework's docs and each
  package's supported versions. The newest Python is not always safe: packages with native or
  GPU builds often lag behind new Python releases.
- See what is installed: `python --version`. On Windows, `py -0p` lists every installed
  interpreter and its path.
- If the needed version is missing, ask the user to install it. Do not install system-wide
  software on their behalf without asking.
- Record the version in `docs/design.md` (section *Environment*) and in a `.python-version` file.

## 2. Write the dependency files

- `requirements.txt` lists the **direct** runtime dependencies, each pinned with `==` to the
  version you verified in Phase 5. Example:

  ```
  # Agent framework (verified against docs on 2026-11-17)
  langgraph==<version>
  # Model provider SDK
  anthropic==<version>
  ```

- `requirements-dev.txt` starts with `-r requirements.txt` and adds test and tooling packages
  (for example pytest), also pinned.
- Every package needs a reason from the design: framework, provider SDK, tracing, validation, a
  tool's client library. No speculative "might need it" packages; each one is attack surface and
  install time.
- If the project already uses `pyproject.toml` with uv, Poetry or PDM, follow that instead. The
  same rules apply: pinned direct dependencies plus a committed lock file.

## 3. Create the virtual environment and install

```
python <skill-dir>/scripts/setup_env.py --python <path-to-interpreter>
```

The script:

1. refuses to continue if any requirement is not pinned with `==`
2. creates `.venv/` in the project with the chosen interpreter (reuses an existing one; add
   `--recreate` to start fresh)
3. upgrades pip, then installs `requirements.txt` and `requirements-dev.txt` if present
4. runs `pip check` to catch conflicting versions
5. writes `requirements.lock.txt` (the full `pip freeze`), so the exact environment can be rebuilt
6. writes `forge/environment.json` (interpreter, versions, lock file, `pip check` result)
7. adds `.venv/` and `.env` to `.gitignore`

In `human_runs` mode, give the user this command (with the interpreter path filled in), stop, and
wait for the output.

**Never install into the global Python or the user's base conda environment.** Everything the
agent needs lives in `.venv/`.

## 4. Secrets and configuration

- Write `.env.example` with every variable the agent needs: API keys, model IDs, endpoints,
  budgets, the kill-switch flag. Add a comment for each; give no real values.
- The user copies it to `.env` (git-ignored) and fills in the keys. Ask them to fill in the file,
  never to paste a key into the chat.

## 5. Prove the stack works

Before Phase 7, write a small smoke command inside the project (for example
`python -m <agent_package>.smoke`) and run it with the venv's interpreter. It should:

- import each key package and print its version
- make one tiny call to the configured model through the project's model module (or confirm the
  local model is downloaded and answers)
- exit non-zero, with a clear message, if a key is missing or the call fails

This confirms keys, network access, quotas and the model ID while nothing else can be blamed.
If the user has not supplied a key yet, record that as an open item in `forge/progress.md`
instead of skipping the check silently.

**Done when:** `.venv` exists, `pip check` is clean, `requirements.lock.txt` and
`forge/environment.json` are written, and the smoke command succeeds (or its failure is recorded
with the reason).

## 6. Rules from here on

- Run everything with the venv's interpreter: `.venv\Scripts\python.exe` on Windows,
  `.venv/bin/python` on macOS and Linux. Set the `command` in `forge/eval_config.json` to use it.
- Adding a package later: pin it in the requirements file, re-run `setup_env.py`, and note why in
  the decision log in `docs/design.md`.
- Upgrading the framework or the provider SDK is a behaviour change: re-run the full evals.
- The container image (pilot tier and above) installs from `requirements.lock.txt`, so
  production matches what was tested.

## 7. Other languages

`setup_env.py` handles Python only. For other stacks, write the equivalent commands and follow the
same principles: isolated, pinned, locked, verified.

| Stack | Isolation and pinning | Install |
|---|---|---|
| TypeScript / Node | pin Node in `.nvmrc` and `engines`; exact versions in `package.json`; commit the lock file | `npm ci` (or `pnpm install --frozen-lockfile`) |
| Go | `go.mod` with exact versions; commit `go.sum` | `go mod download` |
| .NET | pinned `PackageReference` versions; `packages.lock.json` | `dotnet restore --locked-mode` |
| Java / Kotlin | pinned versions; Gradle or Maven lock | the build tool's locked resolve |
