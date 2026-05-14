"""
pages/register_page.py

This file contains the RegisterPage class for the ExpandTesting Notes App UI.

Page covered:
- /notes/app/register

Actions available:
- Enter name/email/password fields, click register, and read success/error messages.
"""

# Standard library imports.
import time

# Selenium locator strategy constants.
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Import the BasePage which contains reusable Selenium actions.
from pages.base_page import BasePage

# Import config reader so the page URL can come from config.ini (no hardcoding).
from utilities.config_reader import read_config


class RegisterPage(BasePage):
    """Page Object for the Notes App register page."""

    # Notes App register URL (read from config.ini).
    URL = read_config("urls", "notes_register_url")

    # Locators (class-level for reuse and clarity).
    EMAIL_INPUT = (By.ID, "email")
    NAME_INPUT = (By.ID, "name")
    PASSWORD_INPUT = (By.ID, "password")
    CONFIRM_PASSWORD_INPUT = (By.ID, "confirmPassword")
    REGISTER_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")

    # Toast / inline / HTML5 validation hints (tests use *_ALERT; getters use *_MESSAGE — same locators).
    ERROR_ALERT = (
        By.CSS_SELECTOR,
        "div.alert, div[class*='toast'], .invalid-feedback, [class*='error'], input:invalid",
    )
    SUCCESS_ALERT = (
        By.CSS_SELECTOR,
        "div.alert-success, div[class*='toast-success'], [class*='success']",
    )
    ERROR_MESSAGE = ERROR_ALERT
    SUCCESS_MESSAGE = SUCCESS_ALERT

    def open(self):
        """
        Navigate to the Notes App register page using the URL from config.ini.
        Dismisses ad overlays after load, then waits for the submit button in the DOM.
        """
        self.logger.info(f"Opening Notes App register page: {self.URL}")
        try:
            self.driver.get(self.URL)
        except Exception as e:
            self.logger.warning(
                f"register_page.open() get() raised: {e.__class__.__name__} — checking URL"
            )
            try:
                current = self.driver.current_url
            except Exception:
                raise e
            if "notes/app" not in current:
                raise e
            self.logger.info(f"URL is correct ({current}), continuing")

        self._dismiss_overlays()
        for _attempt in range(3):
            self._dismiss_overlays()
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located(self.REGISTER_BUTTON)
                )
                break
            except Exception:
                if _attempt == 2:
                    raise
                time.sleep(1)

    def enter_email(self, email: str):
        """
        Type the email into the email input field.
        """
        self.type_text(self.EMAIL_INPUT, email)

    def enter_name(self, name: str):
        """
        Type the name into the name input field.
        """
        self.type_text(self.NAME_INPUT, name)

    def enter_password(self, password: str):
        """
        Type the password into the password input field.
        """
        self.type_text(self.PASSWORD_INPUT, password)

    def enter_confirm_password(self, confirm_password: str):
        """
        Type the confirm password into the confirm password input field.
        """
        self.type_text(self.CONFIRM_PASSWORD_INPUT, confirm_password)

    def click_register(self):
        """
        Click the register button.
        """
        # Use JS click to avoid click interception issues on this site.
        el = self.find_element(self.REGISTER_BUTTON)
        self.driver.execute_script("arguments[0].click()", el)

    def is_displayed(self, locator: tuple, wait_seconds: int = 8) -> bool:
        """
        Wait for DOM presence only (not visibility): ad overlays can cover controls
        while they still exist in the DOM.

        Returns True once the locator is present within the timeout.
        """
        try:
            self.logger.info(f"RegisterPage: checking presence (up to {wait_seconds}s): {locator}")
            WebDriverWait(self.driver, wait_seconds).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False
        except Exception as e:
            self.logger.info(f"RegisterPage.is_displayed: {locator} -> False ({e})")
            return False

    def get_success_message(self) -> str:
        """
        Return the success message shown on the page (if any).
        """
        return self.get_text(self.SUCCESS_MESSAGE)

    def get_error_message(self) -> str:
        """
        Return the error message shown on the page (if any).
        """
        return self.get_text(self.ERROR_MESSAGE)

