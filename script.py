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
    # FTP Configuration
    FTP_HOST = "ftpupload.net"
    FTP_USER = "if0_40253796"
    FTP_PASS = "TL1pBn84f4JIXtI"
    REMOTE_FOLDER = "htdocs/sales_data"
    TARGET_FILENAME = "invoice.xlsx"

    print(f"☁️ Connecting to FTP: {FTP_HOST}...")
    try:
        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.encoding = "utf-8"
            print(f"📂 Navigating to {REMOTE_FOLDER}...")
            ftp.cwd(REMOTE_FOLDER)

            # Delete the previous file if it exists to ensure a clean upload
            files_in_folder = ftp.nlst()
            if TARGET_FILENAME in files_in_folder:
                print(f"🗑️ Deleting existing {TARGET_FILENAME}...")
                ftp.delete(TARGET_FILENAME)

            # Upload the new file in binary mode
            print(f"📤 Uploading fresh {TARGET_FILENAME}...")
            with open(local_file_path, "rb") as file:
                ftp.storbinary(f"STOR {TARGET_FILENAME}", file)
            print("🎯 FTP Upload Complete!")
    except Exception as e:
        print(f"❌ FTP Error: {e}")
        raise e

def castrol_automation():
    # 1. Setup Download Directory
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

    # Enable headless downloads
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": download_dir
    })

    wait = WebDriverWait(driver, 40)

    try:
        # --- PHASE 1: LOGIN ---
        print("🚀 Opening Castrol Portal...")
        driver.get("https://cildist.castroldms.com")
        USERNAME = os.getenv("SITE_USERNAME")
        PASSWORD = os.getenv("SITE_PASSWORD")

        user_field = wait.until(EC.presence_of_element_located((By.NAME, "UserId")))
        user_field.send_keys(USERNAME)
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
        
        login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", login_btn)

        # --- PHASE 2: SESSION CONFLICT ---
        time.sleep(8)
        if "already logged in" in driver.page_source.lower():
            print("⚠️ Session conflict detected! Forcing logout...")
            try:
                found_logout_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Logout')]")
                if found_logout_buttons:
                    driver.execute_script("arguments[0].click();", found_logout_buttons[0])
                    time.sleep(6)
                    # Re-enter credentials
                    wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
                    driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
                    driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
            except Exception as e:
                print(f"⚠️ Conflict bypass attempt failed: {e}")

        # --- PHASE 3: NAVIGATION ---
        print("📂 Navigating to Invoice Export page...")
        time.sleep(4)
        driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")

        # --- PHASE 4: DOWNLOAD ---
        print("💾 Clicking 'Save as Excel'...")
        excel_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Save as Excel')]")))
        driver.execute_script("arguments[0].click();", excel_btn)
        
        print("⏳ Waiting for report generation (60s)...")
        time.sleep(60) 

        # --- PHASE 5: FILE PROCESS & UPLOAD ---
        files = [f for f in os.listdir(download_dir) if f.endswith('.xlsx')]
        if not files:
            time.sleep(15) # Extra buffer
            files = [f for f in os.listdir(download_dir) if f.endswith('.xlsx')]

        if files:
            latest_file = max([os.path.join(download_dir, f) for f in files], key=os.path.getctime)
            final_local_path = os.path.join(download_dir, "invoice.xlsx")
            
            if os.path.exists(final_local_path):
                os.remove(final_local_path)
                
            os.rename(latest_file, final_local_path)
            print(f"✅ File renamed to invoice.xlsx. Starting FTP upload...")
            
            upload_to_ftp(final_local_path)
        else:
            raise Exception("❌ No Excel file found in downloads folder.")

        # --- PHASE 6: DASHBOARD REFRESH ---
        # Using a timestamp to bypass any hosting cache
        timestamp = int(time.time())
        dashboard_url = f"https://krishmo.xo.je/?i=1&t={timestamp}"
        
        print(f"🌐 Visiting Dashboard: {dashboard_url}")
        driver.get(dashboard_url)
        time.sleep(10) # Wait for page load
        
        try:
            print("🔄 Locating and clicking the footer refresh button...")
            # ID from your dashboard code: id="refresh-button"
            refresh_btn = wait.until(EC.presence_of_element_located((By.ID, "refresh-button")))
            driver.execute_script("arguments[0].click();", refresh_btn)
            print("✨ Dashboard refresh triggered!")
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Could not click refresh button: {e}")

        print("🏁 MISSION COMPLETE! Data updated and Dashboard refreshed.")

    except Exception as e:
        print(f"❌ Automation Error: {e}")
        driver.save_screenshot("error_debug.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    castrol_automation()
