"""
utilities/inspect_locators.py

Standalone helper script to inspect real page elements and print locator hints.

Run:
  python utilities/inspect_locators.py

What it does:
- Opens Chrome (non-headless)
- Inspects Register and Login pages
- Tries to log in using credentials from config/config.ini
- Inspects Notes page after login
"""

# Print progress immediately (avoid buffered output confusion).
import sys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Ensure the project root is on sys.path so imports work when running as a script.
import os

# Add project root (one folder above utilities/) to Python import path.
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utilities.config_reader import read_config


print("[INFO] Starting Chrome (headful)...", flush=True)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
print("[INFO] Chrome started.", flush=True)


def get_full_xpath(element):
    """Return the absolute XPath of a Selenium element using JavaScript."""
    return driver.execute_script(
        """
        function absoluteXPath(el) {
          if (el === document.body) return '/html/body';
          if (!el || !el.parentNode) return '';
          let ix = 0;
          const siblings = el.parentNode.childNodes;
          for (let i = 0; i < siblings.length; i++) {
            const sib = siblings[i];
            if (sib === el) {
              const tagName = el.tagName.toLowerCase();
              return absoluteXPath(el.parentNode) + '/' + tagName + '[' + (ix + 1) + ']';
            }
            if (sib.nodeType === 1 && sib.tagName === el.tagName) ix++;
          }
          return '';
        }
        return absoluteXPath(arguments[0]);
        """,
        element,
    )


def safe_attr(el, name):
    """Get an attribute safely (returns empty string if missing)."""
    value = el.get_attribute(name)
    return value if value is not None else ""


def inspect_page(url, page_name):
    """Open the URL and print attributes for all inputs/buttons/textareas."""
    print(f"\n{'=' * 60}", flush=True)
    print(f"INSPECTING: {page_name} - {url}", flush=True)
    print("=" * 60, flush=True)

    driver.get(url)
    time.sleep(3)

    elements = driver.find_elements(By.XPATH, "//input | //button | //textarea")

    for idx, el in enumerate(elements, start=1):
        class_attr = safe_attr(el, "class")
        print(f"\nElement #{idx}", flush=True)
        print(f"  Tag: {el.tag_name}", flush=True)
        print(f"  ID: {safe_attr(el, 'id')}", flush=True)
        print(f"  Name: {safe_attr(el, 'name')}", flush=True)
        print(f"  Type: {safe_attr(el, 'type')}", flush=True)
        print(f"  Placeholder: {safe_attr(el, 'placeholder')}", flush=True)
        print(f"  data-testid: {safe_attr(el, 'data-testid')}", flush=True)
        print(f"  class: {class_attr[:80]}", flush=True)
        print(f"  Full XPath: {get_full_xpath(el)}", flush=True)
        print("  ---", flush=True)


def try_login_for_notes():
    """Try to log in via UI so we can inspect the Notes page."""
    username = read_config("api", "username").strip()
    password = read_config("api", "password").strip()

    if not username or not password:
        print("\n[WARN] config.ini [api] username/password are empty. Cannot auto-login for Notes.", flush=True)
        print("[INFO] Please log in manually in the opened browser, then wait 20 seconds...", flush=True)
        time.sleep(20)
        return

    # Go to login page first.
    driver.get("https://practice.expandtesting.com/login")
    time.sleep(3)

    # Try common input IDs (site may use 'username'/'password' or 'email'/'password').
    user_el = None
    for locator in [(By.ID, "username"), (By.ID, "email"), (By.NAME, "email"), (By.NAME, "username")]:
        found = driver.find_elements(*locator)
        if found:
            user_el = found[0]
            break

    pass_el = None
    for locator in [(By.ID, "password"), (By.NAME, "password")]:
        found = driver.find_elements(*locator)
        if found:
            pass_el = found[0]
            break

    btn_el = None
    for locator in [(By.CSS_SELECTOR, "button[type='submit']"), (By.XPATH, "//button[contains(.,'Login') or contains(.,'Sign in')]")]:
        found = driver.find_elements(*locator)
        if found:
            btn_el = found[0]
            break

    if not user_el or not pass_el or not btn_el:
        print("\n[WARN] Auto-login elements not found. Please log in manually, then wait 20 seconds...", flush=True)
        time.sleep(20)
        return

    user_el.clear()
    user_el.send_keys(username)
    pass_el.clear()
    pass_el.send_keys(password)
    btn_el.click()
    time.sleep(3)


if __name__ == "__main__":
    try:
        inspect_page("https://practice.expandtesting.com/register", "Register Page")
        inspect_page("https://practice.expandtesting.com/login", "Login Page")

        # Log in first to access notes page (using credentials from config.ini).
        driver.get("https://practice.expandtesting.com/login")
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys(read_config("api", "username"))
        driver.find_element(By.ID, "password").send_keys(read_config("api", "password"))

        # Wait until the login button is clickable, then click it safely.
        login_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "submit-login")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", login_btn)
        try:
            login_btn.click()
        except Exception:
            # If something overlays the button, JS click is a simple fallback for inspection scripts.
            driver.execute_script("arguments[0].click();", login_btn)
        time.sleep(3)

        inspect_page("https://practice.expandtesting.com/notes", "Notes Page")
    finally:
        driver.quit()

