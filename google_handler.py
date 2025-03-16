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
    options.add_argument("--disable-notifications")
    options.add_argument('--safebrowsing-disable-auto-update')
    options.add_argument('--enable-automation')
    options.add_argument('--password-store=basic')
    options.add_argument('--use-mock-keychain')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.88 Safari/537.36")

    # options.add_argument('--enable-unsafe-swiftshader')"
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')
    """
    
    print("[INFO] Starting ChromeDriver...")

    # Set up ChromeDriver service
    service = Service(executable_path="/usr/bin/chromedriver", log_output="selenium.log")
    driver = webdriver.Chrome(service=service, options=options)
    print("[INFO] ChromeDriver started successfully!")
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


def scroll_to_bottom(driver, city):

    try:
        print("[INFO] In scroll_to_bottom")
        # divSideBar = driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]')
        # divSideBar = driver.find_element(By.XPATH, f'//div[@aria-label="Results for companies in {city}"]')
        """
        try:
            try:
                reject_ggle_btn = WebDriverWait(driver, 7).until(
                    EC.element_to_be_clickable((By.XPATH, f'//button[contains(@aria-label, "Avvisa alla")]'))
                    
                )
            except Exception as e:
                reject_ggle_btn = WebDriverWait(driver, 7).until(
                    EC.element_to_be_clickable((By.XPATH, f'//button[contains(@aria-label, "Reject all")]'))
                    
                )
            
            reject_ggle_btn.click()
            print("Clicked reject btn")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@role, "feed")]'))
            )
        except Exception as e:
            pass
        """
        
        divSideBar = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((
                By.XPATH, 
                f'//div[contains(@role, "feed")]'
        )))
        print(f"divSideBar gotten")
        
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
    except Exception as e:
        print(f"Scrolling failed: {e}")
        # Dump HTML for debugging
        with open("scroll_error.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)



# Scrape company information from the page
def scrape_company_info(driver, city):

    companies = []
    city = city.capitalize()
    try:
        # company_parent = driver.find_element(By.XPATH,  '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]')
        # company_parent_child = driver.find_element(By.XPATH, f'//div[contains(@aria-label, "Results for companies in {city}")]')
        
        company_parent_child = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((
                By.XPATH, 
                f'//div[contains(@role, "feed")]'
            )))
        company_parent = company_parent_child.find_element(By.XPATH, './parent::div')
        company_parent_soup = BeautifulSoup(company_parent.get_attribute('outerHTML'), 'lxml')

        company_cards = company_parent_soup.find_all("a", {"aria-label": True})
        
        for company in company_cards:

            #open company card
            company_url = company.get("href")
            
            if "https://www.google.com/maps/place/" in company_url:
                print(f"GETTING: {company_url}")
                company_driver = setup_driver()
                company_driver.get(company_url)

                # name_element = WebDriverWait(company_driver, 10).until(
                #     EC.presence_of_element_located((By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[1]/h1'))
                # )
                name_element = WebDriverWait(company_driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f'//div[contains(@role, "main")]/div[2]/div/div[1]/div[1]/h1'))
                )
                name = name_element.text if name_element else None
                
                # category_element = WebDriverWait(company_driver, 10).until(
                #     EC.presence_of_element_located((By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[2]/span/span/button'))
                # )
                category_element = WebDriverWait(company_driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f'//div[contains(@role, "main")]/div[2]/div/div[1]/div[2]/div/div[2]/span/span/button'))
                )
                category = category_element.text if category_element else None

                # info_card = company_driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[7]')
                info_card = company_driver.find_element(By.XPATH, '//div[contains(@role, "main")]/div[7]')
                info_card_soup = BeautifulSoup(info_card.get_attribute('outerHTML'), 'lxml')
                # print(f"\ninfo_card_soup: {info_card_soup}\n")
                

                try:
                    #try with soup
                    address = info_card_soup.find(
                        "button", 
                        attrs={"aria-label": lambda x: x and "Address:" in x}
                    )

                    if address:
                        address = address.get("aria-label")
                        address = address.replace("Address: ", "").replace(f", {city}", "").strip()
                    else:
                        address = info_card_soup.find(
                            "button", 
                            attrs={"aria-label": lambda x: x and "Adresse:" in x}
                        )
                        if address:
                            address = address.get("aria-label")
                            address = address.replace("Adresse: ", "").replace(f", {city}", "").strip()
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
                print(company_info)
                print(f"\n PRINTED company_info \n")
    except:
        pass    
        
    return companies

# Main function
def initiator(search_query, city):
    # search_query = "companies in yaounde"
    url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"

    driver = setup_driver()
    print("Gotten Initiator driver")
    driver.get(url)
    print("[INFO] URL gotten")
    # Wait for the page to load
    time.sleep(5)

    # Scroll to load all results
    print("[INFO] Starting Scroll to Button Func...")
    scroll_to_bottom(driver, city)

    # Scrape company information
    print("[INFO] Starting Company Scraper...")
    companies = scrape_company_info(driver, city)    
    
    # Close the driver
    driver.quit()

    return companies
