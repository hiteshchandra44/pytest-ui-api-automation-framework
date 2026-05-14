"""
utilities/debug_notes.py

Standalone script to debug why NotesPage.is_note_visible_by_title() fails.

Run:
  python utilities/debug_notes.py

Outputs:
  - Console (print)
  - logs/debug_notes.log (same transcript)
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Ensure project root is importable when run as a script.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pages.login_page import LoginPage  # noqa: E402
from pages.notes_page import NotesPage  # noqa: E402
from utilities.config_reader import read_config  # noqa: E402


LOG_PATH = os.path.join(PROJECT_ROOT, "logs", "debug_notes.log")


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


def banner(title: str) -> None:
    line = "=" * 80
    print(line)
    print(title)
    print(line)


def setup_debug_logging() -> None:
    """
    Force DEBUG logging for root and all created loggers (including those created by utilities/logger.py).

    Note: get_logger() sets propagate=False and INFO, and returns early if handlers exist.
    Here we upgrade existing loggers to DEBUG and upgrade handler levels too.
    """
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Add handlers if root has none (avoid duplicates when re-running in same interpreter).
    if not root.handlers:
        fmt = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        sh = logging.StreamHandler(sys.__stdout__)
        sh.setLevel(logging.DEBUG)
        sh.setFormatter(fmt)
        fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        root.addHandler(sh)
        root.addHandler(fh)

    # Upgrade all known loggers created so far.
    for name, obj in logging.Logger.manager.loggerDict.items():
        if not isinstance(obj, logging.Logger):
            continue
        obj.setLevel(logging.DEBUG)
        for h in obj.handlers:
            h.setLevel(logging.DEBUG)


def build_driver() -> webdriver.Chrome:
    opts = ChromeOptions()
    opts.add_argument("--window-size=1400,900")
    # headful by default (do not add --headless)
    drv = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=opts,
    )
    implicit = int(read_config("timeouts", "implicit_wait").strip() or "10")
    page_load = int(read_config("timeouts", "page_load").strip() or "30")
    drv.implicitly_wait(implicit)
    drv.set_page_load_timeout(page_load)
    return drv


def main() -> None:
    setup_debug_logging()

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(f"debug_notes started {datetime.now().isoformat()}\n")

    # Mirror prints to file too (in addition to logging).
    old_stdout = sys.stdout
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        sys.stdout = DualWriter(f)
        try:
            banner("DEBUG NOTES — START")
            print(f"Project root: {PROJECT_ROOT}")
            print(f"Log file: {LOG_PATH}")

            username = read_config("api", "username").strip()
            password = read_config("api", "password").strip()
            print(f"Using config.ini username={username!r} password={'***' if password else '(empty)'}")

            driver = build_driver()
            try:
                banner("STEP 1 — LOGIN")
                login_page = LoginPage(driver)
                login_page.open()
                login_page.enter_email(username)
                login_page.enter_password(password)
                login_page.click_login()

                # Ensure we land on notes base page.
                notes_page = NotesPage(driver)
                notes_page.open()

                banner("STEP 2 — CREATE NOTE")
                notes_page.click_add_note()
                notes_page.enter_note_title("DebugTest_12345")
                notes_page.enter_note_description("debug description")
                notes_page.save_note()

                banner("STEP 3 — POST-SAVE DOM DUMP")
                print(f"[3a] driver.current_url = {driver.current_url!r}")

                cards = driver.find_elements(By.CSS_SELECTOR, "div.card")
                print(f"[3b] div.card count = {len(cards)}")
                for i, c in enumerate(cards, start=1):
                    try:
                        print(f"  card[{i}] displayed={c.is_displayed()}")
                    except Exception as e:
                        print(f"  card[{i}] displayed=<error {e}>")

                headers = driver.find_elements(By.CSS_SELECTOR, "div.card-header")
                print(f"[3c] div.card-header count = {len(headers)}")
                for i, h in enumerate(headers, start=1):
                    try:
                        disp = h.is_displayed()
                    except Exception as e:
                        disp = f"<error {e}>"
                    try:
                        txt = (h.text or "").replace("\n", "\\n")
                    except Exception as e:
                        txt = f"<error {e}>"
                    try:
                        tc = (h.get_attribute("textContent") or "").replace("\n", "\\n")
                    except Exception as e:
                        tc = f"<error {e}>"
                    try:
                        ih = (h.get_attribute("innerHTML") or "").replace("\n", "\\n")
                    except Exception as e:
                        ih = f"<error {e}>"
                    print(f"  header[{i}] displayed={disp}")
                    print(f"    .text={txt!r}")
                    print(f"    textContent={tc!r}")
                    print(f"    innerHTML={ih!r}")

                banner("STEP 4 — JS INSPECTION")
                js_headers = driver.execute_script(
                    """
                    var headers = document.querySelectorAll('div.card-header');
                    var results = [];
                    headers.forEach(function(h) {
                      results.push({
                        class: h.className,
                        textContent: h.textContent,
                        innerHTML: h.innerHTML,
                        offsetParent: h.offsetParent !== null,
                        display: window.getComputedStyle(h).display,
                        visibility: window.getComputedStyle(h).visibility
                      });
                    });
                    return results;
                    """
                )
                print("[4d] JS header inspection result:")
                print(json.dumps(js_headers, indent=2, ensure_ascii=False))

                js_cards = driver.execute_script(
                    """
                    var cards = document.querySelectorAll('div.card');
                    return cards.length + ' cards found';
                    """
                )
                print(f"[4e] JS cards count result: {js_cards!r}")

                banner("STEP 5 — CALL PAGE OBJECT VISIBILITY METHODS")
                v1 = notes_page.is_note_visible_by_title("DebugTest_12345")
                print(f"[5] is_note_visible_by_title('DebugTest_12345') => {v1}")

                v2 = notes_page.is_note_visible_by_title("DebugTest")
                print(f"[6] is_note_visible_by_title('DebugTest') => {v2}")

                banner("STEP 6 — HOLD BROWSER OPEN 5s")
                time.sleep(5)
            finally:
                try:
                    driver.quit()
                except Exception:
                    pass

            banner("DEBUG NOTES — DONE")
        finally:
            sys.stdout = old_stdout

    print(f"[debug_notes] Transcript written to: {LOG_PATH}")


if __name__ == "__main__":
    main()

