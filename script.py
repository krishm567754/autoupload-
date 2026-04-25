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
    
    # Initialize Driver with Auto-Managed Chrome Driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # CRITICAL: Fix for headless downloads in GitHub Actions
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

        print(f"🔑 Entering credentials for: {USERNAME}")
        user_field = wait.until(EC.presence_of_element_located((By.NAME, "UserId")))
        user_field.clear()
        user_field.send_keys(USERNAME)
        
        pass_field = driver.find_element(By.NAME, "Password")
        pass_field.clear()
        pass_field.send_keys(PASSWORD)
        
        # Click the login button using the submit type
        login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        driver.execute_script("arguments[0].click();", login_btn)

        # --- PHASE 2: SESSION CONFLICT ---
        time.sleep(7)
        if "already logged in" in driver.page_source.lower():
            print("⚠️ Session conflict detected! Forcing logout...")
            try:
                logout_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Logout')]")
                driver.execute_script("arguments[0].click();", logout_btn)
                time.sleep(4)
                # Re-login
                wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
                driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
                driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
            except:
                print("Proceeding past conflict check...")

        # --- PHASE 3: NAVIGATION ---
        print("📂 Navigating to Invoice Export page...")
        # Give it a moment to ensure login redirect is fully done
        time.sleep(3)
        driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")

        # --- PHASE 4: DOWNLOAD (Based on your React Logs) ---
        print("💾 Locating 'Save as Excel' button...")
        # Using XPATH 'contains' to match "Save as Excel " exactly from your react logs
        excel_xpath = "//button[contains(., 'Save as Excel')]"
        excel_btn = wait.until(EC.presence_of_element_located((By.XPATH, excel_xpath)))
        
        print("🖱️ Clicking Download button via JS...")
        driver.execute_script("arguments[0].click();", excel_btn)
        
        # Wait for the "Loading..." spinner to finish (seen in video)
        print("⏳ Waiting for generation and download (45s)...")
        time.sleep(45) 

        # --- PHASE 5: FILE VERIFICATION ---
        files = os.listdir(download_dir)
        xlsx_files = [f for f in files if f.endswith('.xlsx')]

        if not xlsx_files:
            # Check again after a small extra buffer
            time.sleep(10)
            xlsx_files = [f for f in os.listdir(download_dir) if f.endswith('.xlsx')]

        if xlsx_files:
            # Sort by creation time to get the newest file
            latest_file = max([os.path.join(download_dir, f) for f in xlsx_files], key=os.path.getctime)
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            new_filename = f"sales_{date_str}.xlsx"
            new_path = os.path.join(download_dir, new_filename)
            
            os.rename(latest_file, new_path)
            print(f"✅ SUCCESS: File saved as {new_filename}")
            return new_path
        
        raise Exception("❌ File not found in downloads folder. Check debug screenshot.")

    except Exception as e:
        print(f"❌ Automation Error: {e}")
        driver.save_screenshot("debug_screenshot.png")
        # Save HTML so we can see the exact state of the buttons if it fails
        with open("debug_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    castrol_automation()
