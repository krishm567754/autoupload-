import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def castrol_automation():
    # 1. Setup Chrome Options
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 25)

    try:
        print("🚀 Opening Castrol Portal...")
        driver.get("https://cildist.castroldms.com")

        USERNAME = os.getenv("SITE_USERNAME")
        PASSWORD = os.getenv("SITE_PASSWORD")

        # --- LOGIN BLOCK ---
        print(f"🔑 Entering credentials for: {USERNAME}")
        # Ensure these lines are aligned exactly with 8 spaces (2 indents)
        wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
        driver.find_element(By.ID, "btn-login").click()

        # --- SESSION CONFLICT BLOCK ---
        time.sleep(5) 
        if "already logged in" in driver.page_source.lower():
            print("⚠️ Session conflict detected! Clicking Logout...")
            try:
                logout_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Logout')]")
                logout_btn.click()
                time.sleep(2)
                # Re-login after force logout
                driver.find_element(By.NAME, "UserId").send_keys(USERNAME)
                driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
                driver.find_element(By.ID, "btn-login").click()
            except Exception as e:
                print(f"Bypass failed or not needed: {e}")

        # --- VERIFICATION & NAVIGATION ---
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "main-header")))
        print("🎊 Login Successful! Navigating to Report...")
        
        # Move to the specific sales report URL
        driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")
        
        # Wait for the 'Load Data' button to appear
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".btn.btn-primary")))
        print("✅ Report page loaded successfully.")

    except Exception as e:
        print(f"❌ Automation Error: {e}")
        driver.save_screenshot("error_state.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    castrol_automation()
