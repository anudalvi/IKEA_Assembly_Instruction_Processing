
import requests
from haystack import component
from config.config_settings import ConfigSettings
from config.log_config import LoggerConfig
from bs4 import BeautifulSoup
import re

from typing import Dict

@component
class ParseProductCategoryLinks:
    def __init__(self,web_scrapping_config:dict,headers:dict,ikea_config):
        self.ikea_config = ikea_config
        self.logger = LoggerConfig().get_logger()
        self.web_scrapping_config = web_scrapping_config
        self.headers = headers
            
    @component.output_types(product_category_links=Dict[str, str])
    def run(self):
        try:
            self.logger.info(f"Fetching category links from: {self.ikea_config.base_url + self.web_scrapping_config.get('fetch_product_details_main_url', '')}")
            
            response = requests.get(self.ikea_config.base_url + self.web_scrapping_config.get('fetch_product_details_main_url', ''), headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, self.web_scrapping_config["parse_product_category_links"]["parser_type"])
            
            product_links = soup.find_all('a', href=re.compile(self.web_scrapping_config['parse_product_category_links']['category_url_to_compile']))
            product_links_output = {
                link.text.strip(): link.get(self.web_scrapping_config['parse_product_category_links']['link_attribute_to_fetch']) 
                for link in product_links 
                if link.get(self.web_scrapping_config['parse_product_category_links']['link_attribute_to_fetch']) and link.text.strip()
            }
            
            self.logger.info(f"Successfully parsed {len(product_links_output)} product category links.")
            return {"product_category_links": product_links_output}
        except Exception as e:
            self.logger.error(f"Error parsing product category links: {e}", exc_info=True)
            return {"product_category_links": {}}

        