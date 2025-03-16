from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument('--no-first-run')
chrome_options.add_argument("--disable-notifications")

service = Service("/usr/bin/chromedriver") 
driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get("https://www.google.com")
print("Title: ", driver.title)
try:
    print("In Try")
    reject_ggle_btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, f'//button[contains(@aria-label, "Avvisa alla")]'))
        
    )
    print("Done with try")
except Exception as e:
    with open("test_scroll_error.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("In except")
    reject_ggle_btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, f'//button[contains(@aria-label, "Reject all")]'))
        
    )
    print("Done with except")

reject_ggle_btn.click()
print("Shouldve Clicked reject btn")
driver.quit()
