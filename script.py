import os
import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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

    wait = WebDriverWait(driver, 30)

    try:
        # --- PHASE 1: LOGIN (The logic that worked) ---
        print("🚀 Opening Castrol Portal...")
        driver.get("https://cildist.castroldms.com")

        USERNAME = os.getenv("SITE_USERNAME")
        PASSWORD = os.getenv("SITE_PASSWORD")

        print(f"🔑 Logging in as: {USERNAME}")
        user_field = wait.until(EC.presence_of_element_located((By.NAME, "UserId")))
        user_field.send_keys(USERNAME)
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
        
        # Click the login button using the submit type (as seen in screenshot)
        login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        login_btn.click()

        # --- PHASE 2: SESSION CONFLICT ---
        time.sleep(5)
        if "already logged in" in driver.page_source.lower():
            print("⚠️ Session conflict! Forcing logout...")
            try:
                logout_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Logout')]")
                logout_btn.click()
                time.sleep(3)
                # Re-login
                wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
                driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            except:
                print("Proceeding past conflict check...")

        # --- PHASE 3: NAVIGATION & DOWNLOAD (Matches your video) ---
        print("📂 Navigating directly to Invoice Export page...")
        driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")

        print("💾 Clicking 'Save as Excel'...")
        # Finding the green button from your video
        excel_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-success")))
        excel_btn.click()
        
        # Wait for the "Loading..." spinner to finish (seen in video)
        print("⏳ Waiting for report generation and download (30s)...")
        time.sleep(30) 

        # --- PHASE 4: FILE VERIFICATION ---
        files = os.listdir(download_dir)
        if not files:
            # If no file, check if it's still 'crdownload' (Chrome's temp format)
            time.sleep(10)
            files = os.listdir(download_dir)

        if files:
            # Get the actual .xlsx file (ignore temp files)
            xlsx_files = [f for f in files if f.endswith('.xlsx')]
            if xlsx_files:
                latest_file = max([os.path.join(download_dir, f) for f in xlsx_files], key=os.path.getctime)
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                new_filename = f"sales_{date_str}.xlsx"
                new_path = os.path.join(download_dir, new_filename)
                
                os.rename(latest_file, new_path)
                print(f"✅ SUCCESS: File saved as {new_filename}")
                return new_path
        
        raise Exception("❌ File was not found in the downloads folder.")

    except Exception as e:
        print(f"❌ Automation Error: {e}")
        driver.save_screenshot("final_error_debug.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    castrol_automation()
