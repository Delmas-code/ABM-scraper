import os
import requests
import json
from time import sleep
import random
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from collections import defaultdict
import logging
from fake_useragent import UserAgent
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class InitialScraper:
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
        self.logger = logging.getLogger('InitialScraper')
        
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

class DataExtractor:
    def __init__(self, html_content, base_url, parser="html.parser"):
        self.html_soup = BeautifulSoup(html_content, parser)
        # print(f"{self.html_soup}\n")
        self.base_url = base_url
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('DataExtractor')
        
    def get_cities(self):
        try:
            section_w_cities = self.html_soup.find('section')
            content_w_cities = section_w_cities.find('div', class_="content")
            # print(f"{content_w_cities}\n")
            links =  content_w_cities.find_all('a', href= True)
            city_data = {}
            for link in links:
                city = link.contents[0].strip()
                city_url = f"{self.base_url}{link["href"]}"
                city_data[city] = city_url
            print(f"Got Cities \n")
            
            with open('cities.json', 'w', encoding='utf-8') as f:
                json.dump(city_data, f, indent=4)
                
            self.logger.info(f"City Data scrapped and stored successfully in cities.json!")
        except Exception as e:
            self.logger.error(f"Failed to get city info: {str(e)}")
        
if __name__ == "__main__":
    scraper = InitialScraper(base_delay=3, max_delay=7)
    
    base_url = os.environ["BASE_URL"]
    cities_url = f"{base_url}/browse-business-cities"
    try:
        response = scraper.get(cities_url)
        print(f"Successfully scraped {cities_url}")
        # Process response here
        extractor =  DataExtractor(html_content=response.content, base_url=base_url)
        extractor.get_cities()
        sleep(random.uniform(1, 3))  # Additional delay between pages
    except Exception as e:
        print(f"Failed to scrape {cities_url}: {str(e)}")
        