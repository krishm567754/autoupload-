import os
import time
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
    TARGET_FILENAME = "sales_data.xlsx" 

    print(f"☁️ Connecting to FTP: {FTP_HOST}...")
    try:
        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.encoding = "utf-8"
            print(f"📂 Navigating to {REMOTE_FOLDER}...")
            ftp.cwd(REMOTE_FOLDER)

            files_in_folder = ftp.nlst()
            if TARGET_FILENAME in files_in_folder:
                print(f"🗑️ Deleting existing {TARGET_FILENAME}...")
                ftp.delete(TARGET_FILENAME)

            print(f"📤 Uploading fresh {TARGET_FILENAME}...")
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

    for f in os.listdir(download_dir):
        os.remove(os.path.join(download_dir, f))

    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Enable browser logging for debug
    chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": download_dir
    })

    wait = WebDriverWait(driver, 35)

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
        time.sleep(7)
        if "already logged in" in driver.page_source.lower():
            print("⚠️ Session conflict detected! Forcing logout...")
            try:
                found_logout_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Logout')]")
                if found_logout_buttons:
                    driver.execute_script("arguments[0].click();", found_logout_buttons[0])
                    print("🖱️ Logout button clicked...")
                    time.sleep(5)
                    wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
                    driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
                    driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
            except Exception as e:
                print(f"⚠️ Conflict bypass attempt failed: {e}")

        # --- PHASE 3: NAVIGATION ---
        print("📂 Navigating directly to Invoice Export page...")
        time.sleep(3)
        driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")

        # --- PHASE 4: DOWNLOAD ---
        print("💾 Clicking 'Save as Excel'...")
        excel_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Save as Excel')]")))
        driver.execute_script("arguments[0].click();", excel_btn)
        
        print("⏳ Waiting for file download to complete...")
        download_timeout = 120
        file_ready = False
        
        for _ in range(download_timeout):
            all_files = os.listdir(download_dir)
            xlsx_files = [f for f in all_files if f.endswith('.xlsx')]
            temp_files = [f for f in all_files if f.endswith('.crdownload') or f.endswith('.tmp')]
            
            if xlsx_files and not temp_files:
                file_ready = True
                break
            time.sleep(1)

        if not file_ready:
            raise Exception("❌ Download timed out. The file took too long or failed to generate.")

        # --- PHASE 5: FILE PROCESS & UPLOAD ---
        files = [f for f in os.listdir(download_dir) if f.endswith('.xlsx')]
        latest_file = max([os.path.join(download_dir, f) for f in files], key=os.path.getctime)
        final_local_path = os.path.join(download_dir, "sales_data.xlsx")
        
        if os.path.exists(final_local_path):
            os.remove(final_local_path)
            
        os.rename(latest_file, final_local_path)
        print(f"✅ File {final_local_path} ready for upload.")
        
        upload_to_ftp(final_local_path)

        # --- PHASE 6: DASHBOARD REFRESH (DEBUG ENABLED) ---
        DASHBOARD_URL = "https://krishmodiexp.xo.je/" 
        print(f"🌐 Opening Dashboard to Trigger Refresh: {DASHBOARD_URL}")
        
        driver.get(DASHBOARD_URL)
        
        print("⏳ Waiting 10 seconds for page load and InfinityFree anti-bot bypass...")
        time.sleep(10) 
        
        # Check initial status
        try:
            initial_status = driver.find_element(By.ID, "syncStatus").text
            print(f"📊 Initial Dashboard Status: {initial_status}")
        except:
            print("⚠️ Could not find #syncStatus element. Anti-bot might still be active.")

        # Find the sync button and click it
        sync_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".refresh-btn")))
        driver.execute_script("arguments[0].click();", sync_btn)
        print("🔄 Dashboard Refresh Clicked!")
        print("⏳ Waiting for Dashboard JS Engine to calculate (Watching for ✅ or ❌)...")

        # Custom Wait: Look for either Success OR Error
        def check_status_complete(d):
            try:
                t = d.find_element(By.ID, "syncStatus").text
                if "✅" in t or "❌" in t:
                    return t
                return False
            except:
                return False
                
        final_result = WebDriverWait(driver, 150).until(check_status_complete)
        
        if "✅" in final_result:
            print(f"🏁 MISSION COMPLETE! Dashboard successfully synced: {final_result}")
        else:
            print(f"\n⚠️ DASHBOARD ENCOUNTERED AN ERROR: {final_result}")
            print("\n--- BROWSER CONSOLE LOGS ---")
            for entry in driver.get_log('browser'):
                print(entry)
            print("----------------------------\n")
            raise Exception(f"Dashboard sync failed with internal error: {final_result}")

    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            driver.save_screenshot("final_error_debug.png")
            print("📸 Error screenshot saved as final_error_debug.png")
        except:
            pass
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    castrol_automation()
