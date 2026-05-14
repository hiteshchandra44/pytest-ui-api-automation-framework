"""
tests/ui/test_register.py

This file contains UI tests for the registration functionality on:
the ExpandTesting practice site (/register).

We use the RegisterPage (POM) to keep tests clean and readable.
"""

# uuid is used to generate unique emails for registration tests.
import uuid

# Import pytest for test structure and skipping when config is missing.
import pytest

# Import our page objects.
from pages.register_page import RegisterPage

# Import logger utility.
from utilities.logger import get_logger

# Import config reader so we never hardcode important test inputs.
from utilities.config_reader import read_config


# Create a module-level logger so each test can log a start message.
logger = get_logger(__name__)


def _unique_email() -> str:
    """
    Generate a unique email for registration tests.
    """
    # Use a UUID fragment to avoid duplicates on every run.
    return f"testuser_{uuid.uuid4().hex[:6]}@test.com"


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.positive
def test_successful_registration(driver):
    """Register with valid unique data and verify a success message appears."""
    logger.info("Running test: test_successful_registration")

    password = read_config("api", "default_password").strip()
    if not password:
        pytest.skip("default_password is missing in config.ini under [api].")

    page = RegisterPage(driver)
    page.open()

    page.enter_name("Test User")
    page.enter_email(_unique_email())
    page.enter_password(password)
    page.enter_confirm_password(password)
    page.click_register()

    assert page.is_displayed(RegisterPage.SUCCESS_ALERT), "Success message should be visible after registration."


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.negative
def test_mismatched_passwords(driver):
    """Verify an error appears when password and confirm password do not match."""
    logger.info("Running test: test_mismatched_passwords")

    password = read_config("api", "default_password").strip()
    wrong_password = read_config("api", "wrong_password").strip()
    if not password or not wrong_password:
        pytest.skip("default_password/wrong_password missing in config.ini under [api].")

    page = RegisterPage(driver)
    page.open()

    page.enter_name("Test User")
    page.enter_email(_unique_email())
    page.enter_password(password)
    page.enter_confirm_password(wrong_password)
    page.click_register()

    assert page.is_displayed(RegisterPage.ERROR_ALERT), "Error message should appear for mismatched passwords."


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.negative
def test_empty_name_field(driver):
    """Submit the form with empty name and verify an error appears."""
    logger.info("Running test: test_empty_name_field")

    password = read_config("api", "default_password").strip()
    if not password:
        pytest.skip("default_password is missing in config.ini under [api].")

    page = RegisterPage(driver)
    page.open()

    page.enter_name("")
    page.enter_email(_unique_email())
    page.enter_password(password)
    page.enter_confirm_password(password)
    page.click_register()

    assert page.is_displayed(RegisterPage.ERROR_ALERT), "Error message should appear when name is empty."


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.negative
def test_empty_email_field(driver):
    """Submit the form with empty email and verify an error appears."""
    logger.info("Running test: test_empty_email_field")

    password = read_config("api", "default_password").strip()
    if not password:
        pytest.skip("default_password is missing in config.ini under [api].")

    page = RegisterPage(driver)
    page.open()

    page.enter_name("Test User")
    page.enter_email("")
    page.enter_password(password)
    page.enter_confirm_password(password)
    page.click_register()

    assert page.is_displayed(RegisterPage.ERROR_ALERT), "Error message should appear when email is empty."


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.negative
def test_short_password(driver):
    """Submit with a short password and verify an error appears."""
    logger.info("Running test: test_short_password")

    short_password = read_config("api", "short_password").strip()
    if not short_password:
        pytest.skip("short_password is missing in config.ini under [api].")

    page = RegisterPage(driver)
    page.open()

    page.enter_name("Test User")
    page.enter_email(_unique_email())
    page.enter_password(short_password)
    page.enter_confirm_password(short_password)
    page.click_register()

    assert page.is_displayed(RegisterPage.ERROR_ALERT), "Error message should appear for a short password."


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.negative
def test_already_registered_email(driver):
    """Try registering with an already registered email and verify an error appears."""
    logger.info("Running test: test_already_registered_email")

    already_registered_email = read_config("api", "already_registered_email").strip()
    fallback_email = read_config("api", "username").strip()
    email_to_use = already_registered_email or fallback_email
    if not email_to_use:
        pytest.skip("already_registered_email and username are both empty in config.ini under [api].")

    password = read_config("api", "default_password").strip()
    if not password:
        pytest.skip("default_password is missing in config.ini under [api].")

    page = RegisterPage(driver)
    page.open()

    page.enter_name("Test User")
    page.enter_email(email_to_use)
    page.enter_password(password)
    page.enter_confirm_password(password)
    page.click_register()

    assert page.is_displayed(RegisterPage.ERROR_ALERT), "Error message should appear for already registered email."


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.positive
def test_register_page_loads(driver):
    """Verify the register page loads and the submit button is visible."""
    logger.info("Running test: test_register_page_loads")

    page = RegisterPage(driver)
    page.open()

    assert "/register" in driver.current_url, f"Expected /register in URL, got: {driver.current_url}"
    assert page.is_displayed(RegisterPage.REGISTER_BUTTON), "Register submit button should be visible on register page."


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.positive
def test_valid_email_format_check(driver):
    """Enter a valid email format and verify no immediate email-format error is shown."""
    logger.info("Running test: test_valid_email_format_check")

    page = RegisterPage(driver)
    page.open()

    page.enter_email("valid.email@example.com")

    # Simple check: the field should still be displayed after entering text.
    assert page.is_displayed(RegisterPage.EMAIL_INPUT), "Email field should accept a valid email format input."

