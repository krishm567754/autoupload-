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
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # Increased wait to 30 seconds for reliability
    wait = WebDriverWait(driver, 30)

    try:
        print("🚀 Opening Castrol Portal...")
        driver.get("https://cildist.castroldms.com")

        USERNAME = os.getenv("SITE_USERNAME")
        PASSWORD = os.getenv("SITE_PASSWORD")

        # --- LOGIN BLOCK ---
        print(f"🔑 Entering credentials for: {USERNAME}")
        
        # Wait for UserId field
        user_field = wait.until(EC.presence_of_element_located((By.NAME, "UserId")))
        user_field.clear()
        user_field.send_keys(USERNAME)
        
        # Find Password field
        pass_field = driver.find_element(By.NAME, "Password")
        pass_field.clear()
        pass_field.send_keys(PASSWORD)
        
        # FIXED: Find button by Type and Class instead of ID
        print("🖱️ Clicking Login Button...")
        login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        login_btn.click()

        # --- SESSION CONFLICT BLOCK ---
        time.sleep(5) 
        if "already logged in" in driver.page_source.lower():
            print("⚠️ Session conflict detected! Clicking Logout...")
            try:
                # Looking for button containing 'Logout' text
                logout_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Logout')]")))
                logout_btn.click()
                time.sleep(3)
                
                # Re-login after force logout
                wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
                driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            except Exception as e:
                print(f"Bypass failed or not needed: {e}")

        # --- VERIFICATION & NAVIGATION ---
        # Wait for the sidebar or header that confirms we are inside
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "skin-blue")))
        print("🎊 Login Successful! Navigating to Report...")
        
        driver.get("https://cildist.castroldms.com/reports/sales/invoicedatatoexcel")
        
        # Wait for the report page to load a primary button
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-primary")))
        print("✅ Report page loaded successfully.")

    except Exception as e:
        print(f"❌ Automation Error: {e}")
        driver.save_screenshot("error_state.png")
        raise e 
    finally:
        driver.quit()

if __name__ == "__main__":
    castrol_automation()
