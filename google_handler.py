import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import re

# Configure Selenium WebDriver (e.g., Chrome)
def setup_driver():

    # Install Chrome and ChromeDriver on the server (if not already installed)
    # if not os.path.exists("/usr/bin/google-chrome"):
    #     print("Installing Google Chrome...")
    #     os.system("wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -")
    #     os.system('echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list')
    #     os.system("sudo apt-get update -y")
    #     os.system("sudo apt-get install -y google-chrome-stable")

    # if not os.path.exists("/usr/local/bin/chromedriver"):
    #     print("Installing ChromeDriver...")
    #     os.system("sudo apt-get install -y unzip")  # Ensure unzip is installed
    #     os.system("wget -q https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip")  # Replace with the latest version
    #     os.system("unzip chromedriver_linux64.zip")
    #     os.system("sudo mv chromedriver /usr/local/bin/")
    #     os.system("sudo chmod +x /usr/local/bin/chromedriver")

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode (no GUI)
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-dev-shm-usage")  # Avoid memory issues
    options.add_argument("--lang=en")
    options.add_argument('--window-size=800,600')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-breakpad')
    options.add_argument('--disable-component-update')
    options.add_argument('--disable-domain-reliability')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-features=AudioServiceOutOfProcess')
    options.add_argument('--disable-hang-monitor')
    options.add_argument('--disable-ipc-flooding-protection')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-prompt-on-repost')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-default-apps')
    options.add_argument('--metrics-recording-only')
    options.add_argument('--no-first-run')
    options.add_argument('--safebrowsing-disable-auto-update')
    options.add_argument('--enable-automation')
    options.add_argument('--password-store=basic')
    options.add_argument('--use-mock-keychain')

    # Set up ChromeDriver service
    service = Service(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extract_coordinates(url):
    # Regex to match latitude and longitude in the URL
    pattern_1 = r"@(-?\d+\.\d+),(-?\d+\.\d+)"
    pattern_2 = r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)"
    match = re.search(pattern_1, url)
    if match:
        latitude = match.group(1)
        longitude = match.group(2)
        return latitude, longitude
    else:
        match = re.search(pattern_2, url)
        if match:
            latitude = match.group(1)
            longitude = match.group(2)
            return latitude, longitude
        return None, None



# Scroll to the bottom of the page to load more results


def scroll_to_bottom(driver):

    divSideBar = driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]')
    
    # Scroll multiple times
    last_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(100):

        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", divSideBar)
        
        # Random delay between 5 and 7 seconds
        time.sleep(random.uniform(5, 7))
        new_height = driver.execute_script("return arguments[0].scrollHeight;", divSideBar)
        if last_height == new_height:
            break
        
        last_height = new_height



# Scrape company information from the page
def scrape_company_info(driver, town):
    
    companies = []
    town = town.capitalize()

    company_parent = driver.find_element(By.XPATH,  '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]')
    company_parent_soup = BeautifulSoup(company_parent.get_attribute('outerHTML'), 'lxml')

    company_cards = company_parent_soup.find_all("a", {"aria-label": True})
    
    for company in company_cards:

        #open company card
        company_url = company.get("href")
        
        if "https://www.google.com/maps/place/" in company_url:
            print(f"GETTING: {company_url}")
            company_driver = setup_driver()
            company_driver.get(company_url)

            name_element = WebDriverWait(company_driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[1]/h1'))
            )
            name = name_element.text if name_element else None
            
            category_element = WebDriverWait(company_driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[2]/span/span/button'))
            )
            category = category_element.text if category_element else None

            info_card = company_driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[7]')
            info_card_soup = BeautifulSoup(info_card.get_attribute('outerHTML'), 'lxml')
            print(f"\ninfo_card_soup: {info_card_soup}\n")
            

            try:
                #try with soup
                address = info_card_soup.find(
                    "button", 
                    attrs={"aria-label": lambda x: x and "Address:" in x}
                )

                if address:
                    address = address.get("aria-label")
                    address = address.replace("Address: ", "").replace(f", {town}", "").strip()
                else:
                    address = info_card_soup.find(
                        "button", 
                        attrs={"aria-label": lambda x: x and "Adresse:" in x}
                    )
                    if address:
                        address = address.get("aria-label")
                        address = address.replace("Adresse: ", "").replace(f", {town}", "").strip()
                    else:
                        address = None
            except:
                address = None
            
            try:
                website = info_card_soup.find(
                    "a", 
                    attrs={"aria-label": lambda x: x and "Website:" in x}
                )
                if website:
                    website = website.get("href")
                else:
                    website = info_card_soup.find(
                        "a", 
                        attrs={"aria-label": lambda x: x and "Site Web:" in x}
                    )
                    if website:
                        website = website.get("href")
                    else:
                        website =None
            except:
                website = None

            try:
                phone = info_card_soup.find(
                    "button", 
                    attrs={"aria-label": lambda x: x and "Phone:" in x}
                )
                
                if phone:
                    phone = phone.get("aria-label")
                    phone = phone.replace("Phone: ", "").strip()
                else:
                    phone = info_card_soup.find(
                        "button", 
                        attrs={"aria-label": lambda x: x and "Numéro de téléphone:" in x}
                    )
                    if phone:
                        phone = phone.get("aria-label")
                        phone = phone.replace("Numéro de téléphone: ", "").strip()
                    else:
                        phone = None
                
            except:
                phone =  None

            latitude, longitude = extract_coordinates(company_url)

            company_info=  {
                'name': name,
                'address': address,
                'contact_numbers': [phone],
                'website': website,
                'size': "",
                'tags': "",
                'description': category,
                'latitude': latitude,
                'longitude': longitude
            }
            company_driver.quit()
            companies.append(company_info)
            
            time.sleep(random.uniform(3, 5))
        
        
    return companies

# Main function
def initiator(search_query, town):
    # search_query = "companies in yaounde"
    url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"

    driver = setup_driver()
    driver.get(url)

    # Wait for the page to load
    time.sleep(5)

    # Scroll to load all results
    scroll_to_bottom(driver)

    # Scrape company information
    companies = scrape_company_info(driver, town)    
    
    # Close the driver
    driver.quit()

    return companies
