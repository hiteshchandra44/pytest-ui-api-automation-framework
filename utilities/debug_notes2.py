"""
utilities/debug_notes2.py

Minimal raw-Selenium script (no page objects) to login, create a note,
and inspect the DOM immediately after save.

Run:
  python utilities/debug_notes2.py

Output:
  - Console
  - logs/debug_notes2.log (same transcript)
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# Ensure project root is importable when run as a script.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utilities.config_reader import read_config  # noqa: E402


LOG_PATH = os.path.join(PROJECT_ROOT, "logs", "debug_notes2.log")


class DualWriter:
    """Write output to both console and a file."""

    def __init__(self, file_obj):
        self._file = file_obj
        self._stdout = sys.__stdout__

    def write(self, data: str) -> int:
        self._stdout.write(data)
        self._stdout.flush()
        self._file.write(data)
        self._file.flush()
        return len(data)

    def flush(self) -> None:
        self._stdout.flush()
        self._file.flush()


def main():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    # Mirror prints to file too.
    old_stdout = sys.stdout
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(f"debug_notes2 started {datetime.now().isoformat()}\n")

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        sys.stdout = DualWriter(f)
        try:
            # Setup
            options = webdriver.ChromeOptions()
            options.page_load_strategy = "eager"
            options.add_argument("--window-size=1400,900")

            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options,
            )
            driver.implicitly_wait(0)  # DISABLE implicit wait for this script

            try:
                base_url = read_config("urls", "notes_login_url").strip()
                username = read_config("api", "username").strip()
                password = read_config("api", "password").strip()

                # Step 1: Login
                print("\n=== STEP 1: LOGIN ===")
                driver.get(base_url)
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "email")))
                driver.find_element(By.ID, "email").send_keys(username)
                driver.find_element(By.ID, "password").send_keys(password)
                driver.execute_script(
                    "arguments[0].click();",
                    driver.find_element(By.CSS_SELECTOR, "button[type='submit']"),
                )
                # Wait for redirect to notes app
                WebDriverWait(driver, 30).until(
                    lambda d: "notes/app" in d.current_url and "login" not in d.current_url
                )
                print(f"Login OK. URL: {driver.current_url}")

                # Step 2: Click Add Note
                print("\n=== STEP 2: OPEN ADD NOTE MODAL ===")
                # Wait for any existing notes to load first
                time.sleep(2)

                # Find and click the add note button
                add_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'add note') or contains(normalize-space(.),'+ Add')]",
                        )
                    )
                )
                print(
                    f"Add button found: '{add_btn.text}' class='{add_btn.get_attribute('class')}'"
                )
                driver.execute_script("arguments[0].click();", add_btn)

                # Wait for modal
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.modal.show"))
                )
                print("Modal opened.")

                # Step 3: Fill and submit
                print("\n=== STEP 3: FILL AND SUBMIT NOTE ===")
                test_title = "DebugNote_FIXED"

                title_input = driver.find_element(By.ID, "title")
                title_input.clear()
                title_input.send_keys(test_title)

                desc_input = driver.find_element(By.ID, "description")
                desc_input.clear()
                desc_input.send_keys("debug description")

                print(f"Filled: title='{test_title}'")

                # Click Create/Submit
                submit_btn = driver.find_element(By.CSS_SELECTOR, '[data-testid="note-submit"]')
                print(f"Submit button: '{submit_btn.text}'")
                driver.execute_script("arguments[0].click();", submit_btn)

                # Step 4: Wait for modal to close
                print("\n=== STEP 4: WAIT FOR MODAL CLOSE ===")
                try:
                    WebDriverWait(driver, 15).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.modal.show"))
                    )
                    print("Modal closed.")
                except Exception as e:
                    print(f"Modal close wait failed: {e}")

                # Step 5: Inspect DOM immediately
                print("\n=== STEP 5: DOM INSPECTION AFTER SAVE ===")
                print(f"Current URL: {driver.current_url}")

                # Raw find_elements with NO implicit wait
                cards = driver.find_elements(By.CSS_SELECTOR, "div.card")
                print(f"div.card count: {len(cards)}")
                for i, card in enumerate(cards):
                    print(f"  card[{i}] displayed={card.is_displayed()}")

                headers = driver.find_elements(By.CSS_SELECTOR, "div.card-header")
                print(f"div.card-header count: {len(headers)}")
                for i, h in enumerate(headers):
                    tc = h.get_attribute("textContent")
                    txt = h.text
                    disp = h.is_displayed()
                    cls = h.get_attribute("class")
                    print(f"  header[{i}]: displayed={disp}")
                    print(f"    class='{cls}'")
                    print(f"    .text='{txt}'")
                    print(f"    textContent='{tc}'")
                    print(f"    textContent.strip()='{tc.strip() if tc else None}'")
                    print(
                        f"    MATCHES '{test_title}': {tc.strip() == test_title if tc else False}"
                    )

                # Step 6: JS inspection
                print("\n=== STEP 6: JS INSPECTION ===")
                js_result = driver.execute_script(
                    """
                    var headers = document.querySelectorAll('div.card-header');
                    var results = [];
                    headers.forEach(function(h, i) {
                        var style = window.getComputedStyle(h);
                        results.push({
                            index: i,
                            className: h.className,
                            textContent: h.textContent,
                            textContentStripped: h.textContent.trim(),
                            innerText: h.innerText,
                            display: style.display,
                            visibility: style.visibility,
                            offsetParent: h.offsetParent !== null
                        });
                    });
                    return results;
                    """
                )
                print(f"JS found {len(js_result)} card-header elements:")
                for item in js_result:
                    print(f"  [{item['index']}] class='{item['className']}'")
                    print(f"       display={item['display']} visibility={item['visibility']}")
                    print(f"       textContent='{item['textContent']}'")
                    print(f"       textContentStripped='{item['textContentStripped']}'")
                    print(f"       innerText='{item['innerText']}'")
                    print(f"       MATCHES: {item['textContentStripped'] == test_title}")

                # Step 7: XPath check
                print("\n=== STEP 7: XPATH CHECK ===")
                xpath_results = driver.find_elements(By.XPATH, "//div[contains(@class,'card-header')]")
                print(f"XPath //div[contains(@class,'card-header')] found: {len(xpath_results)}")
                for i, el in enumerate(xpath_results):
                    print(f"  [{i}] text='{el.text}' displayed={el.is_displayed()}")

                time.sleep(3)
            finally:
                driver.quit()
                print("\n=== DONE ===")
        finally:
            sys.stdout = old_stdout


if __name__ == "__main__":
    main()

