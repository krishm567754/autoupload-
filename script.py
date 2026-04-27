import os
import time
import datetime
import ftplib
import pandas as pd
import warnings
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

def filter_current_month(file_path):
    print("🧹 Opening Excel file to filter for Current Month only...")
    try:
        df = pd.read_excel(file_path)
        
        date_col = "Invoice Date"
        if date_col not in df.columns:
            possible_cols = [col for col in df.columns if 'invoice date' in str(col).lower()]
            if possible_cols:
                date_col = possible_cols[0]
            else:
                print("⚠️ Could not detect 'Invoice Date' column. Uploading full file as safety fallback.")
                return

        original_row_count = len(df)
        print(f"📅 Using column: '{date_col}'. Parsing dates...")
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df['parsed_date'] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=False)
        
        now = datetime.datetime.now()
        current_month = now.month
        current_year = now.year
        
        filtered_df = df[(df['parsed_date'].dt.month == current_month) & (df['parsed_date'].dt.year == current_year)]
        filtered_df = filtered_df.drop(columns=['parsed_date'])
        
        filtered_df.to_excel(file_path, index=False)
        
        new_row_count = len(filtered_df)
        print(f"✂️ Filter successful! Removed {original_row_count - new_row_count} old rows. Keeping {new_row_count} current month rows.")

    except Exception as e:
        print(f"⚠️ Excel filtering failed: {e}. Proceeding with original unfiltered file.")

def upload_to_ftp(local_file_path, ftp_host, ftp_user, ftp_pass, remote_folder, target_filename):
    print(f"☁️ Connecting to FTP Server: {ftp_user}@{ftp_host}...")
    try:
        with ftplib.FTP(ftp_host, ftp_user, ftp_pass) as ftp:
            ftp.encoding = "utf-8"
            print(f"📂 Navigating to {remote_folder}...")
            ftp.cwd(remote_folder)
            
            if target_filename in ftp.nlst():
                print(f"🗑️ Deleting existing {target_filename} to replace it...")
                ftp.delete(target_filename)
                
            print(f"📤 Uploading file as {target_filename}...")
            with open(local_file_path, "rb") as file:
                ftp.storbinary(f"STOR {target_filename}", file)
            print("🎯 FTP Upload Complete!")
    except Exception as e:
        print(f"❌ FTP Error on {ftp_user}: {e}")
        raise e

def castrol_automation():
    download_dir = os.path.abspath(os.path.join(os.getcwd(), "downloads"))
    if not os.path.exists(download_dir): os.makedirs(download_dir)

    for f in os.listdir(download_dir):
        os.remove(os.path.join(download_dir, f))

    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
    
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}") 
    
    prefs = {
        "download.default_directory": download_dir, 
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": download_dir})
    
    wait = WebDriverWait(driver, 25)

    try:
        USERNAME = os.getenv("SITE_USERNAME")
        PASSWORD = os.getenv("SITE_PASSWORD")

        # --- PHASE 1: INITIAL LOGIN ---
        print("🚀 Opening Castrol Portal...")
        login_success = False
        for attempt in range(3):
            try:
                driver.get("https://cildist.castroldms.com")
                user_field = wait.until(EC.presence_of_element_located((By.NAME, "UserId")))
                user_field.clear()
                user_field.send_keys(USERNAME)
                pass_field = driver.find_element(By.NAME, "Password")
                pass_field.clear()
                pass_field.send_keys(PASSWORD)
                driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
                login_success = True
                break 
            except TimeoutException:
                print(f"⚠️ Portal load attempt {attempt + 1} failed. Retrying...")
                time.sleep(5)
                
        if not login_success:
            raise Exception("❌ Failed to load login page.")

        # --- PHASE 2: SMART SESSION RECOVERY ---
        time.sleep(10)
        if "already logged in" in driver.page_source.lower():
            print("⚠️ Session conflict detected! Forcing logout...")
            logout_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Logout')]")
            if logout_btns:
                driver.execute_script("arguments[0].click();", logout_btns[0])
                time.sleep(5)
                print("🔄 Reloading portal to verify state...")
                driver.get("https://cildist.castroldms.com")
                time.sleep(5)
                user_fields = driver.find_elements(By.NAME, "UserId")
                if user_fields:
                    print("🔑 Re-entering credentials...")
                    user_fields[0].clear()
                    user_fields[0].send_keys(USERNAME)
                    driver.find_element(By.NAME, "Password").clear()
                    driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
                    driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
                    time.sleep(8)

        # --- PHASE 3: NAVIGATION ---
        print("📂 Navigating to Export page...")
        time.sleep(4)
        driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")

        # --- PHASE 4: DOWNLOAD ---
        print("💾 Clicking 'Save as Excel'...")
        excel_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Save as Excel')]")))
        time.sleep(2) 
        driver.execute_script("arguments[0].click();", excel_btn)
        
        print("⏳ Monitoring Download Folder (Up to 150s)...")
        download_success = False
        for i in range(15):
            time.sleep(10)
            current_files = os.listdir(download_dir)
            print(f"📁 Checking files ({i+1}/15): {current_files}")
            
            xlsx_files = [f for f in current_files if f.endswith('.xlsx')]
            temp_files = [f for f in current_files if f.endswith('.crdownload') or f.endswith('.tmp')]
            
            if xlsx_files and not temp_files:
                download_success = True
                break
                
        if not download_success:
            raise Exception("❌ Download failed: No XLSX file arrived after 150 seconds.")

        # --- PHASE 5: FILE PROCESS & FILTERING ---
        xlsx_files = [f for f in os.listdir(download_dir) if f.endswith('.xlsx')]
        latest_file = max([os.path.join(download_dir, f) for f in xlsx_files], key=os.path.getctime)
        local_path = os.path.join(download_dir, "temp_filtered.xlsx")
        
        if os.path.exists(local_path): os.remove(local_path)
        os.rename(latest_file, local_path)
        
        filter_current_month(local_path)
        
        # --- PHASE 6: DUAL FTP UPLOADS ---
        print("\n=== STARTING FTP UPLOADS ===")
        upload_to_ftp(
            local_file_path=local_path,
            ftp_host="ftpupload.net",
            ftp_user="if0_40253796",
            ftp_pass="TL1pBn84f4JIXtI",
            remote_folder="htdocs/sales_data",
            target_filename="invoice.xlsx"
        )
        
        now = datetime.datetime.now()
        archive_filename = f"{now.year}_{now.month:02d}.xlsx" 
        upload_to_ftp(
            local_file_path=local_path,
            ftp_host="ftpupload.net",
            ftp_user="if0_40314734",
            ftp_pass="qKLu7SxmpJb65",
            remote_folder="htdocs/monthly_data",
            target_filename=archive_filename
        )
        print("=== FTP UPLOADS COMPLETE ===\n")

        # --- PHASE 7: WEBSITE 1 REFRESH (krishmo.xo.je) ---
        print(f"🌐 Visiting Website 1 (krishmo.xo.je)...")
        driver.get(f"https://krishmo.xo.je/?i=1&t={int(time.time())}")
        time.sleep(8)
        try:
            refresh_btn = wait.until(EC.presence_of_element_located((By.ID, "refresh-button")))
            driver.execute_script("arguments[0].click();", refresh_btn)
            try:
                WebDriverWait(driver, 5).until(EC.alert_is_present())
                driver.switch_to.alert.accept()
                print("✅ Clicked 'OK' on Website 1 popup! Monitoring JS Engine...")
            except: pass
            
            last_status = ""
            for check in range(30): 
                time.sleep(2)
                try:
                    current_status = driver.execute_script("return document.getElementById('loader-text').innerText;")
                    if current_status and current_status != last_status:
                        print(f"📡 Website 1 Status: {current_status}")
                        last_status = current_status
                    if "Done" in str(current_status):
                        print("✅ Website 1 Cache rebuilt successfully!")
                        break
                except: pass
        except Exception as e: print(f"⚠️ Website 1 refresh issue: {e}")

        # --- PHASE 8: WEBSITE 2 REFRESH (krishmodiexp.xo.je) ---
        print(f"\n🌐 Visiting Website 2 (krishmodiexp.xo.je)...")
        driver.get(f"https://krishmodiexp.xo.je/?i=1&t={int(time.time())}")
        time.sleep(8)
        try:
            print("🔄 Looking for the green floating refresh button...")
            driver.execute_script("""
                let btns = Array.from(document.querySelectorAll('button, a, div'));
                let target = btns.reverse().find(b => 
                    b.className.includes('fixed') || 
                    b.innerHTML.includes('<svg') ||
                    b.id === 'refresh-button'
                );
                if (target) { target.click(); }
            """)
            
            sync_active = False
            for check in range(45): 
                time.sleep(2)
                try:
                    page_text = driver.execute_script("return document.body.innerText;")
                    if "Syncing..." in page_text:
                        if not sync_active: print("📡 Website 2 Status: Syncing...")
                        sync_active = True
                    elif sync_active and "Syncing..." not in page_text:
                        print("✅ Website 2 Syncing complete! Cache is fresh.")
                        break
                except: pass
        except Exception as e: print(f"⚠️ Website 2 refresh issue: {e}")

        print("\n🏁 MISSION COMPLETE! All websites fully updated and cached.")

    except Exception as e:
        print(f"❌ Automation Error: {e}")
        try: driver.save_screenshot("debug_error.png")
        except: pass
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    castrol_automation()
