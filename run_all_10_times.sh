#!/usr/bin/env bash
#
# run_all_10_times.sh
#
# Runs `python utilities/run_tests.py stability` 10 times (timestamped HTML per run):
# - UI reports:  reports/ui_run_YYYY-MM-DD_HH-MM-SS.html
# - API reports: reports/api_run_YYYY-MM-DD_HH-MM-SS.html
# - FULL reports: reports/stability_run_YYYY-MM-DD_HH-MM-SS.html (UI+API together, 75 tests)
# It also writes plain-text stability logs and markdown summaries.

# We do NOT use `set -e` because we want to continue all 10 runs even if one fails.
set +e

mkdir -p reports

run_suite_10x () {
  suite_name="$1"        # UI or API
  suite_path="$2"        # tests/ui or tests/api
  report_prefix="$3"     # ui_run or api_run
  expected_total="$4"    # expected test count as string (e.g., 25 or 50)

  passes=0
  fails=0

  log_file="reports/${suite_name,,}_stability_log.txt"
  summary_md="reports/${suite_name,,}_stability_summary.md"

  echo "${suite_name} stability log started" > "${log_file}"

  for i in $(seq 1 10); do
    echo "=== ${suite_name} Run $i/10 ==="

    start_seconds=${SECONDS}

    # Run only the selected suite path using the stability config (NO reruns); timestamped HTML.
    python utilities/run_tests.py stability --path "${suite_path}" --report-prefix "${report_prefix}_${i}"
    exit_code=$?

    time_taken=$((SECONDS - start_seconds))
    today=$(date +%F)

    if [ "${exit_code}" -eq 0 ]; then
      status="PASSED"
      passes=$((passes+1))
      passed_count="${expected_total}/${expected_total}"
    else
      status="FAILED"
      fails=$((fails+1))
      passed_count="0/${expected_total}"
    fi

    echo "Run ${i}: ${status} - ${passed_count} tests | Date: ${today} | Time taken: ${time_taken}s" >> "${log_file}"
  done

  if [ "${fails}" -eq 0 ]; then
    overall="STABLE"
  else
    overall="UNSTABLE"
  fi

  echo "================================"
  echo "STABILITY SUMMARY (${suite_name})"
  echo "Total Runs: 10"
  echo "Passed Runs: ${passes}"
  echo "Failed Runs: ${fails}"
  echo "Overall Result: ${overall}"
  echo "================================"

  # Generate markdown summary for this suite.
  python "utilities/generate_stability_report.py" "${log_file}" "${summary_md}"
}

# FULL SUITE: 75 tests (UI + API together) — required for assessment evidence
run_suite_10x "FULL" "tests" "stability_run" "75"

# UI: 25 tests
run_suite_10x "UI" "tests/ui" "ui_run" "25"

# API: 50 tests
run_suite_10x "API" "tests/api" "api_run" "50"
