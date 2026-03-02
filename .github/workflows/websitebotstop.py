import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


# ----------------------------
# Chrome Setup (CI SAFE)
# ----------------------------

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--remote-debugging-port=9222")

# Optional anti-detection tweaks
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-extensions")
options.add_argument("--disable-popup-blocking")

# IMPORTANT:
# Do NOT set:
# - binary_location
# - user-data-dir
# - manual chromedriver path

service = Service()  # Selenium auto-manages chromedriver
driver = webdriver.Chrome(service=service, options=options)

wait = WebDriverWait(driver, 20)

driver.get("https://accounts.seedloaf.com/sign-in")

wait.until(lambda d: d.execute_script("return document.readyState") == "complete")


# ----------------------------
# LOGIN FUNCTION
# ----------------------------


def run_loginflow(username_value, password_value):
    try:
        # --- STEP 1: Wait for email field ---
        email_input = wait.until(
            EC.element_to_be_clickable((By.ID, "identifier-field"))
        )

        print("Email page:", driver.current_url)

        email_input.clear()
        email_input.send_keys(username_value)

        # Click submit button instead of RETURN (more reliable in CI)
        submit_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        submit_btn.click()

    except Exception as e:
        print("Username step error:", e)
        driver.save_screenshot("username_error.png")
        return False

    try:
        # --- STEP 2: Wait for password field to appear ---
        password_input = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='password']"))
        )

        print("Password page:", driver.current_url)

        password_input.clear()
        password_input.send_keys(password_value)

        submit_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        submit_btn.click()

    except Exception as e:
        print("Password step error:", e)
        driver.save_screenshot("password_error.png")
        return False

    try:
        # --- STEP 3: Confirm redirect away from sign-in ---
        wait.until(lambda d: "sign-in" not in d.current_url)
        print("Login redirect success:", driver.current_url)
        return True

    except Exception as e:
        print("Login redirect failed:", e)
        driver.save_screenshot("redirect_error.png")
        return False


# ----------------------------
# LOGIN CHECK
# ----------------------------

try:
    WebDriverWait(driver, 10).until(lambda d: "dashboard" in d.current_url)
    print("✅ Already logged in")

except:
    print("🔐 Logging in...")

    username_secret = os.getenv("USERNAME")
    password_secret = os.getenv("PASSWORD")

    if not username_secret or not password_secret:
        print("❌ Missing GitHub secrets")
        driver.quit()
        sys.exit(1)

    success = run_loginflow(username_secret, password_secret)

    if not success:
        driver.quit()
        sys.exit(1)


# ----------------------------
# STOP WORLD BUTTON LOGIC
# ----------------------------

try:
    wait = WebDriverWait(driver, 15)

    # Try Stop button
    try:
        stop_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@class, 'btn-error')]")
            )
        )
        stop_button.click()
        print("🛑 Clicked Stop button")
        time.sleep(3)

    except:
        # If Stop not found, maybe already stopped
        try:
            start_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-primary"))
            )
            print("ℹ️ World already stopped (Start button visible)")
        except:
            print("❌ Could not find Start or Stop button")
            driver.quit()
            sys.exit(1)

except Exception as e:
    print("Button handling error:", e)

driver.quit()
print("✅ Script finished cleanly")
