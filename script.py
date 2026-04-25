import os
import time
import datetime
import ftplib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def upload_to_ftp(local_file_path):
    FTP_HOST = "ftpupload.net"
    FTP_USER = "if0_40253796"
    FTP_PASS = "TL1pBn84f4JIXtI"
    REMOTE_FOLDER = "htdocs/sales_data"
    TARGET_FILENAME = "invoice.xlsx"

    print(f"☁️ Connecting to FTP: {FTP_HOST}...")
    try:
        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.encoding = "utf-8"
            ftp.cwd(REMOTE_FOLDER)
            files_in_folder = ftp.nlst()
            if TARGET_FILENAME in files_in_folder:
                ftp.delete(TARGET_FILENAME)
            with open(local_file_path, "rb") as file:
                ftp.storbinary(f"STOR {TARGET_FILENAME}", file)
            print("🎯 FTP Upload Complete!")
    except Exception as e:
        print(f"❌ FTP Error: {e}")
        raise e

def castrol_automation():
    download_dir = os.path.join(os.getcwd(), "downloads")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": download_dir})
    wait = WebDriverWait(driver, 35)

    try:
        # --- PHASE 1: LOGIN ---
        print("🚀 Opening Castrol Portal...")
        driver.get("https://cildist.castroldms.com")
        USERNAME = os.getenv("SITE_USERNAME")
        PASSWORD = os.getenv("SITE_PASSWORD")

        wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
        driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))

        # --- PHASE 2: SESSION CONFLICT ---
        time.sleep(7)
        if "already logged in" in driver.page_source.lower():
            print("⚠️ Session conflict! Forcing logout...")
            logout_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Logout')]")
            if logout_btns:
                driver.execute_script("arguments[0].click();", logout_btns[0])
                time.sleep(5)
                wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
                driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
                driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))

        # --- PHASE 3: DOWNLOAD ---
        print("📂 Navigating to Export page...")
        driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")
        excel_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Save as Excel')]")))
        driver.execute_script("arguments[0].click();", excel_btn)
        print("⏳ Downloading (50s)...")
        time.sleep(50) 

        # --- PHASE 4: FILE HANDLING & FTP ---
        files = [f for f in os.listdir(download_dir) if f.endswith('.xlsx')]
        if files:
            latest_file = max([os.path.join(download_dir, f) for f in files], key=os.path.getctime)
            final_local_path = os.path.join(download_dir, "invoice.xlsx")
            if os.path.exists(final_local_path): os.remove(final_local_path)
            os.rename(latest_file, final_local_path)
            upload_to_ftp(final_local_path)
        else:
            raise Exception("❌ No Excel file found.")

        # --- PHASE 5: REFRESH DASHBOARD ---
        print("🌐 Visiting Dashboard to refresh data...")
        driver.get("https://krishmo.xo.je/?i=1")
        time.sleep(5) # Wait for page load
        
        try:
            # Look for an icon or button that represents 'refresh'
            # Using XPATH to find common refresh icons or text
            refresh_icon = wait.until(EC.presence_of_element_located((By.XPATH, "//i[contains(@class, 'refresh')] | //button[contains(@class, 'refresh')] | //a[contains(@href, 'refresh')]")))
            driver.execute_script("arguments[0].click();", refresh_icon)
            print("🔄 Dashboard Refresh triggered!")
            time.sleep(3)
        except:
            print("⚠️ Could not find a specific refresh icon, but page was visited.")

        print("🏁 All Tasks Completed Successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        driver.save_screenshot("error_debug.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    castrol_automation()
