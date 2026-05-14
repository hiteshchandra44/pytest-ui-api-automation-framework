"""
pages/base_page.py

This file contains the BasePage class for Selenium Page Object Model (POM).

Page covered:
- Not a single page. This is a reusable "base" class that other page classes inherit from.

Actions available:
- Find elements, click, type text, read text, visibility checks, and explicit waits.
"""

# Standard library imports.
import time

# Selenium imports for locating elements and waiting for conditions.
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import our simple utilities for logging and reading config values.
from utilities.logger import get_logger
from utilities.config_reader import read_config


class BasePage:
    """Base class that provides common Selenium actions for all pages."""

    def __init__(self, driver):
        """
        Store the WebDriver instance so page methods can use it.

        Args:
            driver: Selenium WebDriver instance (Chrome/Firefox/Edge, etc.)
        """
        # Save the driver so other methods can interact with the browser.
        self.driver = driver

        # Create a logger for this class/file.
        self.logger = get_logger(self.__class__.__name__)

        # Read explicit wait timeout from config.ini (stored as string).
        timeout_str = read_config("timeouts", "explicit_wait")

        # Convert it to an integer so WebDriverWait can use it.
        self.explicit_wait_seconds = int(timeout_str)

    def _dismiss_overlays(self) -> None:
        """
        Best-effort: hide or remove fixed ad/cookie layers that intercept clicks
        on ad-supported practice sites (used before critical UI actions).
        """
        try:
            self.driver.execute_script(
                """
                document.querySelectorAll(
                    'div[style*="position: fixed"], div[style*="position:fixed"],' +
                    'iframe[id*="google_ads"], div[id*="advert"], iframe[name^="google"]'
                ).forEach(function(el) {
                    try {
                        var rect = el.getBoundingClientRect();
                        var z = parseInt(window.getComputedStyle(el).zIndex, 10) || 0;
                        if (z > 50 || rect.width > window.innerWidth * 0.5) {
                            el.style.display = 'none';
                        }
                    } catch (e) {}
                });
                """
            )
        except Exception:
            pass
        try:
            self.driver.execute_script(
                """
                document.querySelectorAll(
                    'div[style*="position: fixed"], div[style*="position:fixed"]'
                ).forEach(function(el) {
                    try {
                        var z = parseInt(window.getComputedStyle(el).zIndex, 10) || 0;
                        var h = el.getBoundingClientRect().height;
                        if (z > 100 && h > 100) {
                            el.remove();
                        }
                    } catch (e) {}
                });

                document.querySelectorAll('iframe').forEach(function(el) {
                    try {
                        var style = window.getComputedStyle(el);
                        var rect = el.getBoundingClientRect();
                        var isFullViewport = (
                            rect.width >= window.innerWidth * 0.8 ||
                            rect.height >= window.innerHeight * 0.8
                        );
                        if (isFullViewport) {
                            el.style.display = 'none';
                        }
                    } catch(e) {}
                });
                """
            )
        except Exception:
            pass
        time.sleep(0.3)

    def find_element(self, locator: tuple):
        """
        Find and return a web element using a locator tuple.

        Args:
            locator: A tuple like (By.ID, "username") or (By.XPATH, "//div")

        Returns:
            A Selenium WebElement
        """
        # Wrap in try/except so failures are logged clearly.
        try:
            # Log what we are trying to find (helps debugging).
            self.logger.info(f"Finding element using locator: {locator}")

            # Use Selenium's built-in find_element with unpacked locator tuple.
            return self.driver.find_element(*locator)
        except Exception as e:
            # Log the error and raise again with a useful message.
            self.logger.error(f"Failed to find element. Locator: {locator}. Error: {e}")
            raise Exception(f"Failed to find element with locator: {locator}") from e

    def click(self, locator: tuple):
        """
        Click an element identified by the locator.

        Args:
            locator: A tuple like (By.ID, "submit")
        """
        # Wrap in try/except so failures are logged clearly.
        try:
            # Log before clicking.
            self.logger.info(f"Clicking element using locator: {locator}")

            # Wait for element to be clickable for stability.
            self.wait_for_element(locator)

            # Find the element and click it.
            self.find_element(locator).click()
        except Exception as e:
            # Log the error and raise again with a useful message.
            self.logger.error(f"Failed to click element. Locator: {locator}. Error: {e}")
            raise Exception(f"Failed to click element with locator: {locator}") from e

    def type_text(self, locator: tuple, text: str, clear_first: bool = True):
        """
        Type text into an input field.

        Args:
            locator: A tuple like (By.ID, "password")
            text: The string to type into the field
            clear_first: If True, clear existing text before typing
        """
        # Wrap in try/except so failures are logged clearly.
        try:
            # Log what we are typing (avoid logging secrets in real projects).
            self.logger.info(f"Typing text into element using locator: {locator}")

            # Wait until the element is visible before typing.
            self.wait_for_element(locator)

            # Find the input element.
            element = self.find_element(locator)

            # Optionally clear existing text to avoid appending.
            if clear_first:
                element.clear()

            # Type the provided text.
            element.send_keys(text)
        except Exception as e:
            # Log the error and raise again with a useful message.
            self.logger.error(f"Failed to type into element. Locator: {locator}. Error: {e}")
            raise Exception(f"Failed to type into element with locator: {locator}") from e

    def react_type(self, element, text):
        """Type text into a field using native Selenium only."""
        from selenium.webdriver.common.keys import Keys

        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element
        )
        element.click()
        time.sleep(0.2)

        # Select all and delete existing content
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.DELETE)
        time.sleep(0.1)

        # Type the text
        element.send_keys(text)
        time.sleep(0.1)

    def get_text(self, locator: tuple) -> str:
        """
        Get the visible text of an element.

        Args:
            locator: A tuple like (By.CSS_SELECTOR, ".message")

        Returns:
            The element's text as a string
        """
        # Wrap in try/except so failures are logged clearly.
        try:
            # Log text retrieval.
            self.logger.info(f"Getting text from element using locator: {locator}")

            # Wait until the element is visible.
            self.wait_for_element(locator)

            # Return the element's text.
            return self.find_element(locator).text
        except Exception as e:
            # Log the error and raise again with a useful message.
            self.logger.error(f"Failed to get text. Locator: {locator}. Error: {e}")
            raise Exception(f"Failed to get text from element with locator: {locator}") from e

    def is_displayed(self, locator: tuple) -> bool:
        """
        Check if an element is displayed on the page.

        Args:
            locator: A tuple like (By.ID, "flash")

        Returns:
            True if displayed, otherwise False
        """
        # Wrap in try/except so errors are logged but we still return a boolean.
        try:
            # Log visibility check.
            self.logger.info(f"Checking if element is displayed using locator: {locator}")

            # If element exists and is displayed, return True.
            return self.find_element(locator).is_displayed()
        except Exception as e:
            # If element is not found or not visible, log and return False.
            self.logger.info(f"Element not displayed / not found. Locator: {locator}. Error: {e}")
            return False

    def wait_for_element(self, locator: tuple):
        """
        Wait until an element is visible on the page.

        This uses WebDriverWait + Selenium ExpectedConditions.

        Args:
            locator: A tuple like (By.ID, "username")

        Returns:
            The WebElement after it becomes visible
        """
        # Wrap in try/except so failures are logged clearly.
        try:
            # Log the wait action.
            self.logger.info(
                f"Waiting for element to be visible. Locator: {locator}. Timeout: {self.explicit_wait_seconds}s"
            )

            # Create a WebDriverWait object with the timeout from config.
            wait = WebDriverWait(self.driver, self.explicit_wait_seconds)

            # Wait until the element is visible and return it.
            return wait.until(EC.visibility_of_element_located(locator))
        except Exception as e:
            # Log the error and raise again with a useful message.
            self.logger.error(f"Wait failed for element. Locator: {locator}. Error: {e}")
            raise Exception(f"Wait failed for element with locator: {locator}") from e

