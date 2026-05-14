"""
tests/ui/test_login.py

This file contains UI tests for the Notes App login functionality (/notes/app/login).

We use the LoginPage (POM) to keep tests clean and readable.
"""

# Import pytest for test structure and skipping when config is missing.
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Import our page objects.
from pages.login_page import LoginPage
from pages.notes_page import NotesPage

# Import logger utility.
from utilities.logger import get_logger

# Import config reader so we never hardcode credentials or URLs in tests.
from utilities.config_reader import read_config


# Create a module-level logger so each test can log a start message.
logger = get_logger(__name__)


def _get_valid_credentials():
    """
    Read username/password from config.ini.

    If they are not provided, skip tests that require valid login.
    """
    username = read_config("api", "username").strip()
    password = read_config("api", "password").strip()

    # If credentials are missing, return empty values.
    return username, password


def _login(driver, email: str, password: str):
    """
    Helper that performs login using the LoginPage.
    """
    login_page = LoginPage(driver)
    login_page.open()
    login_page.enter_email(email)
    login_page.enter_password(password)
    login_page.click_login()
    return login_page


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.positive
def test_valid_login(driver):
    """Check that a user can log in with correct credentials."""
    logger.info("Running test: test_valid_login")

    email, password = _get_valid_credentials()
    if not email or not password or "(" in email:
        pytest.skip("Valid Notes App credentials are missing in config.ini under [api] username/password.")

    login_page = _login(driver, email, password)
    logger.info(f"URL after login click: {driver.current_url}")

    assert login_page.is_login_successful(), "Login should succeed with valid credentials."


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.negative
def test_invalid_password(driver):
    """Check that login fails with a wrong password and shows an error."""
    logger.info("Running test: test_invalid_password")

    email, _ = _get_valid_credentials()
    if not email or "(" in email:
        pytest.skip("Valid Notes App email is missing in config.ini under [api] username.")

    wrong_password = read_config("api", "wrong_password").strip()
    if not wrong_password:
        pytest.skip("wrong_password is missing in config.ini under [api].")

    login_page = _login(driver, email, wrong_password)

    assert login_page.is_displayed(LoginPage.ERROR_MESSAGE), "Error message should be displayed for invalid password."


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.negative
def test_invalid_username(driver):
    """Check that login fails when username is not a valid email format."""
    logger.info("Running test: test_invalid_username")

    login_page = _login(driver, "invalid-email-format", "somepassword")

    assert not login_page.is_login_successful(), "Login should not succeed with invalid email format."
    assert "login" in driver.current_url.lower(), f"Expected to remain on login page, got: {driver.current_url}"


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.negative
def test_empty_username(driver):
    """Check that login fails when username is empty."""
    logger.info("Running test: test_empty_username")

    login_page = _login(driver, "", "somepassword")

    assert not login_page.is_login_successful(), "Login should not succeed with empty email."
    assert "login" in driver.current_url.lower(), f"Expected to remain on login page, got: {driver.current_url}"


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.negative
def test_empty_password(driver):
    """Check that login fails when password is empty."""
    logger.info("Running test: test_empty_password")

    email = read_config("api", "username")
    if not email:
        pytest.skip("username is missing in config.ini under [api].")

    login_page = _login(driver, email, "")

    assert not login_page.is_login_successful(), "Login should not succeed with empty password."
    assert "login" in driver.current_url.lower(), f"Expected to remain on login page, got: {driver.current_url}"


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.negative
def test_both_fields_empty(driver):
    """Check that login fails when both username and password are empty."""
    logger.info("Running test: test_both_fields_empty")

    login_page = _login(driver, "", "")

    assert not login_page.is_login_successful(), "Login should not succeed with empty credentials."
    assert "login" in driver.current_url.lower(), f"Expected to remain on login page, got: {driver.current_url}"


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.positive
def test_login_page_title(driver):
    """Verify the login page is opened (Notes App login URL)."""
    logger.info("Running test: test_login_page_title")

    login_page = LoginPage(driver)
    login_page.open()

    assert "notes/app/login" in driver.current_url.lower(), f"Expected Notes App login URL, got: {driver.current_url}"


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.positive
def test_login_redirects_to_notes(driver):
    """After successful login, verify the user is redirected to the Notes area."""
    logger.info("Running test: test_login_redirects_to_notes")

    email, password = _get_valid_credentials()
    if not email or not password or "(" in email:
        pytest.skip("Valid Notes App credentials are missing in config.ini under [api] username/password.")

    _login(driver, email, password)

    assert "notes/app" in driver.current_url.lower(), f"Expected to be on Notes App, but URL is: {driver.current_url}"


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.positive
def test_logout_after_login(driver):
    """Login, then logout, and verify user returns to a logged-out page."""
    logger.info("Running test: test_logout_after_login")

    email, password = _get_valid_credentials()
    if not email or not password or "(" in email:
        pytest.skip("Valid Notes App credentials are missing in config.ini under [api] username/password.")

    _login(driver, email, password)

    notes_page = NotesPage(driver)
    notes_page.open()
    notes_page.logout()
    from selenium.webdriver.support.ui import WebDriverWait
    WebDriverWait(driver, 10).until(lambda d: "login" in d.current_url)

    assert "login" in driver.current_url.lower(), f"Expected redirect to login after logout, got: {driver.current_url}"


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.negative
def test_invalid_email_format(driver):
    """Use 'notanemail' as username and verify login shows an error."""
    logger.info("Running test: test_invalid_email_format")

    logger.info(
        "LoginPage.ERROR_MESSAGE locator tuple (verify against DOM): %s",
        LoginPage.ERROR_MESSAGE,
    )

    login_page = _login(driver, "notanemail", "somepassword")

    invalid_email_feedback_xpath = (
        "//div[contains(@class,'alert') or contains(@class,'error') or "
        "contains(@class,'invalid-feedback')][string-length(text()) > 0]"
    )
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.XPATH, invalid_email_feedback_xpath))
    )
    assert login_page.is_displayed(LoginPage.ERROR_MESSAGE), "Error message should be displayed for invalid email format."

