import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ====== LOGIN DETAILS FROM GITHUB SECRETS ======
USERNAME = os.getenv("SITE_USERNAME")
PASSWORD = os.getenv("SITE_PASSWORD")

# ====== DOWNLOAD FOLDER ======
DOWNLOAD_DIR = "/tmp"

# ====== CHROME SETUP (IMPORTANT FIX) ======
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Tell Selenium to use Chromium (GitHub environment)
options.binary_location = "/usr/bin/chromium-browser"

prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
}
options.add_experimental_option("prefs", prefs)

service = Service("/usr/bin/chromedriver")

driver = webdriver.Chrome(service=service, options=options)

try:
    print("Opening website...")
    driver.get("https://cildist.castroldms.com")

    time.sleep(3)

    print("Logging in...")
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[contains(text(),'Login')]").click()

    time.sleep(6)

    print("Opening report page...")
    driver.get("https://cildist.castroldms.com/Reports/InvoiceDataToExcel")

    time.sleep(6)

    print("Clicking Load Data...")
    driver.find_element(By.XPATH, "//button[contains(text(),'Load Data')]").click()

    time.sleep(6)

    print("Clicking Save as Excel...")
    driver.find_element(By.XPATH, "//button[contains(text(),'Excel')]").click()

    time.sleep(12)  # wait for download

    print("Checking downloaded files...")
    files = os.listdir(DOWNLOAD_DIR)
    print("Downloaded files:", files)

except Exception as e:
    print("ERROR OCCURRED:", e)

finally:
    driver.quit()
