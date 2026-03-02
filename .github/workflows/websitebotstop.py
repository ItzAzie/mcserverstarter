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
        username = wait.until(
            EC.presence_of_element_located((By.ID, "identifier-field"))
        )
        print("Username page:", driver.current_url)

        username.send_keys(username_value)
        username.send_keys(Keys.RETURN)
        time.sleep(3)

    except Exception as e:
        print("Username error:", e)
        return False

    try:
        # Check invalid username
        try:
            error_elem = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.ID, "error-identifier"))
            )
            if error_elem:
                print("❌ Invalid username")
                return False
        except:
            pass

        password = wait.until(
            EC.presence_of_element_located((By.ID, "password-field"))
        )

        print("Password page:", driver.current_url)

        password.send_keys(password_value)
        password.send_keys(Keys.RETURN)
        time.sleep(5)

        return True

    except Exception as e:
        print("Password error:", e)
        return False


# ----------------------------
# LOGIN CHECK
# ----------------------------

try:
    WebDriverWait(driver, 10).until(
        lambda d: "dashboard" in d.current_url
    )
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
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-error')]"))
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