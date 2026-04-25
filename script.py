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
    # FTP Configuration based on your details
    FTP_HOST = "ftpupload.net"
    FTP_USER = "if0_40253796"
    FTP_PASS = "TL1pBn84f4JIXtI"
    REMOTE_FOLDER = "htdocs/sales_data"
    TARGET_FILENAME = "invoice.xlsx"

    print(f"☁️ Connecting to FTP: {FTP_HOST}...")
    try:
        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.encoding = "utf-8"
            
            # Navigate to the target folder
            print(f"📂 Navigating to {REMOTE_FOLDER}...")
            ftp.cwd(REMOTE_FOLDER)

            # Delete the previous file if it exists
            files_in_folder = ftp.nlst()
            if TARGET_FILENAME in files_in_folder:
                print(f"🗑️ Deleting existing {TARGET_FILENAME}...")
                ftp.delete(TARGET_FILENAME)

            # Upload the new file
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

    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": download_dir
    })

    wait = WebDriverWait(driver, 35)

    try:
        # --- LOGIN ---
        print("🚀 Opening Castrol Portal...")
        driver.get("https://cildist.castroldms.com")
        USERNAME = os.getenv("SITE_USERNAME")
        PASSWORD = os.getenv("SITE_PASSWORD")

        user_field = wait.until(EC.presence_of_element_located((By.NAME, "UserId")))
        user_field.send_keys(USERNAME)
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
        login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", login_btn)

        time.sleep(7)
        # Handle Session Conflict
        if "already logged in" in driver.page_source.lower():
            logout_btn = driver.find_elements(By.XPATH, "//button[contains(text(), 'Logout')]")
            if logout_btns:
                driver.execute_script("arguments[0].click();", logout_btns[0])
                time.sleep(5)
                driver.find_element(By.NAME, "UserId").send_keys(USERNAME)
                driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
                driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))

        # --- DOWNLOAD ---
        print("📂 Navigating to Export page...")
        driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")

        excel_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Save as Excel')]")))
        driver.execute_script("arguments[0].click();", excel_btn)
        
        print("⏳ Waiting for download (45s)...")
        time.sleep(45) 

        # --- PROCESS FILE ---
        files = [f for f in os.listdir(download_dir) if f.endswith('.xlsx')]
        if not files:
            raise Exception("❌ No Excel file found in downloads.")

        latest_file = max([os.path.join(download_dir, f) for f in files], key=os.path.getctime)
        # We don't need the date in the local filename anymore since it's becoming 'invoice.xlsx' on FTP
        final_local_path = os.path.join(download_dir, "invoice.xlsx")
        
        if os.path.exists(final_local_path):
            os.remove(final_local_path)
            
        os.rename(latest_file, final_local_path)
        print("✅ File renamed locally to invoice.xlsx")
        
        # --- UPLOAD ---
        upload_to_ftp(final_local_path)

    except Exception as e:
        print(f"❌ Error: {e}")
        driver.save_screenshot("final_error.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    castrol_automation()
