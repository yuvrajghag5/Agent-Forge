#!/usr/bin/env python3
"""agent-forge project helper.

Commands:
  init      create the project layout, templates and forge/state.json
  status    show phase, checkpoints, features and the latest eval score
  approve   record a checkpoint approval: spec | design | gate
  advance   mark the current phase done and move to the next one
  goto      reopen an earlier phase for rework

Standard library only, Python 3.9+. Output is ASCII so it prints on any console.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "assets" / "templates"

PHASES = [
    ("intake", "Intake and spec", "references/intake.md"),
    ("shape", "Shape", "references/shape-ladder.md"),
    ("evals", "Evals first", "references/evals.md"),
    ("threat_model", "Threat model", "references/security.md"),
    ("framework", "Framework", "references/frameworks.md"),
    ("environment", "Environment setup", "references/environment.md"),
    ("tools", "Tools", "references/tools.md"),
    ("harness", "Harness", "references/harness.md"),
    ("build", "Build against evals", "references/evals.md (section 7)"),
    ("ops", "Observability and ops", "references/ops.md"),
    ("gate", "Gate and handover", "references/readiness-gate.md, references/handover.md"),
]
PHASE_IDS = [p[0] for p in PHASES]

# A phase cannot be marked done until this checkpoint has been approved.
CHECKPOINT_AFTER = {"intake": "spec", "framework": "design", "gate": "gate"}
CHECKPOINTS = ["spec", "design", "gate"]
TIERS = ["prototype", "pilot", "production"]
MODES = ["agent_runs", "human_runs"]

# template file name -> destination relative to the project root
LAYOUT = {
    "spec.md": "docs/spec.md",
    "design.md": "docs/design.md",
    "threat-model.md": "docs/threat-model.md",
    "rollout.md": "docs/rollout.md",
    "tools.json": "forge/tools.json",
    "eval_config.json": "forge/eval_config.json",
    "progress.md": "forge/progress.md",
    "cases.jsonl": "evals/cases.jsonl",
    "AGENTS.md": "AGENTS.md",
    "READINESS.md": "READINESS.md",
}


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def state_path(project: Path) -> Path:
    return project / "forge" / "state.json"


def load_state(project: Path) -> dict:
    path = state_path(project)
    if not path.exists():
        sys.exit(f"No forge/state.json in {project}. Run 'forge.py init' first.")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_state(project: Path, state: dict) -> None:
    state["updated"] = now()
    path = state_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def phase_title(phase_id: str) -> str:
    for pid, title, _ in PHASES:
        if pid == phase_id:
            return title
    return phase_id


def phase_ref(phase_id: str) -> str:
    for pid, _, ref in PHASES:
        if pid == phase_id:
            return ref
    return ""


def cmd_init(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    if state_path(project).exists():
        sys.exit("forge/state.json already exists: this project is already initialised. "
                 "Use 'forge.py status' to see where it stands.")
    if not TEMPLATES.is_dir():
        sys.exit(f"Templates not found at {TEMPLATES}")

    today = dt.date.today().isoformat()
    subs = {"{{AGENT_NAME}}": args.name, "{{DATE}}": today, "{{TIER}}": args.tier}

    created, skipped = [], []
    for src_name, dest_rel in LAYOUT.items():
        src = TEMPLATES / src_name
        dest = project / dest_rel
        if dest.exists():
            skipped.append(dest_rel)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = src.read_text(encoding="utf-8")
        for key, value in subs.items():
            text = text.replace(key, value)
        dest.write_text(text, encoding="utf-8")
        created.append(dest_rel)
    (project / "evals" / "results").mkdir(parents=True, exist_ok=True)

    state = {
        "schema_version": 1,
        "agent_name": args.name,
        "workspace": str(project),
        "tier": args.tier,
        "execution_mode": args.mode,
        "phase": "intake",
        "phases_done": [],
        "checkpoints": {c: None for c in CHECKPOINTS},
        "decisions": {
            "shape": None,
            "framework": None,
            "framework_version": None,
            "language": None,
            "models": {},
        },
        "assumptions": [],
        "open_questions": [],
        "features": [],
        "created": now(),
        "updated": now(),
    }
    save_state(project, state)

    print(f"Initialised agent-forge project '{args.name}'")
    print(f"Trusted workspace: {project}")
    print(f"Tier: {args.tier}   Execution mode: {args.mode}")
    for rel in created:
        print(f"  created  {rel}")
    for rel in skipped:
        print(f"  kept     {rel} (already existed)")
    print("  created  forge/state.json")
    print(f"Next: phase 1 Intake and spec - read {phase_ref('intake')}")


def cmd_status(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state = load_state(project)
    phase = state.get("phase", "intake")

    print(f"Agent: {state.get('agent_name')}   Tier: {state.get('tier')}   "
          f"Mode: {state.get('execution_mode')}")
    recorded = state.get("workspace")
    print(f"Trusted workspace: {recorded or 'not recorded'}")
    if recorded and Path(recorded).resolve() != project:
        print(f"WARNING: running from {project}, which is not the recorded workspace. "
              "Confirm with the user which folder to use before changing anything.")
    if phase == "done":
        print("Phase: all phases done")
    else:
        idx = PHASE_IDS.index(phase) + 1 if phase in PHASE_IDS else "?"
        print(f"Phase: {idx}/{len(PHASES)} {phase_title(phase)}   (read {phase_ref(phase)})")
    done = state.get("phases_done", [])
    print(f"Phases done: {', '.join(done) if done else 'none'}")

    print("Checkpoints:")
    for cp in CHECKPOINTS:
        rec = state.get("checkpoints", {}).get(cp)
        if rec:
            print(f"  {cp:<7} approved by {rec.get('by')} at {rec.get('at')}")
        else:
            print(f"  {cp:<7} not yet")

    decisions = state.get("decisions", {})
    shown = {k: v for k, v in decisions.items() if v}
    if shown:
        print("Decisions: " + "; ".join(f"{k}={v}" for k, v in shown.items()))

    features = state.get("features", [])
    if features:
        n_done = sum(1 for f in features if f.get("status") == "done")
        print(f"Features: {n_done}/{len(features)} done")
        for feat in features:
            if feat.get("status") != "done":
                print(f"  [{feat.get('status', 'todo')}] {feat.get('id')}: {feat.get('description', '')}")

    if state.get("assumptions"):
        print(f"Assumptions recorded: {len(state['assumptions'])}")
    open_q = state.get("open_questions", [])
    if open_q:
        print("Open questions:")
        for q in open_q:
            print(f"  - {q}")

    latest = project / "evals" / "results" / "latest.json"
    if latest.exists():
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
            overall = data.get("summary", {}).get("overall", {})
            print(f"Latest full eval run {data.get('run_id')}: pass@1={overall.get('pass_at_1')} "
                  f"over {overall.get('cases')} cases, pending judge grades={overall.get('pending')}")
        except (json.JSONDecodeError, OSError):
            print("Latest eval results could not be read.")
    else:
        print("No full eval run yet.")


def cmd_approve(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state = load_state(project)
    state.setdefault("checkpoints", {})[args.checkpoint] = {
        "by": args.by,
        "at": now(),
        "note": args.note or "",
    }
    save_state(project, state)
    print(f"Checkpoint '{args.checkpoint}' approved by {args.by}.")
    if args.by == "auto":
        print("Recorded as auto-approved: list it under 'Needs your decision' in the handover.")


def cmd_advance(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state = load_state(project)
    phase = state.get("phase")
    if phase == "done":
        print("All phases are already done.")
        return
    if phase not in PHASE_IDS:
        sys.exit(f"Unknown phase '{phase}' in state.json.")

    needed = CHECKPOINT_AFTER.get(phase)
    if needed and not state.get("checkpoints", {}).get(needed):
        sys.exit(f"Phase '{phase}' ends at checkpoint '{needed}', which is not approved yet. "
                 f"Get the user's approval, then run: forge.py approve {needed}")

    if phase not in state.setdefault("phases_done", []):
        state["phases_done"].append(phase)
    idx = PHASE_IDS.index(phase)
    if idx + 1 < len(PHASE_IDS):
        state["phase"] = PHASE_IDS[idx + 1]
        save_state(project, state)
        nxt = state["phase"]
        print(f"Done: {phase_title(phase)}. Now: {idx + 2}/{len(PHASES)} {phase_title(nxt)} "
              f"(read {phase_ref(nxt)})")
    else:
        state["phase"] = "done"
        save_state(project, state)
        print("All phases done.")


def cmd_goto(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state = load_state(project)
    current = state.get("phase")
    if current != "done" and current not in PHASE_IDS:
        sys.exit(f"Unknown phase '{current}' in state.json.")
    current_idx = len(PHASE_IDS) if current == "done" else PHASE_IDS.index(current)
    target_idx = PHASE_IDS.index(args.phase)
    if target_idx > current_idx:
        sys.exit("goto only reopens an earlier phase. Use 'advance' to move forward.")
    state["phase"] = args.phase
    state["phases_done"] = [p for p in state.get("phases_done", [])
                            if p in PHASE_IDS and PHASE_IDS.index(p) < target_idx]
    save_state(project, state)
    print(f"Reopened phase {target_idx + 1}: {phase_title(args.phase)}. "
          "Later phases will need to be completed again.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="agent-forge project helper")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", default=".", help="project root (default: current folder)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", parents=[common], help="create layout, templates and state")
    p_init.add_argument("--name", required=True, help="short agent name, e.g. ticket-triage")
    p_init.add_argument("--tier", choices=TIERS, default="pilot")
    p_init.add_argument("--mode", choices=MODES, default="agent_runs",
                        help="who runs code: the coding agent or the human")
    p_init.set_defaults(func=cmd_init)

    p_status = sub.add_parser("status", parents=[common], help="show where the project stands")
    p_status.set_defaults(func=cmd_status)

    p_approve = sub.add_parser("approve", parents=[common], help="record a checkpoint approval")
    p_approve.add_argument("checkpoint", choices=CHECKPOINTS)
    p_approve.add_argument("--by", choices=["user", "auto"], default="user")
    p_approve.add_argument("--note", default="")
    p_approve.set_defaults(func=cmd_approve)

    p_adv = sub.add_parser("advance", parents=[common], help="finish the current phase")
    p_adv.set_defaults(func=cmd_advance)

    p_goto = sub.add_parser("goto", parents=[common], help="reopen an earlier phase")
    p_goto.add_argument("phase", choices=PHASE_IDS)
    p_goto.set_defaults(func=cmd_goto)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
