import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ====== LOGIN DETAILS ======
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

    # ===== LOGIN =====
    print("Logging in...")

    driver.find_element(By.NAME, "UserId").send_keys(USERNAME)
    driver.find_element(By.NAME, "Password").send_keys(PASSWORD)

    # ✅ Correct form submit
    driver.find_element(By.NAME, "Password").submit()

    time.sleep(8)

    print("Current URL after login:", driver.current_url)

    # ✅ Proper login check
    if "forget-password" in driver.current_url.lower() or "login" in driver.current_url.lower():
        print("LOGIN FAILED ❌")
        driver.save_screenshot("login_failed.png")
        raise Exception("Login failed")

    print("Login successful ✅")

    # ===== OPEN REPORT PAGE =====
    print("Opening report page...")
    driver.get("https://cildist.castroldms.com/Reports/InvoiceDataToExcel")
    time.sleep(8)

    print("Current URL after opening report:", driver.current_url)
    print("Page title:", driver.title)

    # ===== CLICK LOAD DATA =====
    print("Searching for Load Data...")

    load_elements = driver.find_elements(By.XPATH, "//*[contains(text(),'Load')] | //input[contains(@value,'Load')]")
    print("Load elements found:", len(load_elements))

    if load_elements:
        load_elements[0].click()
        print("Clicked Load Data")
    else:
        driver.save_screenshot("load_not_found.png")
        raise Exception("Load Data button not found")

    time.sleep(6)

    # ===== CLICK EXCEL =====
    print("Searching for Excel button...")

    excel_elements = driver.find_elements(By.XPATH, "//*[contains(text(),'Excel')] | //input[contains(@value,'Excel')]")
    print("Excel elements found:", len(excel_elements))

    if excel_elements:
        excel_elements[0].click()
        print("Clicked Excel")
    else:
        driver.save_screenshot("excel_not_found.png")
        raise Exception("Excel button not found")

    time.sleep(12)

    # ===== CHECK DOWNLOAD =====
    print("Checking downloaded files...")
    files = os.listdir(DOWNLOAD_DIR)
    print("Downloaded files:", files)

except Exception as e:
    print("ERROR:", e)

finally:
    driver.quit()
