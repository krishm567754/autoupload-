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

    # ===== LOGIN (KEEP SIMPLE & SAME) =====
    print("Logging in...")
    driver.find_element(By.NAME, "UserId").send_keys(USERNAME)
    driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
    driver.find_element(By.NAME, "Password").submit()

    time.sleep(6)
    print("After login URL:", driver.current_url)

    # ===== OPEN REPORT PAGE =====
    driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")
    time.sleep(8)

    print("Finding buttons...")

    buttons = driver.find_elements(By.CLASS_NAME, "btn")
    print("Total buttons found:", len(buttons))

    # ===== CLICK LOAD DATA (usually first primary button) =====
    for btn in buttons:
        if "btn-primary" in btn.get_attribute("class"):
            print("Clicking Load Data button...")
            driver.execute_script("arguments[0].click();", btn)
            break

    time.sleep(6)

    # ===== CLICK EXCEL BUTTON =====
    print("Searching Excel button...")

    buttons = driver.find_elements(By.CLASS_NAME, "btn")
    print("Buttons after load:", len(buttons))

    # try clicking second primary button (Excel)
    clicked = False
    for btn in buttons:
        cls = btn.get_attribute("class")
        if "btn-success" in cls or "excel" in cls:
            driver.execute_script("arguments[0].click();", btn)
            clicked = True
            print("Clicked Excel")
            break

    if not clicked:
        print("Trying fallback click...")
        driver.execute_script("arguments[0].click();", buttons[-1])

    time.sleep(12)

    files = os.listdir(DOWNLOAD_DIR)
    print("Downloaded files:", files)

except Exception as e:
    print("ERROR:", e)

finally:
    driver.quit()
