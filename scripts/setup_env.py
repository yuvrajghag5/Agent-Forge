#!/usr/bin/env python3
"""Create and verify the agent project's Python virtual environment (agent-forge Phase 6).

Usage:
  python setup_env.py [--project .] [--python PATH] [--requirements requirements.txt]
                      [--dev requirements-dev.txt] [--venv .venv] [--recreate]

Steps: refuse unpinned requirements -> create .venv with the chosen interpreter -> upgrade pip
-> install requirements (and dev requirements if present) -> pip check -> write
requirements.lock.txt and forge/environment.json -> git-ignore .venv/ and .env.

Exit code 0 on success, 1 if pip check reports conflicts, other non-zero on failure.
Standard library only, Python 3.9+. Output is ASCII so it prints on any console.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

GITIGNORE_ENTRIES = {
    ".venv/": {".venv", ".venv/", "/.venv", "/.venv/"},
    ".env": {".env", "/.env", ".env*", "/.env*", "*.env"},
}


def venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def run(cmd: list, cwd: Path) -> None:
    printable = " ".join(str(c) for c in cmd)
    print(f"> {printable}")
    proc = subprocess.run([str(c) for c in cmd], cwd=str(cwd))
    if proc.returncode != 0:
        sys.exit(f"Command failed with exit code {proc.returncode}: {printable}")


def capture(cmd: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([str(c) for c in cmd], cwd=str(cwd), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def unpinned_requirements(path: Path) -> list[str]:
    """Return requirement lines that are not pinned with '=='.

    Option lines (-r, -c, -e, --index-url ...) and blank or comment lines are ignored.
    Direct references ("name @ url") are accepted as they are; point them at a tag or commit.
    """
    unpinned = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        requirement = line.split(";", 1)[0].strip()  # drop environment markers
        if " @ " in requirement:
            continue
        if "==" not in requirement:
            unpinned.append(raw.strip())
    return unpinned


def ensure_gitignore(project: Path) -> list[str]:
    path = project / ".gitignore"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    present = {line.strip() for line in lines}
    added = [entry for entry, variants in GITIGNORE_ENTRIES.items() if not (present & variants)]
    if added:
        with path.open("a", encoding="utf-8") as f:
            if lines and lines[-1].strip():
                f.write("\n")
            for entry in added:
                f.write(entry + "\n")
    return added


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="agent-forge environment setup")
    parser.add_argument("--project", default=".", help="project root (default: current folder)")
    parser.add_argument("--python", default=sys.executable,
                        help="interpreter to build the venv with (default: the one running this)")
    parser.add_argument("--requirements", default="requirements.txt")
    parser.add_argument("--dev", default="requirements-dev.txt",
                        help="dev requirements, installed if the file exists")
    parser.add_argument("--venv", default=".venv")
    parser.add_argument("--recreate", action="store_true", help="delete and rebuild the venv")
    args = parser.parse_args(argv)

    project = Path(args.project).resolve()
    req = project / args.requirements
    dev = project / args.dev
    if not req.exists():
        sys.exit(f"{req} not found. Write the pinned requirements first (references/environment.md).")

    req_files = [req] + ([dev] if dev.exists() else [])
    unpinned = []
    for path in req_files:
        unpinned += [f"{path.name}: {line}" for line in unpinned_requirements(path)]
    if unpinned:
        print("These requirements are not pinned with '==':")
        for line in unpinned:
            print(f"  - {line}")
        sys.exit("Pin every direct dependency to the version verified in Phase 5, then re-run.")

    version_proc = capture([args.python, "-c",
                            "import sys; print('%d.%d.%d' % sys.version_info[:3])"], project)
    if version_proc.returncode != 0:
        sys.exit(f"Could not run interpreter '{args.python}': {version_proc.stderr.strip()}")
    py_version = version_proc.stdout.strip()
    print(f"Interpreter: {args.python} (Python {py_version})")

    venv = project / args.venv
    if venv.exists() and args.recreate:
        print(f"Removing existing {venv.name}/ (--recreate)")
        shutil.rmtree(venv)
    vpy = venv_python(venv)
    if not vpy.exists():
        run([args.python, "-m", "venv", venv], project)
    else:
        existing = capture([vpy, "-c", "import sys; print('%d.%d.%d' % sys.version_info[:3])"], project)
        if existing.stdout.strip() != py_version:
            print(f"Note: existing {venv.name}/ uses Python {existing.stdout.strip()}, not "
                  f"{py_version}. Use --recreate to rebuild it with the chosen interpreter.")
            py_version = existing.stdout.strip()

    run([vpy, "-m", "pip", "install", "--upgrade", "pip"], project)
    for path in req_files:
        run([vpy, "-m", "pip", "install", "-r", path], project)

    check = capture([vpy, "-m", "pip", "check"], project)
    check_ok = check.returncode == 0
    print(check.stdout.strip() or check.stderr.strip())

    freeze = capture([vpy, "-m", "pip", "freeze", "--exclude-editable"], project)
    if freeze.returncode != 0:
        sys.exit(f"pip freeze failed: {freeze.stderr.strip()}")
    packages = [line for line in freeze.stdout.splitlines() if line.strip()]
    lock = project / "requirements.lock.txt"
    lock.write_text(
        f"# Generated by agent-forge setup_env.py on {dt.date.today().isoformat()} "
        f"with Python {py_version}.\n# Full environment; rebuild with: pip install -r "
        f"requirements.lock.txt\n" + "\n".join(packages) + "\n",
        encoding="utf-8")

    added = ensure_gitignore(project)

    info = {
        "created": dt.datetime.now().isoformat(timespec="seconds"),
        "python_version": py_version,
        "interpreter_used": str(args.python),
        "venv": args.venv,
        "venv_python": str(vpy.relative_to(project)),
        "requirements": [str(p.relative_to(project)) for p in req_files],
        "lock_file": "requirements.lock.txt",
        "packages_installed": len(packages),
        "pip_check_ok": check_ok,
    }
    env_json = project / "forge" / "environment.json"
    env_json.parent.mkdir(parents=True, exist_ok=True)
    env_json.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")

    print()
    print(f"Environment ready: {len(packages)} packages in {args.venv}/ (Python {py_version})")
    print("Lock file: requirements.lock.txt   Details: forge/environment.json")
    if added:
        print("Added to .gitignore: " + ", ".join(added))
    print(f"Use this interpreter from now on: {vpy.relative_to(project)}")
    if os.name == "nt":
        print(f"Activate (PowerShell): {args.venv}\\Scripts\\Activate.ps1")
    else:
        print(f"Activate: source {args.venv}/bin/activate")
    print("Next: set forge/eval_config.json 'command' to this interpreter, write .env.example,"
          " and run the smoke check (references/environment.md section 5).")
    if not check_ok:
        print("pip check found conflicts: fix the pinned versions before building.")
        sys.exit(1)


if __name__ == "__main__":
    main()
