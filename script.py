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

    print("Logging in...")

    # ✅ FIXED selectors
    driver.find_element(By.NAME, "UserId").send_keys(USERNAME)
    driver.find_element(By.NAME, "Password").send_keys(PASSWORD)

    # login button (generic submit)
    driver.find_element(By.XPATH, "//button").click()

    time.sleep(6)

    print("Opening report page...")
    driver.get("https://cildist.castroldms.com/Reports/InvoiceDataToExcel")

    time.sleep(6)

    print("Click Load Data...")
    driver.find_element(By.XPATH, "//button[contains(.,'Load')]").click()

    time.sleep(6)

    print("Click Excel...")
    driver.find_element(By.XPATH, "//button[contains(.,'Excel')]").click()

    time.sleep(12)

    files = os.listdir(DOWNLOAD_DIR)
    print("Downloaded files:", files)

except Exception as e:
    print("ERROR:", e)

finally:
    driver.quit()
