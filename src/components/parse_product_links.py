import requests
from haystack import component
from config.config_settings import ConfigSettings
from config.log_config import LoggerConfig
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
from typing import Dict

@component
class ParseProductLinks:
    def __init__(self, web_scrapping_config: Dict, headers: Dict, ikea_config: ConfigSettings, datasource_config: ConfigSettings):
        self.web_scrapping_config = web_scrapping_config
        self.headers = headers
        self.ikea_config = ikea_config
        self.logger = LoggerConfig().get_logger()
        self.datasource_config = datasource_config
    
    @component.output_types(product_links_data=Dict)
    def run(self, product_category_links_data: Dict):
        product_links_details = []
        product_data = []
        try:
            self.logger.info("Starting ParseProductLinks component")
            #self.logger.info(f"Product Links Data: {product_category_links_data}")
            
            for title, link in product_category_links_data.items():
                try:
                    # Assuming product_links is title: link
                    product_data.append({"title": title, "link": link})
                except ValueError as e:
                    self.logger.warning(f"Skipping product '{title}' due to ValueError: {e}")
                    continue

            df_products = pd.DataFrame(product_data)
            self.logger.info(f"Total products: {len(df_products)}")
            for _, row in df_products.iterrows():
                response = requests.get(row['link'], headers=self.headers)
                response.raise_for_status() # Raise an exception for bad status codes   
                soup = BeautifulSoup(response.text, self.web_scrapping_config['parse_product_links']['parser_type'])
                product_links = soup.find_all(self.web_scrapping_config['parse_product_links']['product_links_locator']['tag_name'],class_ = self.web_scrapping_config['parse_product_links']['product_links_locator']['class_name'])
                for p in product_links:
                    product_links_details.append({"title": row['title'],"parent_link": row['link'],"link": p.find(self.web_scrapping_config['parse_product_links']['link_child_tag'])[self.web_scrapping_config['parse_product_links']['link_attribute']]})

            self.logger.info(f"Total Product Links records: {len(product_links_details)}")
            df_product_links = pd.DataFrame(product_links_details)
            df_product_links.to_csv(os.path.join(self.datasource_config.parent_data_folder,self.web_scrapping_config['parse_product_links']['product_links_csv_filename']), index=False)
            return {"product_links_data": product_links_details}
        except Exception as e:
            self.logger.error(f"Error parsing product links: {e}", exc_info=True)
            return None