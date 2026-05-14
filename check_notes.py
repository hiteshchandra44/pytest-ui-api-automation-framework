from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import sys

# Ensure project root is importable when running as a script
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utilities.config_reader import read_config

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()

EMAIL = read_config("api", "username").strip()   # Notes App email from config.ini
PASSWORD = read_config("api", "password").strip()  # Notes App password from config.ini

# --- REGISTER ON NOTES APP (run once, comment out after) ---
driver.get("https://practice.expandtesting.com/notes/app/register")
time.sleep(3)
print("Register page inputs:")
for el in driver.find_elements(By.TAG_NAME, "input"):
    print(f"  id='{el.get_attribute('id')}' name='{el.get_attribute('name')}'")

driver.find_element(By.ID, "email").send_keys(EMAIL)
driver.find_element(By.ID, "name").send_keys("Test User")
driver.find_element(By.ID, "password").send_keys(PASSWORD)
driver.find_element(By.ID, "confirmPassword").send_keys(PASSWORD)
btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
driver.execute_script("arguments[0].click();", btn)
time.sleep(4)
print("After register URL:", driver.current_url)

# --- LOGIN ON NOTES APP ---
driver.get("https://practice.expandtesting.com/notes/app/login")
time.sleep(3)
print("Login page inputs:")
for el in driver.find_elements(By.TAG_NAME, "input"):
    print(f"  id='{el.get_attribute('id')}' name='{el.get_attribute('name')}'")

driver.find_element(By.ID, "email").send_keys(EMAIL)
driver.find_element(By.ID, "password").send_keys(PASSWORD)
btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
driver.execute_script("arguments[0].click();", btn)
time.sleep(4)
print("After login URL:", driver.current_url)

# --- NOTES HOME PAGE ---
print("\n===== NOTES HOME - ALL BUTTONS =====")
for el in driver.find_elements(By.TAG_NAME, "button"):
    print(f"  id='{el.get_attribute('id')}' text='{el.text.strip()}' class='{el.get_attribute('class')[:50]}'")

print("\n===== NOTES HOME - ALL LINKS =====")
for el in driver.find_elements(By.TAG_NAME, "a"):
    href = el.get_attribute('href') or ''
    if 'notes' in href.lower() or el.text.strip():
        print(f"  href='{href}' text='{el.text.strip()}' id='{el.get_attribute('id')}'")

print("\n===== NOTES HOME - HEADINGS =====")
for tag in ["h1","h2","h3","h4","h5"]:
    for el in driver.find_elements(By.TAG_NAME, tag):
        if el.text.strip():
            print(f"  <{tag}> text='{el.text.strip()}' class='{el.get_attribute('class')}'")

# --- CLICK ADD NOTE BUTTON ---
print("\n===== TRYING TO CLICK ADD NOTE =====")
try:
    wait = WebDriverWait(driver, 10)
    # Try common patterns for add note button
    for selector in [
        "//button[contains(text(),'Add')]",
        "//button[contains(text(),'New')]", 
        "//button[contains(text(),'+')]",
        "//a[contains(text(),'Add')]",
        "//a[contains(@href,'new')]",
        "//a[contains(@href,'create')]",
    ]:
        els = driver.find_elements(By.XPATH, selector)
        if els:
            print(f"  Found via {selector}: text='{els[0].text}'")
            driver.execute_script("arguments[0].click();", els[0])
            time.sleep(3)
            break
except Exception as e:
    print("  Error:", e)

print("After clicking add note URL:", driver.current_url)

print("\n===== ADD NOTE FORM - ALL INPUTS =====")
for el in driver.find_elements(By.TAG_NAME, "input"):
    print(f"  id='{el.get_attribute('id')}' name='{el.get_attribute('name')}' placeholder='{el.get_attribute('placeholder')}' type='{el.get_attribute('type')}'")

print("\n===== ADD NOTE FORM - ALL TEXTAREAS =====")
for el in driver.find_elements(By.TAG_NAME, "textarea"):
    print(f"  id='{el.get_attribute('id')}' name='{el.get_attribute('name')}' placeholder='{el.get_attribute('placeholder')}'")

print("\n===== ADD NOTE FORM - ALL SELECTS =====")
for el in driver.find_elements(By.TAG_NAME, "select"):
    print(f"  id='{el.get_attribute('id')}' name='{el.get_attribute('name')}'")

print("\n===== ADD NOTE FORM - ALL BUTTONS =====")
for el in driver.find_elements(By.TAG_NAME, "button"):
    print(f"  id='{el.get_attribute('id')}' text='{el.text.strip()}' type='{el.get_attribute('type')}'")

input("\nPress Enter to close browser...")
driver.quit()