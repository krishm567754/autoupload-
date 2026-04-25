import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

USERNAME = os.getenv("SITE_USERNAME")
PASSWORD = os.getenv("SITE_PASSWORD")

DOWNLOAD_DIR = "/tmp"

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
    driver.find_element(By.NAME, "Password").submit()
    time.sleep(5)

    # ===== HANDLE POPUP =====
    print("Checking popup...")
    logout_popup = driver.find_elements(By.XPATH, "//*[contains(text(),'Logout')]")
    if logout_popup:
        print("Popup found → clicking logout")
        logout_popup[0].click()
        time.sleep(5)

        # re-login
        driver.find_element(By.NAME, "UserId").send_keys(USERNAME)
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
        driver.find_element(By.NAME, "Password").submit()
        time.sleep(6)

    print("Login done, URL:", driver.current_url)

    # ===== OPEN REPORT PAGE =====
    driver.get("https://cildist.castroldms.com/Reports/InvoiceDataToExcel")
    time.sleep(8)

    # ===== CLICK LOAD DATA =====
    print("Click Load Data...")
    load_btns = driver.find_elements(By.XPATH, "//input[contains(@value,'Load')] | //button[contains(.,'Load')]")
    if load_btns:
        load_btns[0].click()
    else:
        raise Exception("Load Data not found")

    time.sleep(6)

    # ===== CLICK SAVE AS EXCEL =====
    print("Click Save as Excel...")

    excel_btns = driver.find_elements(By.XPATH,
        "//*[contains(text(),'Excel')] | " +
        "//input[contains(@value,'Excel')] | " +
        "//*[contains(@class,'excel')] | " +
        "//i[contains(@class,'excel')]"
    )

    print("Excel buttons found:", len(excel_btns))

    if excel_btns:
        driver.execute_script("arguments[0].click();", excel_btns[0])
        print("Excel clicked ✅")
    else:
        driver.save_screenshot("excel_not_found.png")
        raise Exception("Excel button not found")

    time.sleep(12)

    # ===== CHECK DOWNLOAD =====
    files = os.listdir(DOWNLOAD_DIR)
    print("Downloaded files:", files)

except Exception as e:
    print("ERROR:", e)

finally:
    driver.quit()
