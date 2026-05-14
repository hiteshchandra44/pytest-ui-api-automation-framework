#!/usr/bin/env bash
#
# run_tests.sh
#
# Simple test runner for Mac/Linux.
# Make executable: chmod +x run_tests.sh

set -e

echo "Default run (all tests + full report)"
python -m pytest -c pytest_all.ini

echo "UI only (UI report)"
python -m pytest -c pytest_ui.ini

echo "API only (API report)"
python -m pytest -c pytest_api.ini

echo "Chrome run (all tests + full report)"
python -m pytest -c pytest_all.ini --browser=chrome

echo "Firefox run (all tests + full report)"
python -m pytest -c pytest_all.ini --browser=firefox

