import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def castrol_login():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # This automatically downloads the correct driver for the runner's Chrome version
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    wait = WebDriverWait(driver, 20)

    try:
        print("🚀 Navigating to Castrol Portal...")
        driver.get("https://cildist.castroldms.com")

        USERNAME = os.getenv("SITE_USERNAME")
        PASSWORD = os.getenv("SITE_PASSWORD")

        if not USERNAME or not PASSWORD:
            print("❌ Error: Credentials missing in GitHub Secrets.")
            return None

        print(f"🔑 Attempting login for: {USERNAME}")
        wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
        driver.find_element(By.ID, "btn-login").click()

        # Handle Session Conflict
        time.sleep(5) 
        if "already logged in" in driver.page_source.lower():
            print("⚠️ Session conflict! Forcing logout...")
            try:
                logout_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Logout')]")
                logout_btn.click()
                time.sleep(2)
                # Re-login
                driver.find_element(By.NAME, "UserId").send_keys(USERNAME)
                driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
                driver.find_element(By.ID, "btn-login").click()
            except Exception as e:
                print(f"Could not bypass popup: {e}")

        # Verification
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "main-header")))
        print("🎊 Success! Dashboard reached.")
        return driver

    except Exception as e:
        print(f"❌ Failed: {e}")
        driver.save_screenshot("login_error.png")
        raise e # Tells GitHub Actions the job failed
    finally:
        driver.quit()

if __name__ == "__main__":
    castrol_login()        
        # Using the specific field names you provided: UserId and Password
        wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
        driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
        
        # Locate and click the login button (usually ID 'btn-login')
        driver.find_element(By.ID, "btn-login").click()

        # 4. Handle Session Conflict Popup
        # We wait a few seconds to see if the "Already Logged In" message appears
        time.sleep(5) 
        
        try:
            # Look for the 'Logout' button in the popup
            # Using XPATH to find a button that contains the text 'Logout'
            conflict_btn = driver.find_elements(By.XPATH, "//button[contains(text(), 'Logout')]")
            
            if conflict_btn:
                print("⚠️ Session conflict detected! Clicking 'Logout' to force session...")
                conflict_btn[0].click()
                
                # After clicking logout, we usually need to re-enter credentials or it auto-submits
                time.sleep(2)
                print("🔄 Re-attempting login after forcing logout...")
                wait.until(EC.presence_of_element_located((By.NAME, "UserId"))).send_keys(USERNAME)
                driver.find_element(By.NAME, "Password").send_keys(PASSWORD)
                driver.find_element(By.ID, "btn-login").click()
        except Exception:
            print("✅ No session conflict popup detected.")

        # 5. Verify Successful Login
        # We check for an element that only exists on the dashboard (like the main-header)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "main-header")))
        print("🎊 Login Successful! We are now on the Dashboard.")
        
        return driver

    except Exception as e:
        print(f"❌ Login Failed: {e}")
        driver.save_screenshot("login_error.png") # Helpful for debugging in GitHub Actions
        driver.quit()
        return None

if __name__ == "__main__":
    # For local testing, you can set these manually in your terminal:
    # export SITE_USERNAME='your_user'
    # export SITE_PASSWORD='your_password'
    browser_session = castrol_login()
    
    if browser_session:
        print("Ready for next step: Navigation to Report.")
        # browser_session.quit() # Keep it open if you're chaining steps
