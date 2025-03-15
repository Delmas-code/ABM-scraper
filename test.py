from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service("/usr/bin/chromedriver") 
driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get("https://www.google.com")
print("Title: ", driver.title)
driver.quit()
