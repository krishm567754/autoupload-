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

    # CRITICAL: Fix for headless downloads
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": download_dir
    })

    wait = WebDriverWait(driver, 30)

    try:
        # --- LOGIN & NAVIGATION (Already Working) ---
        print("🚀 Opening Castrol Portal...")
        driver.get("https://cildist.castroldms.com")
        
        USERNAME = os.getenv("SITE_USERNAME")
        PASSWORD = os.getenv("SITE_PASSWORD")

        wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        time.sleep(5)
        # (Add your session conflict check here if needed)

        print("📂 Navigating to Sales Report...")
        driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")

        # --- STEP 1: LOAD DATA ---
        print("📊 Clicking 'Load Data'...")
        # Usually, this is a primary button on the report page
        load_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.btn-primary")))
        load_btn.click()
        
        # We must wait for the data to actually load into the grid
        print("⏳ Waiting for data to populate (15s)...")
        time.sleep(15) 

        # --- STEP 2: DOWNLOAD EXCEL ---
        print("💾 Exporting to Excel...")
        # Finding the Excel button - trying XPATH first as it's often an icon or text link
        excel_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Excel')] | //a[contains(@class, 'export')] | //button[contains(@class, 'btn-success')]")))
        excel_btn.click()
        
        # Give the file time to download
        print("📥 Downloading file...")
        time.sleep(10)

        # --- STEP 3: DETECT & RENAME ---
        files = os.listdir(download_dir)
        if not files:
            raise Exception("❌ Download failed: No file found in download folder.")
        
        # Get the most recent file
        latest_file = max([os.path.join(download_dir, f) for f in files], key=os.path.getctime)
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        new_filename = f"sales_{date_str}.xlsx"
        new_path = os.path.join(download_dir, new_filename)
        
        os.rename(latest_file, new_path)
        print(f"✅ Report saved and renamed: {new_filename}")
        
        # Return the path so we can use it for FTP upload next
        return new_path

    except Exception as e:
        print(f"❌ Automation Error: {e}")
        driver.save_screenshot("report_error.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    report_file = castrol_automation()
    if report_file:
        print(f"Ready to upload {report_file} to FTP.")
