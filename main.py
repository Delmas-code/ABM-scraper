import os
import requests
import json
from time import sleep
import random
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from collections import defaultdict, OrderedDict
import logging
from fake_useragent import UserAgent
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from database import MongoDataHandler
from classifier import IndustryClassifier

from google_handler import initiator

load_dotenv()

class EntityScraper:
    def __init__(self, base_delay=3, max_delay=10):
        """
        Initialize scraper with configurable delays and tracking
        
        Args:
            base_delay (int): Minimum delay between requests in seconds
            max_delay (int): Maximum delay between requests in seconds
        """
        self.session = requests.Session()
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.last_requests = defaultdict(datetime.now)
        self.ua = UserAgent()
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('EntityScraper')
        
        # Set default headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })

    def _get_domain(self, url):
        """Extract domain from URL"""
        return urlparse(url).netloc

    def _update_user_agent(self):
        """Rotate user agent"""
        self.session.headers['User-Agent'] = self.ua.random

    def _respect_robots(self, url):
        """
        Check robots.txt and respect crawl-delay
        Returns True if allowed, False if not
        """
        # Implementation would go here
        return True

    def get(self, url, **kwargs):
        """
        Make a GET request with built-in delays and rotating user agents
        """
        domain = self._get_domain(url)
        
        # Check time since last request to this domain
        time_since_last = datetime.now() - self.last_requests[domain]
        if time_since_last < timedelta(seconds=self.base_delay):
            sleep_time = self.base_delay - time_since_last.total_seconds()
            self.logger.info(f"Sleeping for {sleep_time:.2f}s to respect rate limits")
            sleep(sleep_time)
        
        # Add jitter to avoid detection
        jitter = random.uniform(0, self.max_delay - self.base_delay)
        sleep(jitter)
        
        # Update tracking
        self.last_requests[domain] = datetime.now()
        
        # Rotate user agent
        self._update_user_agent()
        
        try:
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            raise
    
    # def scrape_with_proxy(self, url, proxy):

    #     proxies = {
    #         'http': proxy,
    #         'https': proxy
    #     }
    #     return self.get(url, proxies=proxies)

class BLDataExtractor:
    def __init__(self, html_content, base_url, parser="html.parser"):
        self.html_soup = BeautifulSoup(html_content, parser)
        self.base_url = base_url

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.files_dir = os.path.join(self.current_dir, "files")
        if not os.path.exists(self.files_dir):
            self.logger.error(f"Files folder not found!")
            raise Exception("Files folder not found!")
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('BLDataExtractor')
        
    def extract_cities(self):
        try:
            section_w_cities = self.html_soup.find('section')
            content_w_cities = section_w_cities.find('div', class_="content")
            links =  content_w_cities.find_all('a', href= True)
            city_data = {}
            for link in links:
                city = link.contents[0].strip()
                city_url = f"{self.base_url}{link['href']}"
                city_data[city] = city_url

            #reordeering
            reordered_city_data = OrderedDict()
            if "Yaounde" in city_data:
                reordered_city_data["Yaounde"] = city_data["Yaounde"]
            if "Douala" in city_data:
                reordered_city_data["Douala"] = city_data["Douala"]
            if "Buea" in city_data:
                reordered_city_data["Buea"] = city_data["Buea"]
            if "Kumba" in city_data:
                reordered_city_data["Kumba"] = city_data["Kumba"]

            for key, value in city_data.items():
                if key not in ["Yaounde", "Douala", "Buea", "Kumba"]:
                    reordered_city_data[key] = value

            file_path = os.path.join(self.files_dir, "cities.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(reordered_city_data, f, indent=4)
                
            self.logger.info(f"City Data scrapped and stored successfully in cities.json!")
        except Exception as e:
            self.logger.error(f"Failed to get city info: {str(e)}")

    def extract_companies(self, city):

        try:
            company_links = []
            all_companies = self.html_soup.find_all("div", class_ = "company")
            for company in all_companies:
                link_tag = company.find("a", href=True)
                link = f"{self.base_url}{link_tag['href']}"
                company_links.append(link)

            next_page_scroller = self.html_soup.find("div", class_ = "scroller_with_ul")
            next_page_link = next_page_scroller.find('a', rel="next", href=True)
            next_page_link = f"{self.base_url}{next_page_link['href']}" if next_page_link else None

            return next_page_link, company_links
        
        except Exception as e:
            self.logger.error(f"Failed to get companies for {city}: {str(e)}")
    
    def extract_company_data(self):
        try:
            latitude, longitude, company_site_link = "", "", ""

            company_info = self.html_soup.find_all("div", class_ = "info")
            company_name = company_info[0].find("div", id="company_name")
            if company_name:
                company_name = company_name.text.strip()

                company_address = company_info[1].find("div", id="company_address")
                if company_address:
                    company_address = company_address.text

                company_geo_link = company_info[1].find('a', rel="noopener", href=True )
                if company_geo_link:
                    company_geo_link = company_geo_link["href"]
                    company_geo_link = company_geo_link.split("=")[1].split("&")[0].split(",")
                    latitude, longitude = company_geo_link[0], company_geo_link[1]

                contact_number_list = []
                mobile_number_list= []
                con_number = self.html_soup.find("div", class_="phone")
                if con_number:
                    con_number_list = con_number.find_all("a")
                    for number in con_number_list:
                        contact_number_list.append(number.text.strip())

                mobile_number_tag = self.html_soup.find("div", class_="phone")
                if mobile_number_tag:
                    mobile_number_tag = mobile_number_tag.find_next("div", class_="info")
                if mobile_number_tag:
                    label_text = mobile_number_tag.find("div", class_="label").text.strip().lower()
                else:
                    label_text = ""
                if label_text == "mobile phone":
                    _mobile_number_list = mobile_number_tag.find_all("a")
                    _mobile_number_list = [number.text.strip() for number in _mobile_number_list]
                    mobile_number_list = _mobile_number_list

                phone_numbers = contact_number_list
                for number in mobile_number_list:
                    phone_numbers.append(number) if number not in phone_numbers else phone_numbers

                company_site_tag = self.html_soup.find("div", class_ ="weblinks")
                if company_site_tag:
                    company_site_link = company_site_tag.find('a', rel="noopener", href=True )["href"]
                    company_site_link = company_site_link.split("=")[-1].replace("%2f", "/").replace("%2F", "/")

                company_description = self.html_soup.find("div", class_ ='desc')
                if company_description:
                    company_description = company_description.text.strip()
                    #remove special characters
                    chars_to_replace = ['\n', '\r', '\t', '\xa0', '\u200b']
                    for char in chars_to_replace:
                        company_description = company_description.replace(char, ' ')

                company_extra_info = self.html_soup.find("div", class_='extra_info')
                size = ""
                if company_extra_info:
                    company_extra_info = company_extra_info.find_all("div", class_="info")
                    for info in company_extra_info:
                        label_text = info.find("div", class_="label").text.strip()
                        if label_text.lower() == 'employees':
                            size = info.contents[1].strip()
                            break

                
                company_tags = self.html_soup.find("div", class_ ="tags")
                all_tags = []
                if company_tags:
                    company_tags_text_list = company_tags.find_all("a")
                    for company_tag in company_tags_text_list:
                        all_tags.append(company_tag.text)


                company_data = {
                    "name": company_name,
                    "address": company_address if company_address else "",
                    "size": size if size else "",
                    "website": company_site_link if company_site_link else "",
                    "description": company_description if company_description else "",
                    "latitude": latitude if latitude else "",
                    "longitude": longitude if longitude else "",
                    "contact_numbers": phone_numbers if phone_numbers else "",
                    "tags": all_tags if all_tags else ""
                }
                return company_data
            else:
                return None
        
        except Exception as e:
            self.logger.error(f"Error Getting Company Data: {str(e)}")
            
class BLFlowHandler:
    def __init__(self, base_url):
        self.base_url = base_url

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.files_dir = os.path.join(self.current_dir, "files")
        if not os.path.exists(self.files_dir):
            self.logger.error(f"Files folder not found!")
            raise Exception("Files folder not found!")

        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('BLFlowHandler')

        #configure for industry mapper
        self.industry_maps = IndustryClassifier()

        #configure connection for company bulk inserter
        self.company_inserter = MongoDataHandler(
            connection_string= os.environ["CONN_STRING"],
            database_name= os.environ["DB_NAME"],
            collection_name= os.environ["COMPANY_COLLECTION"],
            buffer_size=100,  # Will insert after 100 documents
            max_wait_time=300  # Or after 300 seconds, whichever comes first
        )

        #configure connection for inserting in location collection
        self.location_inserter = MongoDataHandler(
            connection_string= os.environ["CONN_STRING"],
            database_name= os.environ["DB_NAME"],
            collection_name= os.environ["LOCATION_COLLECTION"]
        )

        #configure connection for inserting in industry collection
        self.industry_inserter = MongoDataHandler(
            connection_string= os.environ["CONN_STRING"],
            database_name= os.environ["DB_NAME"],
            collection_name= os.environ["INDUSTRY_COLLECTION"]
        )

    def _scraper(self, working_url):
        scraper = EntityScraper(base_delay=3, max_delay=7)
        response = scraper.get(working_url)
        return response
    
    def _extract_companies(self, response, city):
        extractor =  BLDataExtractor(html_content=response.content, base_url=self.base_url)
        next_page_link, company_links = extractor.extract_companies(city)
        return next_page_link, company_links
    
    def _extract_company_data(self, response):
        extractor =  BLDataExtractor(html_content=response.content, base_url=self.base_url)
        company_data = extractor.extract_company_data()
        return company_data
    
    def _organise_company_data(self, company_data, city, states):
        location_data = {
            "country": "Cameroon",
            "city": city,
            "state": states[city] if city in states else "",
            "address": company_data["address"],
            "latitude": company_data["latitude"],
            "longitude": company_data["longitude"],
            "created_at": datetime.now(timezone.utc)
        }

        location_id = self.location_inserter.insert_document(location_data)
        if company_data["tags"] == "":
            industry = self.industry_maps.classify_company(company_data["description"], "desc")
        else:
            industry = self.industry_maps.classify_company(company_data["tags"], "tags")
        industry_id = self.industry_inserter.check_and_create_document(industry)

        updated_company_data = {
            "name": company_data["name"],
            "size": company_data["size"],
            "revenue": "",
            "website": company_data["website"],
            "description": company_data["description"],
            "contact_numbers": company_data["contact_numbers"],
            "location_id": location_id,
            "industry_id": industry_id,
            "created_at": datetime.now(timezone.utc)
        }
        return updated_company_data
    
    def _handle_company_flow(self, working_url, city, states):
        response = self._scraper(working_url)
        next_page_link, company_links = self._extract_companies(response, city)
        for link in company_links:
            sleep(random.uniform(1, 3))
            response = self._scraper(link)
            company_data = self._extract_company_data(response)

            if company_data:
                updated_company_data = self._organise_company_data(company_data, city, states)
                status = self.company_inserter.add_document(updated_company_data)
        return next_page_link


    def start_company_flow(self):
        try:
            file_path = os.path.join(self.files_dir, "cities.json")
            with open(file_path) as f:
                cities = json.load(f)

            file_path = os.path.join(self.files_dir, "city_state.json")
            with open(file_path) as f:
                states = json.load(f)
            
            city_links = list(cities.values())
            all_cities = list(cities.keys())

            file_path = os.path.join(self.files_dir, "scrapped_cities.json")
            with open(file_path) as f:
                scrapped_cities = json.load(f)

            for i in range(len(city_links)):
                if all_cities[i] not in scrapped_cities:
                    next_page_link = self._handle_company_flow(city_links[i], all_cities[i], states)
                    while True:
                        if next_page_link:
                            sleep(random.uniform(1, 3))
                            next_page_link = self._handle_company_flow(next_page_link, all_cities[i], states)
                        else:
                            break
                    
                    scrapped_cities[all_cities[i]] = city_links[i]
                    file_path = os.path.join(self.files_dir, "scrapped_cities.json")
                    with open(file_path, 'w') as f:
                        json.dump(scrapped_cities, f, indent=4)

                    self.logger.info(f"DONE WITH {all_cities[i]}!!")
            
            self.logger.info(f"DONE SCRAPPING ALL CITIES IN `cities.json`!!")

            # flush buffer for any remains
            self.company_inserter.flush_buffer()

            #close all open connections
            self.company_inserter.close_connection()
            self.location_inserter.close_connection()
            self.industry_inserter.close_connection()

            print(f"BUFFER: {self.company_inserter.buffer}\n")

        except Exception as e:
            self.logger.error(f"Error Occured in Flow: {str(e)}")



def  bl_runner(scraper):
    base_url = os.environ["BL_BASE_URL"]
    handler = BLFlowHandler(base_url=base_url)
    cities_url = f"{base_url}/browse-business-cities"

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        files_dir = os.path.join(current_dir, "files")
        file_path = os.path.join(files_dir, "cities.json")
        if not os.path.exists(file_path):
            print(f"Cities file not found")
            response = scraper.get(cities_url)
            print(f"Successfully scraped {cities_url}")
            # Process response here
            extractor =  BLDataExtractor(html_content=response.content, base_url=base_url)
            extractor.extract_cities()
            sleep(random.uniform(1, 3))  # Additional delay between pages
            
            handler.start_company_flow()
        else:
            handler.start_company_flow()

            
    except Exception as e:
        print(f"Failed to scrape {cities_url}: {str(e)}")


def google_runner(scraper):
    # base_url = os.environ["GGLE_BASE_URL"]
    base_url = os.environ["BL_BASE_URL"]
    handler = BLFlowHandler(base_url=base_url)

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        files_dir = os.path.join(current_dir, "files")
        file_path = os.path.join(files_dir, "cities.json")
        states_file_path = os.path.join(files_dir, "city_state.json")

        if not os.path.exists(file_path):
            print(f"Cities file not found")
            bl_base_url = os.environ["BL_BASE_URL"]
            cities_url = f"{bl_base_url}/browse-business-cities"
            response = scraper.get(cities_url)
            print(f"Successfully scraped {cities_url}")
            extractor =  BLDataExtractor(html_content=response.content, base_url=base_url)
            extractor.extract_cities()
            sleep(random.uniform(1, 3))  # Additional delay between pages

            file_path = os.path.join(files_dir, "cities.json")
            with open(file_path) as f:
                cities = json.load(f)

            with open(states_file_path) as f:
                states = json.load(f)
            
            all_cities = list(cities.keys())
            for city in all_cities:
                query = f"companies in {city}"
                companies = initiator(query)
                if len(companies)>0:
                    for company in companies:
                        updated_company_data = handler._organise_company_data(company, city, states)
                        status = handler.company_inserter.add_document(updated_company_data)
                sleep(3)
                
        else:
            with open(file_path) as f:
                cities = json.load(f)
            
            with open(states_file_path) as f:
                states = json.load(f)
            
            all_cities = list(cities.keys())
            for city in all_cities:
                query = f"companies in {city}"
                companies = initiator(query)
                if len(companies)>0:
                    for company in companies:
                        updated_company_data = handler._organise_company_data(company, city, states)
                        status = handler.company_inserter.add_document(updated_company_data)
                sleep(3)
        
        # flush buffer for any remains
        handler.company_inserter.flush_buffer()

        #close all open connections
        handler.company_inserter.close_connection()
        handler.location_inserter.close_connection()
        handler.industry_inserter.close_connection()

    except Exception as e:
        pass

if __name__ == "__main__":
    try:
        scraper = EntityScraper(base_delay=3, max_delay=7)
        # bl_runner(scraper)
        google_runner(scraper)
    except:
        print("scraper failed")
        pass
    