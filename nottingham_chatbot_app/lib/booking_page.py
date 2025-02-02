from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys

# Retrieve arguments from FastAPI request
username, password, venue, contact_no, purpose, date, session = sys.argv[1:]

# Base URL
base_url = "https://apps.nottingham.edu.my"

# Set up Selenium WebDriver
chrome_options = Options()
# Uncomment below line to run in headless mode
# chrome_options.add_argument("--headless")  # Optional: Run in headless mode
chrome_options.add_argument("--disable-gpu")
service = Service("C:/Users/PC 5/Desktop/Year 3/chromedriver-win64/chromedriver-win64/chromedriver.exe")  # Replace with your ChromeDriver path

driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Step 1: Open the login page
    driver.get(f"{base_url}/jw/web/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "OWASP_CSRFTOKEN")))

    # Step 2: Enter login credentials
    driver.find_element(By.ID, "j_username").send_keys(username)  # Replace with actual username
    driver.find_element(By.ID, "j_password").send_keys(password)  # Replace with actual password

    # Step 3: Click the login button
    login_button = driver.find_element(By.CSS_SELECTOR, "input[name='submit']")
    login_button.click()

    # Step 4: Wait for post-login page to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "app-link")))

    # Step 5: Open the New Booking page directly
    new_booking_page_url = f"{base_url}/jw/web/userview/booking/v/_/request"
    driver.get(new_booking_page_url)

    # Step 6: Verify access to the New Booking page
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    current_url = driver.current_url
    print(f"Current URL: {current_url}")

    if "request" in current_url:
        print("Successfully accessed the New Booking page!")

        # Step 7: Ensure the page is fully loaded before selecting the gym option
        time.sleep(2)  # Allow additional time for elements to be interactive

        # Step 8: Select Gymnasium option using JavaScript click
        venue_radio_button = driver.find_element(By.CSS_SELECTOR, "input[id='venue'][value='{venue}']")
        driver.execute_script("arguments[0].click();", venue_radio_button)
        print("Gymnasium selected!")
        
        # Step 9: Click the Next button to proceed
        next_button = driver.find_element(By.ID, "assignmentComplete")
        driver.execute_script("arguments[0].click();", next_button)
        print("Next button clicked, proceeding to the next form.")
        
        # Step 10: Fill out additional fields
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "contact_no")))
        driver.find_element(By.ID, "contact_no").send_keys(contact_no)
        print("Contact number entered.")
        
        driver.find_element(By.ID, "purpose").send_keys(purpose)
        print("Purpose entered.")
        
        # Step 11: Select Booking Date from Calendar
        date_picker = driver.find_element(By.ID, "booking_date__1665888614947936754611897066452")
        driver.execute_script("arguments[0].removeAttribute('readonly')", date_picker)  # Remove readonly attribute
        date_picker.clear()
        date_picker.send_keys(date)  # Replace with desired date
        print("Booking date selected!")
        
        # Step 12: Select Session (9:00 - 10:00)
        session_radio_button = driver.find_element(By.CSS_SELECTOR, "input[id='session'][value='{session}']")
        driver.execute_script("arguments[0].click();", session_radio_button)
        print("Session selected!")
        
        # Step 13: Confirm booking details by clicking the complete button
        complete_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'][value='Complete']")))
        driver.execute_script("arguments[0].click();", complete_button)
        print("Booking completed! Waiting for page to load...")
        
        # Step 14: Wait for the page to load completely after booking
        time.sleep(7)  # Adjust sleep time if necessary to ensure booking is processed
        print("Booking process completed successfully!")

    else:
        print("Failed to access the New Booking page.")


finally:
    driver.quit()




# gym button <input id="venue" name="venue" type="radio" value="45419910-a0000040-5b1ba29c-fcac248d">
# swimming pool <input id="venue" name="venue" type="radio" value="58e58998-a0000040-1455f332-fa3a484b">
# next button <input id="assignmentComplete" name="assignmentComplete" class="waves-button-input" type="submit" value="Next" style="background-color:rgba(0,0,0,0);">

# contact number field <input id="contact_no" name="contact_no" class="textfield__166588861443415107021139876928" type="text" placeholder="" value="">
# purpose field <input id="purpose" name="purpose" class="textfield__166588861443415107021_220463842" type="text" placeholder="" value="">
# date field <input id="booking_date__1665888614947936754611897066452" name="booking_date" type="text" value="Tue, 28-January-2025 16:03" class="booking_date no-manual-input hasDatepicker" readonly="" placeholder="EEE, DD-MMMMM-YYYY">

# session 9-10 <input grouping="" id="session" name="session" type="radio" value="c6d16693-a0000040-615864a2-402fab7d">
# session 5-6 <input grouping="" id="session" name="session" type="radio" value="ee0108db-a0000040-6172fc20-ad779c80">

# complete button <input id="assignmentComplete" name="assignmentComplete" class="waves-button-input" type="submit" value="Complete" style="background-color:rgba(0,0,0,0);">