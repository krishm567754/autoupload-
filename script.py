import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

USERNAME = os.getenv("SITE_USERNAME")
PASSWORD = os.getenv("SITE_PASSWORD")

DOWNLOAD_DIR = "/tmp"

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options)

try:
    driver.get("https://cildist.castroldms.com")

    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[contains(text(),'Login')]").click()

    time.sleep(5)

    driver.get("https://cildist.castroldms.com/Reports/InvoiceDataToExcel")

    time.sleep(5)

    driver.find_element(By.XPATH, "//button[contains(text(),'Load Data')]").click()

    time.sleep(5)

    driver.find_element(By.XPATH, "//button[contains(text(),'Excel')]").click()

    time.sleep(10)

    files = os.listdir(DOWNLOAD_DIR)
    print("Downloaded files:", files)

except Exception as e:
    print("Error:", e)

finally:
    driver.quit()
