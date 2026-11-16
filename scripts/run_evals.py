#!/usr/bin/env python3
"""Run agent-forge eval cases against an agent and score them.

Commands:
  run         run every case (or a subset) and write evals/results/run-<time>.json
  summarize   recompute scores for a results file after judge grades were filled in
  validate    check evals/cases.jsonl without running anything

The agent is invoked as described in forge/eval_config.json (see references/evals.md).
Standard library only, Python 3.9+. Output is ASCII so it prints on any console.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

GRADER_FIELDS = {
    "contains": ["value"],
    "not_contains": ["value"],
    "regex": ["pattern"],
    "equals": ["value"],
    "json_field": ["path", "value"],
    "tool_called": ["name"],
    "tool_not_called": ["name"],
    "max_tool_calls": ["value"],
    "exit_code": ["value"],
    "judge": ["rubric"],
}
OUTPUT_LIMIT = 8000
STDERR_LIMIT = 1500
MAX_TOOL_CALLS_STORED = 50
_MISSING = object()


# ---------------------------------------------------------------- loading

def load_cases(path: Path) -> list[dict]:
    """Read a JSONL file of cases. Blank lines and lines starting with '#' are skipped."""
    if not path.exists():
        raise SystemExit(f"Cases file not found: {path}")
    cases = []
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            try:
                case = json.loads(text)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{lineno}: invalid JSON: {exc}")
            if not isinstance(case, dict):
                raise SystemExit(f"{path}:{lineno}: each line must be a JSON object")
            case["_line"] = lineno
            cases.append(case)
    return cases


def validate_cases(cases: list[dict]) -> list[str]:
    """Return a list of problems; empty means the cases are valid."""
    problems = []
    seen = set()
    for case in cases:
        where = f"line {case.get('_line', '?')}"
        cid = case.get("id")
        if not isinstance(cid, str) or not cid.strip():
            problems.append(f"{where}: missing string 'id'")
        elif cid in seen:
            problems.append(f"{where}: duplicate id '{cid}'")
        else:
            seen.add(cid)
        if "input" not in case:
            problems.append(f"{where} ({cid}): missing 'input'")
        if not isinstance(case.get("category"), str):
            problems.append(f"{where} ({cid}): missing string 'category'")
        graders = case.get("graders")
        if not isinstance(graders, list) or not graders:
            problems.append(f"{where} ({cid}): needs at least one grader")
            continue
        for i, grader in enumerate(graders):
            if not isinstance(grader, dict):
                problems.append(f"{where} ({cid}): grader {i} is not an object")
                continue
            gtype = grader.get("type")
            if gtype not in GRADER_FIELDS:
                problems.append(f"{where} ({cid}): grader {i} has unknown type '{gtype}'")
                continue
            for field in GRADER_FIELDS[gtype]:
                if field not in grader:
                    problems.append(f"{where} ({cid}): {gtype} grader needs '{field}'")
            if gtype == "regex" and "pattern" in grader:
                try:
                    re.compile(grader["pattern"])
                except re.error as exc:
                    problems.append(f"{where} ({cid}): bad regex: {exc}")
            if gtype in ("max_tool_calls", "exit_code") and not isinstance(grader.get("value"), int):
                problems.append(f"{where} ({cid}): {gtype} value must be an integer")
    return problems


def load_config(project: Path) -> dict:
    path = project / "forge" / "eval_config.json"
    if not path.exists():
        raise SystemExit(f"Missing {path}. Run forge.py init or create it (references/evals.md).")
    config = json.loads(path.read_text(encoding="utf-8"))
    command = config.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(c, str) for c in command):
        raise SystemExit("eval_config.json: 'command' must be a non-empty list of strings")
    if any("TODO" in c for c in command):
        raise SystemExit("eval_config.json: 'command' still contains a TODO placeholder")
    return config


# ---------------------------------------------------------------- running

def _get_path(obj, path: str):
    """Resolve a dotted path; strings met along the way are parsed as JSON if possible."""
    current = obj
    for part in path.split("."):
        if isinstance(current, str):
            try:
                current = json.loads(current)
            except json.JSONDecodeError:
                return _MISSING
        if isinstance(current, list) and part.isdigit():
            idx = int(part)
            if idx >= len(current):
                return _MISSING
            current = current[idx]
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return _MISSING
    return current


def apply_grader(grader: dict, result: dict, returncode) -> dict:
    gtype = grader["type"]
    output = result.get("output", "")
    if not isinstance(output, str):
        output = json.dumps(output, ensure_ascii=False)
    calls = [c.get("name") for c in (result.get("tool_calls") or []) if isinstance(c, dict)]
    record = dict(grader)

    if gtype in ("contains", "not_contains"):
        needle = str(grader["value"])
        hay = output
        if not grader.get("case_sensitive", False):
            needle, hay = needle.lower(), hay.lower()
        found = needle in hay
        record["passed"] = found if gtype == "contains" else not found
        record["detail"] = "found" if found else "not found"
    elif gtype == "regex":
        match = re.search(grader["pattern"], output, re.DOTALL)
        record["passed"] = match is not None
        record["detail"] = "matched" if match else "no match"
    elif gtype == "equals":
        record["passed"] = output.strip() == str(grader["value"]).strip()
        record["detail"] = "equal" if record["passed"] else "different"
    elif gtype == "json_field":
        value = _get_path(result, grader["path"])
        record["passed"] = value is not _MISSING and value == grader["value"]
        record["detail"] = "missing" if value is _MISSING else f"got {json.dumps(value)[:200]}"
    elif gtype == "tool_called":
        record["passed"] = grader["name"] in calls
        record["detail"] = f"calls: {calls[:20]}"
    elif gtype == "tool_not_called":
        record["passed"] = grader["name"] not in calls
        record["detail"] = f"calls: {calls[:20]}"
    elif gtype == "max_tool_calls":
        record["passed"] = len(calls) <= grader["value"]
        record["detail"] = f"{len(calls)} calls"
    elif gtype == "exit_code":
        record["passed"] = returncode == grader["value"]
        record["detail"] = f"exit code {returncode}"
    elif gtype == "judge":
        record["passed"] = None
        record["detail"] = "pending: grade against the rubric, then run 'summarize'"
    return record


def trial_status(trial: dict):
    """True / False / None (pending judge grades). Errors always fail."""
    if trial.get("error"):
        return False
    graders = trial.get("graders", [])
    if any(g.get("passed") is False for g in graders):
        return False
    if any(g.get("passed") is None for g in graders):
        return None
    return True


def run_trial(case: dict, config: dict, project: Path, trial_no: int) -> dict:
    command = list(config["command"])
    raw_input = case["input"]
    input_text = raw_input if isinstance(raw_input, str) else json.dumps(raw_input, ensure_ascii=False)
    stdin_data = None
    if config.get("input_mode", "stdin") == "arg":
        command.append(input_text)
    else:
        stdin_data = input_text

    env = os.environ.copy()
    env.update({str(k): str(v) for k, v in (config.get("env") or {}).items()})
    env["FORGE_EVAL"] = "1"
    env["FORGE_CASE_ID"] = str(case["id"])
    env.setdefault("PYTHONIOENCODING", "utf-8")
    timeout = config.get("timeout_s", 120)

    trial = {"trial": trial_no, "error": None, "returncode": None, "duration_s": None,
             "output": "", "tool_calls": [], "usage": {}, "stderr_tail": "", "graders": []}
    start = time.monotonic()
    try:
        proc = subprocess.run(command, input=stdin_data, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout,
                              cwd=str(project), env=env)
    except subprocess.TimeoutExpired:
        trial["duration_s"] = round(time.monotonic() - start, 3)
        trial["error"] = f"timeout after {timeout}s"
        trial["passed"] = False
        return trial
    except OSError as exc:
        trial["error"] = f"could not start agent: {exc}"
        trial["passed"] = False
        return trial
    trial["duration_s"] = round(time.monotonic() - start, 3)
    trial["returncode"] = proc.returncode
    stdout = proc.stdout or ""
    trial["stderr_tail"] = (proc.stderr or "")[-STDERR_LIMIT:]

    result = {"output": stdout.strip(), "tool_calls": [], "usage": {}}
    if config.get("output_format", "json") == "json":
        lines = [line for line in stdout.splitlines() if line.strip()]
        parsed = None
        if lines:
            try:
                parsed = json.loads(lines[-1])
            except json.JSONDecodeError:
                try:
                    parsed = json.loads(stdout)
                except json.JSONDecodeError:
                    parsed = None
        if isinstance(parsed, dict) and "output" in parsed:
            result = parsed
        else:
            trial["error"] = "last line of stdout is not a JSON object with an 'output' field"

    output = result.get("output", "")
    if not isinstance(output, str):
        output = json.dumps(output, ensure_ascii=False)
    trial["output"] = output[:OUTPUT_LIMIT]
    calls = result.get("tool_calls") or []
    trial["tool_calls"] = calls[:MAX_TOOL_CALLS_STORED] if isinstance(calls, list) else []
    trial["usage"] = result.get("usage") if isinstance(result.get("usage"), dict) else {}

    graders = case["graders"]
    trial["graders"] = [apply_grader(g, result, proc.returncode) for g in graders]
    if not any(g["type"] == "exit_code" for g in graders):
        trial["graders"].append({"type": "exit_code", "value": 0, "implicit": True,
                                 "passed": proc.returncode == 0,
                                 "detail": f"exit code {proc.returncode}"})
    trial["passed"] = trial_status(trial)
    return trial


# ---------------------------------------------------------------- scoring

def _mean(values):
    values = list(values)
    return round(sum(values) / len(values), 4) if values else None


def _aggregate(rows: list[dict]) -> dict:
    graded = [r for r in rows if not r["pending"] and r["n"] > 0]
    return {
        "cases": len(rows),
        "graded": len(graded),
        "pending": len(rows) - len(graded),
        "pass_at_1": _mean(r["passes"] / r["n"] for r in graded),
        "pass_at_k": _mean(1.0 if r["passes"] >= 1 else 0.0 for r in graded),
        "pass_hat_k": _mean(1.0 if r["passes"] == r["n"] else 0.0 for r in graded),
    }


def compute_summary(case_results: list[dict]) -> dict:
    rows = []
    durations, costs = [], []
    for case in case_results:
        trials = case.get("trials", [])
        for t in trials:
            t["passed"] = trial_status(t)
            if t.get("duration_s") is not None:
                durations.append(t["duration_s"])
            cost = (t.get("usage") or {}).get("cost_usd")
            if isinstance(cost, (int, float)):
                costs.append(cost)
        rows.append({
            "id": case["id"],
            "category": case.get("category", "uncategorised"),
            "n": len(trials),
            "passes": sum(1 for t in trials if t["passed"] is True),
            "pending": any(t["passed"] is None for t in trials),
        })
    by_category = {}
    for cat in sorted({r["category"] for r in rows}):
        by_category[cat] = _aggregate([r for r in rows if r["category"] == cat])
    durations.sort()
    p95 = durations[min(len(durations) - 1, int(round(0.95 * (len(durations) - 1))))] if durations else None
    return {
        "overall": _aggregate(rows),
        "by_category": by_category,
        "trials_per_case": min((r["n"] for r in rows), default=0),
        "latency_s": {"mean": _mean(durations), "p95": p95},
        "cost_usd": {"total": round(sum(costs), 6) if costs else None,
                     "mean_per_trial": _mean(costs)},
        "failed_cases": [r["id"] for r in rows if not r["pending"] and r["passes"] < r["n"]],
        "pending_cases": [r["id"] for r in rows if r["pending"]],
    }


def print_summary(summary: dict) -> None:
    def fmt(v):
        return "-" if v is None else f"{v:.2f}"
    print(f"{'category':<16}{'cases':>6}{'pass@1':>9}{'pass@k':>9}{'pass^k':>9}{'pending':>9}")
    for cat, agg in summary["by_category"].items():
        print(f"{cat:<16}{agg['cases']:>6}{fmt(agg['pass_at_1']):>9}{fmt(agg['pass_at_k']):>9}"
              f"{fmt(agg['pass_hat_k']):>9}{agg['pending']:>9}")
    o = summary["overall"]
    print(f"{'OVERALL':<16}{o['cases']:>6}{fmt(o['pass_at_1']):>9}{fmt(o['pass_at_k']):>9}"
          f"{fmt(o['pass_hat_k']):>9}{o['pending']:>9}")
    print(f"trials per case: {summary['trials_per_case']}   "
          f"latency mean/p95: {summary['latency_s']['mean']}/{summary['latency_s']['p95']} s   "
          f"cost total: {summary['cost_usd']['total']}")
    if summary["failed_cases"]:
        print("failed: " + ", ".join(summary["failed_cases"][:30]))
    if summary["pending_cases"]:
        print("pending judge grades: " + ", ".join(summary["pending_cases"][:30]))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


# ---------------------------------------------------------------- commands

def cmd_validate(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    cases = load_cases(project / "evals" / "cases.jsonl")
    problems = validate_cases(cases)
    counts = {}
    for case in cases:
        counts[case.get("category", "?")] = counts.get(case.get("category", "?"), 0) + 1
    print(f"{len(cases)} cases: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    if problems:
        print("Problems:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print("Cases are valid.")


def cmd_run(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    config = load_config(project)
    cases = load_cases(project / "evals" / "cases.jsonl")
    problems = validate_cases(cases)
    if problems:
        print("Fix these case problems first:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    partial = False
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        cases = [c for c in cases if c["id"] in wanted]
        partial = True
    if args.category:
        cases = [c for c in cases if c.get("category") == args.category]
        partial = True
    if not cases:
        sys.exit("No cases selected.")

    trials = args.trials or int(config.get("trials", 1))
    run_id = dt.datetime.now().strftime("run-%Y%m%d-%H%M%S")
    print(f"{run_id}: {len(cases)} cases x {trials} trials{' (partial run)' if partial else ''}")

    case_results = []
    for case in cases:
        trial_records = []
        for t in range(1, trials + 1):
            record = run_trial(case, config, project, t)
            trial_records.append(record)
            mark = {True: "pass", False: "FAIL", None: "pending"}[record["passed"]]
            extra = f" ({record['error']})" if record.get("error") else ""
            print(f"  {case['id']} trial {t}: {mark}{extra}")
        case_results.append({"id": case["id"], "category": case.get("category"),
                             "feature": case.get("feature"), "input": case["input"],
                             "trials": trial_records})

    summary = compute_summary(case_results)
    results = {
        "run_id": run_id,
        "created": dt.datetime.now().isoformat(timespec="seconds"),
        "partial": partial,
        "trials": trials,
        "config": {k: v for k, v in config.items() if k != "env"},
        "case_ids": [c["id"] for c in case_results],
        "summary": summary,
        "cases": case_results,
    }
    out_dir = project / "evals" / "results"
    out_path = out_dir / f"{run_id}.json"
    write_json(out_path, results)
    if not partial:
        write_json(out_dir / "latest.json", results)
    print()
    print_summary(summary)
    print(f"\nResults: {out_path}")
    if partial:
        print("Partial run: latest.json was not updated. Run all cases before the readiness gate.")


def cmd_summarize(args: argparse.Namespace) -> None:
    path = Path(args.results).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    data["summary"] = compute_summary(data.get("cases", []))
    write_json(path, data)
    latest = path.parent / "latest.json"
    if not data.get("partial") and path.name != "latest.json":
        if latest.exists():
            try:
                current = json.loads(latest.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                current = {}
            if current.get("run_id") == data.get("run_id"):
                write_json(latest, data)
    print_summary(data["summary"])


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="agent-forge eval runner")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", default=".", help="project root (default: current folder)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", parents=[common], help="run the eval cases")
    p_run.add_argument("--trials", type=int, default=0, help="trials per case (default from config)")
    p_run.add_argument("--only", default="", help="comma-separated case ids")
    p_run.add_argument("--category", default="", help="run one category only")
    p_run.set_defaults(func=cmd_run)

    p_sum = sub.add_parser("summarize", parents=[common], help="rescore a results file")
    p_sum.add_argument("results", help="path to a results JSON file")
    p_sum.set_defaults(func=cmd_summarize)

    p_val = sub.add_parser("validate", parents=[common], help="check cases.jsonl")
    p_val.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
