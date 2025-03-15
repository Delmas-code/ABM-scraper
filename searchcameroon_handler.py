import os
import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from main import BLFlowHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up Selenium options (headless mode)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Path to your chromedriver executable
driver_path = 'C:/Users/User/Desktop/Ongoing Project/Instanvi/repo/ABM-scraper/chromedriver/chromedriver.exe'


# URL to start with
# start_url = "https://searchcameroon.com/location/yaounde-g73-2/?v=820eb5b696ea"
start_urls = ["https://searchcameroon.com/location/douala/?v=820eb5b696ea", "https://searchcameroon.com/location/yaounde-g73-2/?v=820eb5b696ea"]


# Function to extract company links from a listing page
def get_company_links(page_source):
    soup = BeautifulSoup(page_source, "html.parser")
    links = []
    
    content_girds = soup.find('div', id="content-grids")
    company_cards = content_girds.find_all('div', class_= "card1")
    for company in company_cards:
        company_link = company.find("a")
        company_link= company_link.get('href')
        if company_link:
            links.append(company_link)
    
    logger.info(f"Found {len(links)} company links on the page")
    return links

# Function to extract company details from a detail page
def get_company_details(driver, company_list, files_dir, scrapped_companies, page_number):
    # Wait until the key element is loaded (adjust the selector as needed)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )
    except Exception as e:
        logger.error("Timed out waiting for company details to load.")
        return None

    # soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # You may need to adjust these selectors based on the actual page structure:
    try:
        name_section = driver.find_element(By.XPATH, '//*[@id="page"]/section/div[1]/div/div/div[1]')
        name_soup = BeautifulSoup(name_section.get_attribute('outerHTML'), 'lxml')
        name = name_soup.find("h1").text
    except Exception:
        name = ""

    if str(name).lower() not in company_list:
        try:
            details = driver.find_element(By.CLASS_NAME, "post-detail-content")
            details_soup = BeautifulSoup(details.get_attribute('outerHTML'), 'lxml')
            p_tags = details_soup.find_all("p")
            ul_tags = details_soup.find_all("ul")
            ol_tags = details_soup.find_all("ol")
            p2 = p_tags[1].text if len(p_tags) > 3 else None

            if len(p_tags) == 6 and p2:
                if "coming soon!" in str(p2).lower() or "BIENTÔT DISPONIBLE!" in str(p2).upper() or "ARRIVE BIENTÔT!" in str(p2).upper():
                    description = p_tags[0].text
                else:
                    description =  ""
                    for p_tag in p_tags:
                        description += f" //{p_tag.text}"
                    if len(ul_tags) > 0:
                        for ul_tag in ul_tags:
                            description += f" //{ul_tag.text}"
                    if len(ol_tags) > 0:
                        for ol_tag in ol_tags:
                            description += f" //{ol_tag.text}"

        except Exception as e:
            description = ""
        
        try:
            "lp-details-address"
            infos = driver.find_element(By.CLASS_NAME, "listing-detail-infos")
            infos_soup = BeautifulSoup(infos.get_attribute('outerHTML'), 'lxml')
            address = infos_soup.find("li", "lp-details-address")
            phone = infos_soup.find("li", "lp-listing-phone-whatsapp")

            address = address.text if address else ""
            phone = phone.text if phone else ""
            
        except Exception as e:
            address = ""
            phone = ""


        company_data = {
            "name": name,
            "address": address,
            "contact_numbers": [phone],
            "description": description,
            "website": "",
            "latitude": "",
            "longitude": "",
            "size": "",
            "tags": ""
        }
        name = str(name).lower()
        scrapped_companies[name] = f"from page {page_number}"
        file_path = os.path.join(files_dir, "scrapped_companies.json")
        with open(file_path, 'w') as f:
            json.dump(scrapped_companies, f, indent=4)

        logger.info(f"Scraped company: {name}")
        return True, company_data
    else:
        logger.info(f"Already Scraped: {name}")
        return False, {}



def get_total_pages(driver):
    try:
        pagination = driver.find_element(By.CSS_SELECTOR, "div.lp-pagination")
        # details_soup = BeautifulSoup(pagination.get_attribute('outerHTML'), 'lxml')
        # print(f"{details_soup} \n")
        pages = pagination.find_elements(By.CSS_SELECTOR, "span.haspaglink[data-pageurl]")
        return max(int(page.get_attribute("data-pageurl")) for page in pages)
    except NoSuchElementException:
        return 1
  

def click_next_page(driver, curr_page=1):
    """
    This function finds the pagination container (the <ul> element),
    locates the current page (span with class 'current'),
    and clicks on the next clickable page (span with attribute data-pageurl).
    Returns True if a next page was found and clicked, or False if the current page is the last one.
    """
    try:
        # Wait for the pagination ul element to be present and clickable
        # print(f"{driver.page_source}\n\n")
        pagination_page = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'page-numbers haspaglink'))
            
        )
        pagination_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'lp-pagination'))
            
        )
        
    except Exception as e:
        print("Pagination element not found:", e)
        return False

    # Get all the <span> elements within the ul (each representing a page)
    spans = pagination_div.find_elements(By.TAG_NAME, "span")
    for idx, span in enumerate(spans):
        if idx == curr_page:
            span.click()
            time.sleep(3)
            return True
        
    return False
    

def main():
    service = Service(executable_path='C:/Users/User/Desktop/Ongoing Project/Instanvi/repo/ABM-scraper/chromedriver/chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    all_companies = []
    page_number = 1

    current_dir = os.path.dirname(os.path.abspath(__file__))
    files_dir = os.path.join(current_dir, "files")
    file_path = os.path.join(files_dir, "scrapped_companies.json")

    if os.path.exists(file_path):
        with open(file_path) as f:
            companies = json.load(f)

    states_file_path = os.path.join(files_dir, "city_state.json")
    with open(states_file_path) as f:
        states = json.load(f)

    base_url = os.environ["BL_BASE_URL"]
    handler = BLFlowHandler(base_url=base_url)

    for idx, start_url in enumerate(start_urls):
        # start_url = "https://searchcameroon.com/location/yaounde-g73-2/?v=820eb5b696ea"
        driver.get(start_url)
        

        city = "Douala" if idx == 0 else "Yaounde"
        while True:
            logger.info(f"Processing page {page_number}")
            # Wait for page to load (adjust the wait condition to something that is reliably present)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "content-grids"))
                )
            except Exception as e:
                logger.error("Timeout waiting for company links to load.")
                break

            company_names = list(companies.keys())

            # Get company links from the current page
            company_links = get_company_links(driver.page_source)

            # Process each company detail page
            for link in company_links:
                try:
                    
                    # Open the company detail in the same window
                    driver.get(link)
                    
                    # Optionally wait a bit for the page to load
                    time.sleep(2)
                    
                    status, company_data = get_company_details(driver, company_names, files_dir, companies, page_number)
                    if status and company_data:
                        # all_companies.append(company_data)
                        # print(f"{company_data}\n")
                        
                        updated_company_data = handler._organise_company_data(company_data, city, states)
                        status = handler.company_inserter.add_document(updated_company_data)
                        logger.info("Send company data to buffer")
                    # break
                except Exception as e:
                    logger.error(f"Error processing link {link}: {e}")
                    continue

            # Go back to the listing page.
            # In some cases, it might be more robust to re-navigate using the driver.get() with the URL.
            driver.get(start_url)
            total_pages = get_total_pages(driver)
            print(f"Total pages found: {total_pages}")
            # Click to go to the next page.
            try:
                # Wait until the pagination control is available.
                # Adjust the selector to match the "Next" button in the pagination area.
                # if not click_next_page(driver, page_number):
                #     continue
                page_number += 1

                # for page_number in range(1, total_pages + 1):
                if page_number > 1 and page_number <= total_pages:
                    try:
                        page_btn = WebDriverWait(driver, 20).until(
                            EC.element_to_be_clickable(
                                (By.CSS_SELECTOR, f"span.haspaglink[data-pageurl='{page_number}']"))
                            )
                        driver.execute_script("arguments[0].click();", page_btn)
                        time.sleep(5)  # Adjust based on network speed
                    except Exception as e:
                        print(f"Failed to navigate to page {page_number}: {str(e)}")
                        break
                print(f"Moving to page: {page_number}")

            except Exception as e:
                logger.info("No more pages found or unable to click next page. Exiting loop.")
                logger.error(e)
                continue

    driver.quit()

    # Output the scraped data
    for company in all_companies:
        print(company)

if __name__ == "__main__":
    main()
