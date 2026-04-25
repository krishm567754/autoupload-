import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ====== CREDENTIALS ======
USERNAME = os.getenv("SITE_USERNAME")
PASSWORD = os.getenv("SITE_PASSWORD")

DOWNLOAD_DIR = "/tmp"

# ====== CHROME SETUP ======
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.binary_location = "/usr/bin/chromium-browser"

prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
}
options.add_experimental_option("prefs", prefs)

service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

try:
    print("Opening site...")
    driver.get("https://cildist.castroldms.com")
    time.sleep(3)

    # ===== LOGIN (STABLE) =====
    print("Logging in...")

    user = driver.find_element(By.NAME, "UserId")
    pwd = driver.find_element(By.NAME, "Password")

    user.clear()
    user.send_keys(USERNAME)

    pwd.clear()
    pwd.send_keys(PASSWORD)

    # submit form
    pwd.submit()

    time.sleep(8)

    print("URL after login:", driver.current_url)

    # STRICT CHECK
    if "forget-password" in driver.current_url.lower() or "login" in driver.current_url.lower():
        driver.save_screenshot("login_failed.png")
        raise Exception("❌ Login failed")

    print("✅ Login successful")

    # ===== OPEN REPORT =====
    print("Opening report page...")
    driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")
    time.sleep(8)

    # ===== FIND BUTTONS =====
    print("Finding buttons...")
    buttons = driver.find_elements(By.CLASS_NAME, "btn")
    print("Total buttons found:", len(buttons))

    # ===== CLICK LOAD DATA =====
    print("Clicking Load Data...")
    clicked = False
    for btn in buttons:
        cls = btn.get_attribute("class")
        if "btn-primary" in cls:
            driver.execute_script("arguments[0].click();", btn)
            clicked = True
            break

    if not clicked:
        raise Exception("Load Data button not found")

    time.sleep(6)

    # ===== CLICK EXCEL =====
    print("Clicking Excel...")

    buttons = driver.find_elements(By.CLASS_NAME, "btn")
    print("Buttons after load:", len(buttons))

    # try last button (usually Excel)
    driver.execute_script("arguments[0].click();", buttons[-1])

    time.sleep(12)

    # ===== CHECK DOWNLOAD =====
    files = os.listdir(DOWNLOAD_DIR)
    print("Downloaded files:", files)

except Exception as e:
    print("ERROR:", e)

finally:
    driver.quit()
