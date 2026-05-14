"""
utilities/generate_stability_report.py

Reads reports/stability_log.txt and generates reports/stability_summary.md.
This is used by the 10x stability scripts to produce a simple proof summary.
"""

import os
import re
import sys


def _project_root() -> str:
    """Return the project root folder path."""
    return os.path.dirname(os.path.dirname(__file__))


def parse_stability_log(log_path: str):
    """Parse stability_log.txt lines into a list of run dicts."""
    runs = []
    if not os.path.exists(log_path):
        return runs

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("Run "):
                continue

            # Expected format:
            # Run 1: PASSED - 75/75 tests | Date: YYYY-MM-DD | Time taken: Xs
            m = re.match(
                r"Run\s+(?P<run>\d+):\s+(?P<status>PASSED|FAILED)\s+-\s+"
                r"(?P<p_passed>\d+)/(?P<p_total>\d+)\s+tests\s+\|\s+Date:\s+(?P<date>[^|]+)\|\s+"
                r"Time taken:\s+(?P<time>.+)$",
                line,
            )
            if not m:
                continue

            run_no = int(m.group("run"))
            status = m.group("status")
            passed = int(m.group("p_passed"))
            total = int(m.group("p_total"))
            failed = total - passed
            time_taken = m.group("time").strip()

            runs.append(
                {
                    "run": run_no,
                    "status": status,
                    "passed": passed,
                    "failed": failed,
                    "date": m.group("date").strip(),
                    "time": time_taken,
                    "total": total,
                }
            )

    return runs


def write_markdown_summary(runs, output_path: str):
    """Write a simple markdown summary table to stability_summary.md."""
    total_runs = len(runs)
    passed_runs = sum(1 for r in runs if r["status"] == "PASSED")
    failed_runs = total_runs - passed_runs
    totals = [r.get("passed", 0) + r.get("failed", 0) for r in runs]
    tests_per_run = max(totals) if totals else 0
    stability_pct = (passed_runs / total_runs * 100.0) if total_runs else 0.0

    lines = []
    lines.append("## Stability Summary (10 runs)")
    lines.append("")

    lines.append(f"- Total runs recorded: **{total_runs}**")
    if tests_per_run:
        lines.append(f"- Total tests per run (max observed): **{tests_per_run}**")
    lines.append(f"- Passed runs: **{passed_runs}**")
    lines.append(f"- Failed runs: **{failed_runs}**")
    lines.append(f"- Overall stability: **{stability_pct:.1f}%** (passed runs / total runs)")
    lines.append("")

    lines.append("| Run # | Date | Total Tests | Passed | Failed | Stability % | Time |")
    lines.append("|---:|---|---:|---:|---:|---:|---|")

    for r in sorted(runs, key=lambda x: x["run"]):
        total = (r.get("passed", 0) + r.get("failed", 0)) or 0
        run_pct = ((r.get("passed", 0) / total) * 100.0) if total else 0.0
        lines.append(
            f"| {r['run']} | {r.get('date','').strip()} | {total} | {r['passed']} | {r['failed']} | {run_pct:.1f}% | {r['time']} |"
        )

    lines.append("")

    if failed_runs == 0 and total_runs == 10:
        lines.append("**Final verdict:** All 10 runs passed with 100% stability")
    else:
        bad = [str(r["run"]) for r in runs if r["status"] == "FAILED"]
        lines.append(f"**Final verdict:** UNSTABLE. Failed runs: {', '.join(bad) if bad else 'N/A'}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return total_runs, passed_runs, failed_runs


def main():
    """Entry point used by the shell/bat scripts.

    Optional args:
    - argv[1] = input log path (default: reports/stability_log.txt)
    - argv[2] = output md path (default: reports/stability_summary.md)
    """
    root = _project_root()
    default_log = os.path.join(root, "reports", "stability_log.txt")
    default_md = os.path.join(root, "reports", "stability_summary.md")

    log_path = sys.argv[1] if len(sys.argv) > 1 else default_log
    md_path = sys.argv[2] if len(sys.argv) > 2 else default_md

    runs = parse_stability_log(log_path)
    total, passed, failed = write_markdown_summary(runs, md_path)

    print("STABILITY REPORT")
    print(f"Total Runs: {total}")
    print(f"Passed Runs: {passed}")
    print(f"Failed Runs: {failed}")
    print(f"Markdown written to: {md_path}")


if __name__ == "__main__":
    main()

