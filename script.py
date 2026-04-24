import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

USERNAME = os.getenv("SITE_USERNAME")
PASSWORD = os.getenv("SITE_PASSWORD")

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.binary_location = "/usr/bin/chromium-browser"

service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

try:
    print("Opening site...")
    driver.get("https://cildist.castroldms.com")
    time.sleep(3)

    print("Logging in...")

    driver.find_element(By.NAME, "UserId").send_keys(USERNAME)
    driver.find_element(By.NAME, "Password").send_keys(PASSWORD)

    # try multiple login methods
    driver.find_element(By.XPATH, "//button | //input[@type='submit']").click()

    time.sleep(8)

    print("Current URL after login:", driver.current_url)

    # check if login failed
    if "login" in driver.current_url.lower():
        print("LOGIN FAILED ❌")
        driver.save_screenshot("login_failed.png")
        raise Exception("Login not successful")

    print("Login successful ✅")

    # wait more for dashboard
    time.sleep(5)

    print("Opening report page...")
    driver.get("https://cildist.castroldms.com/Reports/InvoiceDataToExcel")

    time.sleep(8)

    print("Current URL after opening report:", driver.current_url)

    # debug: print page source small part
    print("Page title:", driver.title)

    # try clicking Load Data (multiple options)
    print("Trying to click Load Data...")

    elements = driver.find_elements(By.XPATH, "//*[contains(text(),'Load')]")
    print("Found Load elements:", len(elements))

    if elements:
        elements[0].click()
    else:
        raise Exception("Load Data button not found")

    time.sleep(5)

    print("Trying Excel button...")

    excel_btns = driver.find_elements(By.XPATH, "//*[contains(text(),'Excel')]")
    print("Found Excel buttons:", len(excel_btns))

    if excel_btns:
        excel_btns[0].click()
    else:
        raise Exception("Excel button not found")

    time.sleep(10)

    files = os.listdir("/tmp")
    print("Downloaded files:", files)

except Exception as e:
    print("ERROR:", e)

finally:
    driver.quit()
