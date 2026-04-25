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

    print(f"☁️ Connecting to FTP...")
    try:
        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.encoding = "utf-8"
            ftp.cwd(REMOTE_FOLDER)
            if TARGET_FILENAME in ftp.nlst():
                ftp.delete(TARGET_FILENAME)
            with open(local_file_path, "rb") as file:
                ftp.storbinary(f"STOR {TARGET_FILENAME}", file)
            print("🎯 FTP Upload Complete!")
    except Exception as e:
        print(f"❌ FTP Error: {e}")
        raise e

def castrol_automation():
    download_dir = os.path.join(os.getcwd(), "downloads")
    if not os.path.exists(download_dir): os.makedirs(download_dir)

    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Force Chrome to allow downloads in headless mode
    prefs = {"download.default_directory": download_dir, "download.prompt_for_download": False}
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Specific CDP command for GitHub Actions headless downloads
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": download_dir})
    
    wait = WebDriverWait(driver, 40)

    try:
        # --- PHASE 1: LOGIN ---
        print("🚀 Opening Castrol Portal...")
        driver.get("https://cildist.castroldms.com")
        USERNAME = os.getenv("SITE_USERNAME")
        PASSWORD = os.getenv("SITE_PASSWORD")

        wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
        driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))

        # --- PHASE 2: SESSION CONFLICT RECOVERY ---
        time.sleep(10) # Give it time to show the popup
        if "already logged in" in driver.page_source.lower():
            print("⚠️ Session conflict detected! Forcing logout...")
            logout_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Logout')]")
            if logout_btns:
                driver.execute_script("arguments[0].click();", logout_btns[0])
                time.sleep(8) # Wait for page to clear
                # Re-enter credentials
                wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
                driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
                driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
                time.sleep(5)

        # --- PHASE 3: NAVIGATION ---
        # Ensure we are logged in by checking for a dashboard element
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "skin-blue")))
        print("📂 Navigating to Export page...")
        driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")

        # --- PHASE 4: DOWNLOAD (THE FIX) ---
        print("💾 Clicking 'Save as Excel'...")
        excel_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Save as Excel')]")))
        driver.execute_script("arguments[0].click();", excel_btn)
        
        print("⏳ Monitoring Download Folder (Up to 90s)...")
        # Check every 10 seconds for the file
        download_success = False
        for i in range(9):
            time.sleep(10)
            current_files = os.listdir(download_dir)
            print(f"📁 Files found: {current_files}")
            if any(f.endswith('.xlsx') for f in current_files):
                download_success = True
                break
        
        if not download_success:
            raise Exception("❌ Download failed: No XLSX file arrived.")

        # --- PHASE 5: FILE PROCESS & UPLOAD ---
        xlsx_files = [f for f in os.listdir(download_dir) if f.endswith('.xlsx')]
        latest_file = max([os.path.join(download_dir, f) for f in xlsx_files], key=os.path.getctime)
        final_local_path = os.path.join(download_dir, "invoice.xlsx")
        
        if os.path.exists(final_local_path): os.remove(final_local_path)
        os.rename(latest_file, final_local_path)
        print(f"✅ Local file ready: {final_local_path}")
        
        upload_to_ftp(final_local_path)

        # --- PHASE 6: WEBSITE REFRESH ---
        print(f"🌐 Refreshing Dashboard: https://krishmo.xo.je/?i=1")
        # Visiting with a timestamp helps bypass InfinityFree cache
        driver.get(f"https://krishmo.xo.je/?i=1&t={int(time.time())}")
        time.sleep(10)
        
        try:
            refresh_btn = wait.until(EC.presence_of_element_located((By.ID, "refresh-button")))
            driver.execute_script("arguments[0].click();", refresh_btn)
            print("🔄 Dashboard Refresh Clicked!")
            time.sleep(5)
        except:
            print("⚠️ Dashboard refresh button not clicked, but page was visited.")

        print("🏁 MISSION COMPLETE!")

    except Exception as e:
        print(f"❌ Automation Error: {e}")
        driver.save_screenshot("debug_error.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    castrol_automation()
