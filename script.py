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
        print("🚀 Opening Castrol Portal...")
        driver.get("https://cildist.castroldms.com")

        USERNAME = os.getenv("SITE_USERNAME")
        PASSWORD = os.getenv("SITE_PASSWORD")

        # --- LOGIN ---
        print(f"🔑 Logging in as: {USERNAME}")
        wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
        
        # Click login button (the green one from your video)
        login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        login_btn.click()

        # Wait for dashboard to load
        time.sleep(5)
        
        # --- NAVIGATION ---
        print("📂 Navigating to Sales Report URL...")
        driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")

        # --- DOWNLOAD LOGIC (Updated via Video) ---
        print("💾 Clicking 'Save as Excel'...")
        # In your video, the button has the class 'btn-success' and is green
        excel_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-success")))
        excel_btn.click()
        
        # In your video, it says 'Loading...' after clicking. 
        # We wait for the loading spinner to disappear and the file to start downloading.
        print("⏳ Processing report... (Waiting 20s for download to start)")
        time.sleep(20) 

        # --- FILE HANDLING ---
        print("📥 Checking downloads folder...")
        files = os.listdir(download_dir)
        
        # Retry loop to wait for file to appear
        for i in range(10):
            if any(f.endswith('.xlsx') for f in os.listdir(download_dir)):
                break
            time.sleep(2)
            files = os.listdir(download_dir)

        if not files:
            # Take a screenshot if it fails here so we can see the 'Loading' state
            driver.save_screenshot("download_fail_screen.png")
            raise Exception("❌ File never arrived in downloads folder.")
        
        latest_file = max([os.path.join(download_dir, f) for f in files], key=os.path.getctime)
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        new_filename = f"sales_{date_str}.xlsx"
        new_path = os.path.join(download_dir, new_filename)
        
        os.rename(latest_file, new_path)
        print(f"✅ SUCCESS: Saved as {new_filename}")
        
        return new_path

    except Exception as e:
        print(f"❌ Automation Error: {e}")
        driver.save_screenshot("last_error.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    report_file = castrol_automation()
