from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# Base URL and login endpoint
base_url = "https://apps.nottingham.edu.my"

# Set up Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")  # Optional: Run in headless mode
chrome_options.add_argument("--disable-gpu")
service = Service("C:/Users/PC 5/Desktop/Year 3/chromedriver-win64/chromedriver.exe")  # Replace with your ChromeDriver path

driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Step 1: Open the login page
    driver.get(f"{base_url}/jw/web/login")
    time.sleep(2)  # Wait for the page to load

    # Step 2: Fetch the CSRF token
    csrf_token_element = driver.find_element(By.NAME, "OWASP_CSRFTOKEN")
    csrf_token = csrf_token_element.get_attribute("value")
    print(f"CSRF token found: {csrf_token}")

    # Step 3: Enter login credentials
    driver.find_element(By.ID, "j_username").send_keys("hcyyc7")  # Replace with actual username
    driver.find_element(By.ID, "j_password").send_keys("CyC399339!")  # Replace with actual password

    # Step 4: Click the login button
    login_button = driver.find_element(By.CSS_SELECTOR, "input[name='submit']")
    login_button.click()

    time.sleep(3)  # Wait for the page to load after login

    # Step 5: Check if login was successful
    current_url = driver.current_url
    print(f"Current URL after login: {current_url}")

    # Debug: Capture page source
    print(driver.page_source[:500])  # Print the first 500 characters of the page source

    if "dashboard" in current_url or "home" in current_url:
        print("Login successful!")
    else:
        print("Login failed. Check credentials or CSRF handling.")

finally:
    driver.quit()
    
    
    
    
    
    
    
# <a href="/jw/web/userview/booking/v/_/request" class="menu-link default"><span>New Booking</span></a>       new gym booking
# https://apps.nottingham.edu.my/jw/web/userview/sport_booking/sport_complex_homepage/_/sport_complex    sports complex
#  <a class="app-link" target="_blank" href="/jw/web/userview/booking/v"> <span class="userview-icon" style="background-image:url('/jw/web/app/sport_booking/resources/swim.png')"></span>   gym and swimming

