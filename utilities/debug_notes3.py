"""
debug_notes3.py — Drop this into utilities/ and run:
    python utilities/debug_notes3.py

Diagnoses exactly why the Add Note modal is not saving.
Uses raw Selenium only, no page objects.
"""
import time
import sys
import os

# Make project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from utilities.config_reader import read_config


def p(msg):
    print(msg, flush=True)


def main():
    options = webdriver.ChromeOptions()
    options.page_load_strategy = "eager"
    options.add_argument("--window-size=1400,900")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    driver.implicitly_wait(0)

    try:
        login_url = read_config("urls", "notes_login_url").strip()
        username = read_config("api", "username").strip()
        password = read_config("api", "password").strip()

        # ── LOGIN ────────────────────────────────────────────────────────────
        p("\n=== LOGIN ===")
        driver.get(login_url)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        driver.find_element(By.ID, "email").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(driver, 30).until(
            lambda d: "notes/app" in d.current_url and "login" not in d.current_url
        )
        p(f"Logged in. URL: {driver.current_url}")
        time.sleep(2)

        # ── OPEN MODAL ───────────────────────────────────────────────────────
        p("\n=== OPEN MODAL ===")
        add_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(normalize-space(.), 'Add Note')]")
            )
        )
        p(f"Add button text: '{add_btn.text}'")
        add_btn.click()   # native click
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.modal.show"))
        )
        p("Modal opened.")
        time.sleep(0.5)

        # ── INSPECT MODAL FIELDS ─────────────────────────────────────────────
        p("\n=== MODAL FIELD INSPECTION ===")
        modal = driver.find_element(By.CSS_SELECTOR, "div.modal.show")
        p(f"Modal HTML snippet (first 2000 chars):\n{modal.get_attribute('innerHTML')[:2000]}")

        # Find all inputs inside the modal
        inputs = modal.find_elements(By.TAG_NAME, "input")
        textareas = modal.find_elements(By.TAG_NAME, "textarea")
        p(f"\nInputs in modal: {len(inputs)}")
        for i, inp in enumerate(inputs):
            p(f"  input[{i}]: id='{inp.get_attribute('id')}' "
              f"name='{inp.get_attribute('name')}' "
              f"type='{inp.get_attribute('type')}' "
              f"placeholder='{inp.get_attribute('placeholder')}'")
        p(f"Textareas in modal: {len(textareas)}")
        for i, ta in enumerate(textareas):
            p(f"  textarea[{i}]: id='{ta.get_attribute('id')}' "
              f"name='{ta.get_attribute('name')}' "
              f"placeholder='{ta.get_attribute('placeholder')}'")

        # ── FILL FIELDS ──────────────────────────────────────────────────────
        p("\n=== FILL FIELDS ===")
        test_title = "DebugSave_TEST"

        # Try to find title field
        title_field = None
        for selector in ["#title", "[name='title']", "input[placeholder*='itle']",
                         "input[placeholder*='note']", "input"]:
            try:
                els = modal.find_elements(By.CSS_SELECTOR, selector)
                if els:
                    title_field = els[0]
                    p(f"Title field found via '{selector}'")
                    break
            except Exception:
                pass

        if not title_field:
            p("ERROR: Could not find title field!")
            return

        # Click to focus, then type
        title_field.click()
        time.sleep(0.2)
        title_field.clear()
        title_field.send_keys(test_title)
        time.sleep(0.2)
        actual_value = title_field.get_attribute("value")
        p(f"Title field value after typing: '{actual_value}'")

        # React state check via JS
        react_value = driver.execute_script(
            "return arguments[0]._valueTracker ? "
            "arguments[0]._valueTracker.getValue() : 'no_tracker';",
            title_field
        )
        p(f"React _valueTracker: '{react_value}'")

        # Find description field
        desc_field = None
        for selector in ["#description", "[name='description']",
                         "textarea[placeholder*='escription']", "textarea"]:
            try:
                els = modal.find_elements(By.CSS_SELECTOR, selector)
                if els:
                    desc_field = els[0]
                    p(f"Desc field found via '{selector}'")
                    break
            except Exception:
                pass

        if desc_field:
            desc_field.click()
            time.sleep(0.2)
            desc_field.clear()
            desc_field.send_keys("debug description text")
            time.sleep(0.2)
            p(f"Desc field value: '{desc_field.get_attribute('value')}'")

        # ── SUBMIT ───────────────────────────────────────────────────────────
        p("\n=== SUBMIT ===")
        # Find submit button
        submit = None
        for selector in ['[data-testid="note-submit"]', "button[type='submit']",
                         ".modal-footer button.btn-primary"]:
            try:
                els = modal.find_elements(By.CSS_SELECTOR, selector)
                if els:
                    submit = els[0]
                    p(f"Submit button found via '{selector}': text='{submit.text}'")
                    break
            except Exception:
                pass

        if not submit:
            p("ERROR: Submit button not found!")
            return

        p(f"Submit button enabled: {submit.is_enabled()}, displayed: {submit.is_displayed()}")

        # Try NATIVE click
        p("Attempting native .click()...")
        submit.click()
        time.sleep(1)

        # Check if modal closed
        modals_after = driver.find_elements(By.CSS_SELECTOR, "div.modal.show")
        p(f"div.modal.show elements after click: {len(modals_after)}")

        if len(modals_after) > 0:
            p("Modal still open after native click. Trying send_keys ENTER on title...")
            title_field.send_keys(Keys.RETURN)
            time.sleep(1)
            modals_after2 = driver.find_elements(By.CSS_SELECTOR, "div.modal.show")
            p(f"div.modal.show after ENTER: {len(modals_after2)}")

        if len(driver.find_elements(By.CSS_SELECTOR, "div.modal.show")) > 0:
            p("Modal STILL open. Trying submit button send_keys RETURN...")
            submit.send_keys(Keys.RETURN)
            time.sleep(1)
            modals_after3 = driver.find_elements(By.CSS_SELECTOR, "div.modal.show")
            p(f"div.modal.show after submit RETURN: {len(modals_after3)}")

        # ── WAIT AND CHECK RESULT ────────────────────────────────────────────
        p("\n=== RESULT CHECK ===")
        try:
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.modal.show"))
            )
            p("Modal closed successfully!")
        except Exception:
            p("Modal did NOT close within 10s.")

        time.sleep(1)
        headers = driver.find_elements(By.CSS_SELECTOR, "div.card-header")
        p(f"Card headers found: {len(headers)}")
        for i, h in enumerate(headers):
            p(f"  [{i}] textContent='{h.get_attribute('textContent').strip()}'")

        # ── CHECK FOR ANY ERROR IN MODAL ─────────────────────────────────────
        p("\n=== MODAL ERROR CHECK ===")
        error_els = driver.find_elements(
            By.CSS_SELECTOR,
            ".modal.show .invalid-feedback, .modal.show .text-danger, "
            ".modal.show .alert, .modal.show [class*='error']"
        )
        p(f"Error elements in modal: {len(error_els)}")
        for e in error_els:
            p(f"  error: '{e.text}' displayed={e.is_displayed()}")

        # Final modal HTML if still open
        remaining = driver.find_elements(By.CSS_SELECTOR, "div.modal.show")
        if remaining:
            p(f"\nModal still open. Full HTML:\n{remaining[0].get_attribute('innerHTML')[:3000]}")

        time.sleep(3)

    finally:
        driver.quit()
        p("\n=== DONE ===")


if __name__ == "__main__":
    main()