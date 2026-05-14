"""
utilities/inspect_dom.py

Standalone DOM diagnostic for practice.expandtesting.com Notes app.
Run: python utilities/inspect_dom.py

Uses Chrome (headful), webdriver-manager, and config/config.ini credentials.
Output goes to the console and to logs/dom_inspection.log
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Project root on sys.path when run as: python utilities/inspect_dom.py
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utilities.config_reader import read_config  # noqa: E402


LOG_REL = os.path.join("logs", "dom_inspection.log")
CLASS_HINTS_STEP1 = ("card", "note", "item", "list-item", "title")
FEEDBACK_CLASS_SUBSTRINGS = (
    "toast",
    "alert",
    "error",
    "danger",
    "message",
    "notification",
    "feedback",
)


def _log_path() -> str:
    return os.path.join(PROJECT_ROOT, LOG_REL)


class DualWriter:
    """Write the same bytes to console and a log file."""

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


def _banner(p, title: str, char: str = "=") -> None:
    line = char * 72
    p(line)
    p(title)
    p(line)


def _body_outer_html(driver) -> str:
    return driver.execute_script("return document.body ? document.body.outerHTML : '';") or ""


def _print_elements_class_hints(p, driver, hints: tuple, label: str) -> None:
    _banner(p, label, "-")
    parts = [f"contains(@class, '{h}')" for h in hints]
    xpath = "//*[" + " or ".join(parts) + "]"
    seen = set()
    try:
        els = driver.find_elements(By.XPATH, xpath)
    except Exception as ex:
        p(f"[ERROR] XPath scan failed: {ex}")
        return
    for el in els:
        try:
            if not el.is_displayed():
                continue
        except Exception:
            continue
        try:
            tag = el.tag_name
            cls = el.get_attribute("class") or ""
            text = (el.text or "").strip().replace("\n", " ")[:500]
            key = (tag, cls, text)
            if key in seen:
                continue
            seen.add(key)
            p(f"  <{tag}> class={cls!r} text={text!r}")
        except Exception as ex:
            p(f"  [skip element] {ex}")
    p(f"  (total unique rows printed: {len(seen)})")


def _print_feedback_elements(p, driver, label: str) -> None:
    _banner(p, label, "-")
    parts = [f"contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{s}')" for s in FEEDBACK_CLASS_SUBSTRINGS]
    xpath = "//*[" + " or ".join(parts) + "]"
    count = 0
    try:
        els = driver.find_elements(By.XPATH, xpath)
    except Exception as ex:
        p(f"[ERROR] feedback XPath failed: {ex}")
        return
    for el in els:
        try:
            tag = el.tag_name
            cls = el.get_attribute("class") or ""
            text = (el.text or "").strip().replace("\n", " ")[:800]
            disp = el.is_displayed()
            p(f"  <{tag}> displayed={disp} class={cls!r}")
            p(f"      text={text!r}")
            count += 1
        except Exception as ex:
            p(f"  [skip] {ex}")
    p(f"  (elements matched: {count})")


def _print_visible_modal_html(p, driver) -> None:
    _banner(p, "--- Visible modal / dialog HTML ---", "-")
    selectors = [
        (By.CSS_SELECTOR, "div[role='dialog']"),
        (By.CSS_SELECTOR, "[role='dialog']"),
        (By.CSS_SELECTOR, "div.modal.show"),
        (By.CSS_SELECTOR, "div.modal.fade.show"),
        (By.CSS_SELECTOR, "div[class*='modal']"),
        (By.CSS_SELECTOR, ".MuiDialog-root"),
        (By.CSS_SELECTOR, ".MuiModal-root"),
    ]
    found = False
    for by, sel in selectors:
        try:
            for el in driver.find_elements(by, sel):
                try:
                    if el.is_displayed():
                        html = driver.execute_script("return arguments[0].outerHTML;", el)
                        p(f"[from {sel}] length={len(html)} chars")
                        p(html[:200000] if len(html) > 200000 else html)
                        found = True
                except Exception:
                    continue
        except Exception as ex:
            p(f"[warn] selector {sel}: {ex}")
    if not found:
        p("(no visible modal/dialog matched known selectors)")


def _click_add_note(p, driver) -> bool:
    _banner(p, "--- Clicking Add Note (trying common selectors) ---", "-")
    candidates: list[tuple[str, tuple]] = [
        ("xpath Add Note text", (By.XPATH, "//button[contains(., 'Add Note')]")),
        ("xpath + Add Note", (By.XPATH, "//button[contains(., '+ Add Note')]")),
        ("xpath add note lower", (By.XPATH, "//*[self::button or self::a][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'add note')]")),
        ("xpath button contains Add", (By.XPATH, "//button[contains(., 'Add')]")),
        ("xpath contains +", (By.XPATH, "//button[contains(., '+')]")),
        ("xpath btn primary add", (By.XPATH, "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'add')]")),
    ]
    for name, loc in candidates:
        by, sel = loc
        try:
            els = driver.find_elements(by, sel)
        except Exception as ex:
            p(f"  {name}: find error {ex}")
            continue
        for el in els:
            try:
                if not el.is_displayed():
                    continue
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                driver.execute_script("arguments[0].click();", el)
                p(f"  CLICKED via {name}: {sel!r}")
                return True
            except Exception as ex:
                p(f"  {name}: click failed {ex}")
    p("  FAILED: could not click Add Note with any candidate.")
    return False


def _build_chrome_driver() -> webdriver.Chrome:
    opts = ChromeOptions()
    opts.add_argument("--window-size=1400,900")
    # headless=False (explicit: do not add --headless)
    implicit = int(read_config("timeouts", "implicit_wait").strip() or "10")
    page_load = int(read_config("timeouts", "page_load").strip() or "30")
    drv = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=opts,
    )
    drv.implicitly_wait(implicit)
    drv.set_page_load_timeout(page_load)
    return drv


def step1_notes_dom(p, driver) -> None:
    _banner(p, "STEP 1: NOTES PAGE DOM INSPECTION")
    username = read_config("api", "username").strip()
    password = read_config("api", "password").strip()
    login_url = read_config("urls", "notes_login_url").strip()
    notes_base = read_config("urls", "base_url").strip()

    p(f"[1a] Credentials: username={username!r} password={'***' if password else '(empty)'}")
    p(f"[1b] Navigating to login: {login_url}")
    driver.get(login_url)

    p("[1c] Logging in...")
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "email")))
        driver.find_element(By.ID, "email").clear()
        driver.find_element(By.ID, "email").send_keys(username)
        driver.find_element(By.ID, "password").clear()
        driver.find_element(By.ID, "password").send_keys(password)
        btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", btn)
    except Exception as ex:
        p(f"[ERROR] Login failed: {ex}")
        return

    p(f"[1d] After login, waiting 5s for page to settle. current_url={driver.current_url!r}")
    time.sleep(5)

    if notes_base and notes_base not in driver.current_url:
        p(f"[info] Navigating to notes base URL: {notes_base}")
        driver.get(notes_base)
        time.sleep(3)

    p("[1e] FULL document.body outerHTML:")
    body_html = _body_outer_html(driver)
    p(body_html)
    p(f"--- (body HTML length: {len(body_html)} chars) ---")

    _print_elements_class_hints(p, driver, CLASS_HINTS_STEP1, "[1f] Elements with class hints (card|note|item|list-item|title)")

    if not _click_add_note(p, driver):
        p("[1g] Skipping modal / save steps because Add Note was not clicked.")
        return

    p("[1g] Waiting 2s after Add Note click...")
    time.sleep(2)
    _print_visible_modal_html(p, driver)

    p("[1h-i] Filling modal title/description and saving...")
    try:
        title_el = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "title")))
        title_el.clear()
        title_el.send_keys("TestDiagnostic")
        desc_el = driver.find_element(By.ID, "description")
        desc_el.clear()
        desc_el.send_keys("test desc")
    except Exception as ex:
        p(f"[WARN] Could not use id=title/description: {ex}. Trying common alternatives...")
        try:
            driver.find_element(By.NAME, "title").send_keys("TestDiagnostic")
            driver.find_element(By.NAME, "description").send_keys("test desc")
        except Exception as ex2:
            p(f"[ERROR] Could not fill title/description: {ex2}")
            return

    save_clicked = False
    for by, sel in [
        (By.XPATH, "//button[contains(., 'Create')]"),
        (By.XPATH, "//button[contains(., 'Save')]"),
        (By.CSS_SELECTOR, "button[type='submit']"),
    ]:
        try:
            for el in driver.find_elements(by, sel):
                if el.is_displayed():
                    driver.execute_script("arguments[0].click();", el)
                    p(f"  Save clicked: {sel!r}")
                    save_clicked = True
                    break
            if save_clicked:
                break
        except Exception:
            continue
    if not save_clicked:
        p("[WARN] No save/create button clicked.")

    p("[1j] Waiting 3s after save...")
    time.sleep(3)
    _print_elements_class_hints(
        p, driver, CLASS_HINTS_STEP1, "[1j] Elements with class hints AFTER save (tag + class + text)"
    )


def step2_login_dom(p, driver) -> None:
    _banner(p, "STEP 2: LOGIN PAGE DOM INSPECTION")
    login_url = read_config("urls", "notes_login_url").strip()
    p("[2a] Clearing cookies so login form is reachable, then opening login page.")
    driver.delete_all_cookies()
    driver.get(login_url)
    time.sleep(1)

    p("[2b] Entering invalid email + wrong password, clicking login...")
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "email")))
        driver.find_element(By.ID, "email").clear()
        driver.find_element(By.ID, "email").send_keys("notanemail")
        driver.find_element(By.ID, "password").clear()
        driver.find_element(By.ID, "password").send_keys("wrong")
        btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", btn)
    except Exception as ex:
        p(f"[ERROR] Step2 login interaction failed: {ex}")
        return

    p("[2c] Waiting 5s for error UI...")
    time.sleep(5)

    _print_feedback_elements(p, driver, "[2d-e] Feedback-like elements (toast|alert|error|...)")
    p("[2f] FULL document.body outerHTML:")
    p(_body_outer_html(driver))


def step3_register_dom(p, driver) -> None:
    _banner(p, "STEP 3: REGISTER PAGE DOM INSPECTION")
    register_url = read_config("urls", "notes_register_url").strip()
    default_pw = read_config("api", "default_password").strip()
    wrong_pw = read_config("api", "wrong_password").strip() or "WrongPassword@123"
    unique_email = f"dominspect_{int(time.time())}@example.com"

    # --- empty name scenario ---
    p("[3a-d] Register: empty name, valid email/password/confirm, submit")
    driver.delete_all_cookies()
    driver.get(register_url)
    time.sleep(1)
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "email")))
        driver.find_element(By.ID, "name").clear()
        driver.find_element(By.ID, "email").clear()
        driver.find_element(By.ID, "email").send_keys(unique_email)
        driver.find_element(By.ID, "password").clear()
        driver.find_element(By.ID, "password").send_keys(default_pw)
        driver.find_element(By.ID, "confirmPassword").clear()
        driver.find_element(By.ID, "confirmPassword").send_keys(default_pw)
        btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", btn)
    except Exception as ex:
        p(f"[ERROR] Register empty-name flow failed: {ex}")
    time.sleep(5)
    _print_feedback_elements(p, driver, "[3d-e] After EMPTY NAME submit — feedback elements")
    p("[3f] FULL document.body outerHTML (empty name scenario):")
    p(_body_outer_html(driver))

    # --- mismatched passwords ---
    _banner(p, "STEP 3 (continued): MISMATCHED PASSWORDS", "=")
    unique_email2 = f"dominspect_{int(time.time())}@example.com"
    p("[3f] Register: mismatched password vs confirm")
    driver.get(register_url)
    time.sleep(1)
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "email")))
        driver.find_element(By.ID, "name").clear()
        driver.find_element(By.ID, "name").send_keys("Dom Inspect User")
        driver.find_element(By.ID, "email").clear()
        driver.find_element(By.ID, "email").send_keys(unique_email2)
        driver.find_element(By.ID, "password").clear()
        driver.find_element(By.ID, "password").send_keys(default_pw)
        driver.find_element(By.ID, "confirmPassword").clear()
        driver.find_element(By.ID, "confirmPassword").send_keys(wrong_pw)
        btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", btn)
    except Exception as ex:
        p(f"[ERROR] Mismatched password flow failed: {ex}")
    time.sleep(5)
    _print_feedback_elements(p, driver, "[3f] After MISMATCHED PASSWORDS — feedback elements")
    p("[3f] FULL document.body outerHTML (mismatched passwords scenario):")
    p(_body_outer_html(driver))


def main() -> None:
    log_path = _log_path()
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    old_stdout = sys.stdout
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"dom_inspection started {datetime.now().isoformat()}\n")
        log_file.flush()
        sys.stdout = DualWriter(log_file)
        try:
            p = lambda *a, **k: print(*a, **k)
            _banner(p, "DOM INSPECTION SCRIPT — practice.expandtesting.com /notes")
            p(f"Log file: {log_path}")
            p(f"Project root: {PROJECT_ROOT}")
            p("Chrome: headful (headless=False). Close the browser window to abort.\n")

            driver = _build_chrome_driver()
            try:
                step1_notes_dom(p, driver)
                step2_login_dom(p, driver)
                step3_register_dom(p, driver)
            finally:
                p("\nClosing browser...")
                driver.quit()

            _banner(p, "DONE — inspect console and logs/dom_inspection.log")
        finally:
            sys.stdout = old_stdout

    print(f"\n[inspect_dom] Wrote full transcript to: {log_path}")


if __name__ == "__main__":
    main()
