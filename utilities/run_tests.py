"""
utilities/run_tests.py

Run pytest with a timestamped HTML report under reports/.
INI files do not set --html so runs here do not overwrite previous reports.

Usage:
  python utilities/run_tests.py ui
  python utilities/run_tests.py api
  python utilities/run_tests.py all
  python utilities/run_tests.py stability
  python utilities/run_tests.py stability --path tests/ui --report-prefix ui_run
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")

# suite -> (config ini, default test paths, default report filename prefix)
SUITES: dict[str, tuple[str, list[str], str]] = {
    "ui": ("pytest_ui.ini", ["tests/ui"], "ui_report"),
    "api": ("pytest_api.ini", ["tests/api"], "api_report"),
    "all": ("pytest_all.ini", ["tests"], "full_report"),
    "stability": ("pytest_stability.ini", ["tests"], "stability_report"),
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run pytest with a timestamped HTML report in reports/."
    )
    parser.add_argument(
        "suite",
        choices=["ui", "api", "stability", "all"],
        help="Suite type: config file and default paths/report name",
    )
    parser.add_argument(
        "--path",
        dest="paths",
        nargs="+",
        default=None,
        metavar="PATH",
        help="Override test path(s) (default: suite-specific). Used by stability batches.",
    )
    parser.add_argument(
        "--report-prefix",
        default=None,
        metavar="PREFIX",
        help="Override report base name before timestamp (default: suite-specific).",
    )
    args = parser.parse_args()

    ini_name, default_paths, default_prefix = SUITES[args.suite]
    paths = args.paths if args.paths is not None else list(default_paths)
    prefix = args.report_prefix if args.report_prefix is not None else default_prefix

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    html_filename = f"{prefix}_{timestamp}.html"
    os.makedirs(REPORTS_DIR, exist_ok=True)
    html_rel = os.path.join("reports", html_filename).replace("\\", "/")
    html_abs = os.path.join(REPORTS_DIR, html_filename)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-c",
        ini_name,
        *paths,
        f"--html={html_rel}",
        "--self-contained-html",
    ]

    # Print to stderr so batch wrappers can still parse stdout reliably.
    print("Running:", " ".join(cmd), file=sys.stderr)
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    print(f"Report file: {html_abs}", file=sys.stderr)
    return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
