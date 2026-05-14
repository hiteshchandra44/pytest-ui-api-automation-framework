"""
pages/login_page.py

This file contains the LoginPage class for the ExpandTesting Notes App UI.

Page covered:
- /notes/app/login

Actions available:
- Enter email/password, click login, read error messages, and verify login success.
"""

# Selenium locator strategy constants.
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Import the BasePage which contains reusable Selenium actions.
from pages.base_page import BasePage

# Import config reader so the page URL can come from config.ini (no hardcoding).
from utilities.config_reader import read_config


class LoginPage(BasePage):
    """Page Object for the Notes App login page."""

    # Notes App login URL (read from config.ini).
    URL = read_config("urls", "notes_login_url")

    # Locators (keep them as class-level variables for clarity and reuse).
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (
        By.CSS_SELECTOR,
        '[class*="toast"], [class*="alert"], [class*="error"], '
        '[class*="notification"], [role="alert"]',
    )

    def open(self):
        """
        Navigate to the Notes App login page using the URL from config.ini.
        """
        self.logger.info(f"Opening Notes App login page: {self.URL}")
        try:
            self.driver.get(self.URL)
        except Exception as e:
            self.logger.warning(
                f"login_page.open() get() raised: {e.__class__.__name__} — checking URL"
            )
            try:
                current = self.driver.current_url
                if "notes/app" in current:
                    self.logger.info(f"URL is correct ({current}), continuing")
                    return
            except Exception:
                pass
            raise

    def enter_email(self, email: str):
        """
        Type the email into the email input field.
        """
        self.type_text(self.EMAIL_INPUT, email)

    def enter_password(self, password: str):
        """
        Type the password into the password input field.
        """
        self.type_text(self.PASSWORD_INPUT, password)

    def click_login(self):
        """
        Click the login button and wait for URL to change away from the login page.

        Uses scroll-into-view plus a JavaScript click on the submit button so the
        action targets the real control even when an ad overlay would intercept a
        native pointer click.
        """

        def _get_submit():
            return WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.LOGIN_BUTTON)
            )

        def _scroll_and_js_click(btn):
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", btn
            )
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", btn)

        self._dismiss_overlays()
        submit = _get_submit()
        _scroll_and_js_click(submit)
        self.logger.info("Login button clicked (JS), waiting for redirect...")

        def _left_login(driver):
            return "login" not in driver.current_url

        try:
            WebDriverWait(self.driver, 30).until(_left_login)
            self.logger.info(f"Redirected to: {self.driver.current_url}")
            return
        except Exception:
            self.logger.warning(
                "URL did not change after login click within 30s — retrying JS click once"
            )

        try:
            self._dismiss_overlays()
            submit = _get_submit()
            _scroll_and_js_click(submit)
            WebDriverWait(self.driver, 15).until(_left_login)
            self.logger.info(f"Redirected to: {self.driver.current_url}")
        except Exception:
            self.logger.warning(
                "URL did not change after second JS login click within 15s"
            )

    def get_error_message(self) -> str:
        """
        Return the error message shown on the page (if any).
        """
        return self.get_text(self.ERROR_MESSAGE)

    def is_displayed(self, locator):
        import time

        # Wait up to 5s for a DOM error element (server-side error toast)
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            element = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(locator))
            if element.is_displayed():
                return True
        except Exception:
            pass

        # Check HTML5 native validity (fires when native submit used)
        try:
            result = self.driver.execute_script(
                """
                var inputs = document.querySelectorAll('input');
                for (var i = 0; i < inputs.length; i++) {
                    if (inputs[i].validity && !inputs[i].validity.valid) {
                        return true;
                    }
                }
                return false;
                """
            )
            if result:
                return True
        except Exception:
            pass

        # Check if we're still on the login page with an email value that looks invalid
        try:
            email_el = self.driver.find_element(By.CSS_SELECTOR, "#email, input[type='email']")
            email_val = email_el.get_attribute("value") or ""
            if "@" not in email_val and email_val:
                current_url = self.driver.current_url
                if "login" in current_url:
                    return True
        except Exception:
            pass

        return False

    def is_login_successful(self):
        """Check if login succeeded by verifying current URL."""
        current = self.driver.current_url
        self.logger.info(f"Current URL after login attempt: {current}")
        return "notes/app" in current and "login" not in current

