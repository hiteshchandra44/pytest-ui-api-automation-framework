"""
conftest.py

This file contains Pytest fixtures that are shared across all tests.

What we provide:
- A session-scoped "config" fixture that reads config/config.ini once per test session.
- A function-scoped "driver" fixture that starts a browser before each test and quits after (tests/page objects perform navigation).
- A function-scoped "api_client" fixture that returns an APIClient instance.
- A function-scoped "auth_token" fixture that logs in via API (config credentials) once per test and returns a token string.
- A pytest_configure hook that auto-generates timestamped HTML report and log file under reports/.
"""

# Pytest is used for fixtures.
import pytest

# configparser is used to read INI files in a beginner-friendly way.
import configparser

# os is used to build file paths reliably.
import os

# datetime is used to generate timestamped report/log filenames.
from datetime import datetime

# Selenium WebDriver and browser options.
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# webdriver-manager downloads the correct browser driver automatically.
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

# Selenium service classes are used to start the driver executables.
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService

# Our small utilities for reading single config values and logging.
from utilities.config_reader import read_config
from utilities.logger import get_logger
from utilities.api_client import APIClient

# time is used to generate unique registration emails.
import time


# ---------------------------------------------------------------------------
# Timestamped HTML report + log file
# ---------------------------------------------------------------------------
def pytest_configure(config):
    """
    Runs early at pytest startup (before collection).
    Injects a timestamped --html report path and log_file path so that
    every test run produces uniquely named output files under reports/.

    File naming:
        reports/api_report_YYYY-MM-DD_HH-MM-SS.html
        reports/api_log_YYYY-MM-DD_HH-MM-SS.txt
    The prefix (api / ui / stability / all) is derived from the active .ini file.
    """
    # Determine suite prefix from whichever .ini file was loaded.
    ini_file = config.inifile  # e.g. PosixPath('pytest_api.ini') or None
    if ini_file:
        name = os.path.basename(str(ini_file))                    # "pytest_api.ini"
        prefix = name.replace("pytest_", "").replace(".ini", "")  # "api"
    else:
        prefix = "all"

    # Single timestamp shared by both the HTML report and the log file.
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Ensure reports/ directory exists.
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    # --- HTML report (pytest-html) ----------------------------------------
    # Only set if pytest-html is installed and --html wasn't already passed on CLI.
    html_path = os.path.join(reports_dir, f"{prefix}_report_{timestamp}.html")
    if config.pluginmanager.hasplugin("html"):
        if not config.option.__dict__.get("htmlpath"):
            config.option.htmlpath = html_path
            config.option.self_contained_html = True  # portable single file

    # --- Plain-text log file ------------------------------------------------
    log_path = os.path.join(reports_dir, f"{prefix}_log_{timestamp}.txt")
    config.inicfg["log_file"]             = log_path
    config.inicfg["log_file_level"]       = config.inicfg.get("log_file_level", "DEBUG")
    config.inicfg["log_file_format"]      = config.inicfg.get(
        "log_file_format",
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    )
    config.inicfg["log_file_date_format"] = config.inicfg.get(
        "log_file_date_format", "%Y-%m-%d %H:%M:%S"
    )


# ---------------------------------------------------------------------------
# HTML report title
# ---------------------------------------------------------------------------

# This hook customizes the pytest-html report title.
def pytest_html_report_title(report):
    # Set a friendly title for the generated HTML report.
    report.title = "Automation Test Report"


# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------

# This adds a custom command line option:
# Example: pytest --browser=firefox
def pytest_addoption(parser):
    # --browser overrides the browser value from config.ini.
    parser.addoption("--browser", action="store", default=None)


# ---------------------------------------------------------------------------
# Session fixtures
# ---------------------------------------------------------------------------

# This fixture logs once at the start of the session which browser will be used.
@pytest.fixture(scope="session", autouse=True)
def log_browser_choice(request):
    # Create a logger for session startup.
    logger = get_logger("session")

    # Read browser from CLI if provided; otherwise read from config.ini.
    cli_browser = request.config.getoption("--browser")
    config_browser = read_config("browser", "browser").strip().lower()
    chosen = (cli_browser or config_browser).strip().lower()

    # Log the chosen browser for clarity.
    logger.info(f"Test session browser: {chosen}")


# This fixture reads config/config.ini once and returns a ConfigParser object.
@pytest.fixture(scope="session")
def config():
    # Create a ConfigParser instance to hold all INI settings.
    parser = configparser.ConfigParser()

    # Build the absolute path to config/config.ini.
    project_root = os.path.dirname(__file__)
    config_path = os.path.join(project_root, "config", "config.ini")

    # Read the INI file.
    parser.read(config_path)

    # Return the parser so tests (or fixtures) can read any value they need.
    return parser


# ---------------------------------------------------------------------------
# Browser fixture
# ---------------------------------------------------------------------------

# This fixture starts a browser before each test and closes it after the test finishes.
@pytest.fixture(scope="function")
def driver(request):
    # Create a logger for browser lifecycle messages.
    logger = get_logger("driver_fixture")

    # Read browser name from CLI option if provided; otherwise fall back to config.ini.
    cli_browser = request.config.getoption("--browser")
    browser_name = (cli_browser or read_config("browser", "browser")).strip().lower()

    # Read the headless flag from config.ini and convert it to a boolean.
    # If config.ini has headless = true, this becomes True; otherwise False.
    headless = read_config("browser", "headless").strip().lower() == "true"

    # Read timeouts from config.ini.
    implicit_wait_seconds = int(read_config("timeouts", "implicit_wait"))
    try:
        page_load_seconds = int(read_config("timeouts", "page_load_timeout"))
    except Exception:
        # Backward-compatible fallback for older config key.
        page_load_seconds = int(read_config("timeouts", "page_load"))

    # Create the driver based on the browser name.
    if browser_name == "chrome":
        # Create Chrome options.
        chrome_options = ChromeOptions()
        chrome_options.page_load_strategy = "eager"

        # If headless is enabled, apply headless mode + common stability flags.
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

        # Start Chrome using webdriver-manager (no manual driver setup).
        web_driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=chrome_options,
        )

    elif browser_name == "firefox":
        # Create Firefox options.
        firefox_options = FirefoxOptions()
        firefox_options.page_load_strategy = "eager"

        # If headless is enabled, apply Firefox headless flag.
        if headless:
            firefox_options.add_argument("--headless")

        # Start Firefox using webdriver-manager (no manual driver setup).
        web_driver = webdriver.Firefox(
            service=FirefoxService(GeckoDriverManager().install()),
            options=firefox_options,
        )

    else:
        # If the config value is not supported, fail fast with a clear error.
        raise ValueError(f"Unsupported browser in config.ini: '{browser_name}'. Use 'chrome' or 'firefox'.")

    # Apply implicit wait (this affects find_element calls).
    web_driver.implicitly_wait(implicit_wait_seconds)

    # Apply page load timeout.
    web_driver.set_page_load_timeout(page_load_seconds)

    # Page objects navigate via their open() methods; no initial URL load here.
    logger.info(f"Browser started: {browser_name}, headless={headless}")

    # Provide the driver to the test.
    yield web_driver

    # If the test failed, take a screenshot to help debugging.
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        # Build the screenshots folder inside reports/.
        screenshots_dir = os.path.join(os.path.dirname(__file__), "reports", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)

        # Build a simple screenshot filename from the test name.
        screenshot_path = os.path.join(screenshots_dir, f"{request.node.name}.png")

        # Log and save the screenshot.
        logger.info(f"Test failed. Saving screenshot: {screenshot_path}")
        web_driver.save_screenshot(screenshot_path)

    # Quit the browser after the test finishes.
    logger.info("Quitting browser")
    web_driver.quit()


# ---------------------------------------------------------------------------
# API fixtures
# ---------------------------------------------------------------------------

# This fixture creates a new API client for each test (simple + isolated).
@pytest.fixture(scope="function")
def api_client():
    # Return a ready-to-use APIClient instance.
    return APIClient()


# This fixture logs in via API and returns a fresh auth token per test.
@pytest.fixture(scope="function")
def auth_token(api_client):
    resp = api_client.post(
        "users/login",
        payload={
            "email": read_config("api", "username").strip(),
            "password": read_config("api", "password").strip(),
        },
    )
    body = resp.json() or {}
    token = (
        body.get("token")
        or body.get("access_token")
        or (body.get("data") or {}).get("token")
        or ""
    )
    return token


# ---------------------------------------------------------------------------
# Setup / teardown logging + result capture
# ---------------------------------------------------------------------------

# This fixture logs SETUP before a test and TEARDOWN after a test.
@pytest.fixture(scope="function", autouse=True)
def setup_teardown(request):
    # Create a logger for setup/teardown messages.
    logger = get_logger("setup_teardown")

    # Log setup message before the test runs.
    logger.info(f"SETUP: {request.node.nodeid}")

    # Run the test.
    yield

    # Log teardown message after the test completes.
    logger.info(f"TEARDOWN: {request.node.nodeid}")


# This hook captures the test result so fixtures can check pass/fail.
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    # Let pytest run the actual reporting first.
    outcome = yield

    # Get the generated test report for this phase (setup/call/teardown).
    rep = outcome.get_result()

    # Attach report objects to the item so fixtures can access them.
    setattr(item, f"rep_{rep.when}", rep)

    # Log pass/fail for the test call phase (the actual test body).
    if rep.when == "call":
        logger = get_logger("test_result")
        if rep.failed:
            logger.info(f"FAIL: {item.nodeid}")
        else:
            logger.info(f"PASS: {item.nodeid}")