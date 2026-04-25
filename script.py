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

    # ===== HANDLE POPUP (IMPORTANT) =====
    print("Checking for session popup...")

    try:
        logout_popup = driver.find_elements(
            By.XPATH,
            "//*[contains(text(),'Logout')] | //button[contains(text(),'Logout')]"
        )

        if logout_popup:
            print("Popup detected → clicking Logout...")
            logout_popup[0].click()
            time.sleep(5)

            # After logout, login again
            print("Re-login after logout...")

            driver.find_element(By.NAME, "UserId").clear()
            driver.find_element(By.NAME, "UserId").send_keys(USERNAME)

            driver.find_element(By.NAME, "Password").clear()
            driver.find_element(By.NAME, "Password").send_keys(PASSWORD)

            driver.find_element(By.NAME, "Password").submit()
            time.sleep(6)

    except Exception as e:
        print("No popup or error handling popup:", e)

    print("Current URL after login:", driver.current_url)

    if "login" in driver.current_url.lower():
        raise Exception("Login failed ❌")

    print("Login successful ✅")

    # ===== OPEN REPORT PAGE =====
    print("Opening report page...")
    driver.get("https://cildist.castroldms.com/Reports/InvoiceDataToExcel")
    time.sleep(8)

    print("Searching Load Data...")

    load_btns = driver.find_elements(
        By.XPATH,
        "//*[contains(text(),'Load')] | //input[contains(@value,'Load')]"
    )

    if load_btns:
        load_btns[0].click()
        print("Clicked Load Data")
    else:
        raise Exception("Load Data not found")

    time.sleep(6)

    print("Searching Excel button...")

    excel_btns = driver.find_elements(
        By.XPATH,
        "//*[contains(text(),'Excel')] | //input[contains(@value,'Excel')]"
    )

    if excel_btns:
        excel_btns[0].click()
        print("Clicked Excel")
    else:
        raise Exception("Excel button not found")

    time.sleep(12)

    files = os.listdir(DOWNLOAD_DIR)
    print("Downloaded files:", files)

except Exception as e:
    print("ERROR:", e)

finally:
    driver.quit()
