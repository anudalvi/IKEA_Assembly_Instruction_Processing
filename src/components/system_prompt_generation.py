import requests
from haystack import component
from config.log_config import LoggerConfig
from typing import Dict, List, Any   
import pandas as pd
import os   
import asyncio
from playwright.async_api import async_playwright
import json

@component
class SystemPromptGeneration:
    def __init__(self,datasource_config:dict):
        self.logger = LoggerConfig().get_logger()
        self.datasource_config = datasource_config
    
    @component.output_types(system_prompt=str)
    def run(self, result: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = ""
        try:
            product_details = ""
            product_material = ""
            safety_compliance = ""
            product_name_arr = ["", "", ""]
            product_category = ""

            #product_name_arr = result['PDF File Details']["product_name"].split(",")
            for row in result.get('Product Details', []):
                if row['header'] == 'Product details':
                    text = row['text']
                    if "Designer" in text:
                        product_details = text[:text.index("Designer")].strip()
                    else:
                        product_details = text.strip()
                if row['header'] == 'Material':
                    product_material = row['text']
                if row['header'] == 'Safety and compliance':
                    safety_compliance = row['text']
                if row['header'] == 'product_name':
                    product_name_arr = row['text'].split(',')
                if row['header'] == 'product_category':
                    product_category = row['text']
            
            '''for r in result.get('PDF File Details', []):
                if r['pdf_type'] == 'Assembly instructions':
                    product_name_arr = r['product_name'].split(',')
                    product_category = r['product_category']'''

            replacements = {
                "product_name": product_name_arr[0] if len(product_name_arr) > 0 else "",
                #"product_dimension": product_name_arr[2] if len(product_name_arr) > 2 else "",
                #"product_color": product_name_arr[1] if len(product_name_arr) > 1 else "",
                "product_category": product_category,
                "product_details": product_details,
                "safety_compliance": safety_compliance
                #,"material": product_material
            }
            #print(f"Replacement: {replacements}")

            with open(self.datasource_config.system_prompt_filepath, 'r') as f:
                for line in f:
                    # Safely replace placeholders to avoid KeyError with literal braces in the template (e.g. JSON examples)
                    formatted_line = line
                    for key, value in replacements.items():
                        placeholder = "{" + key + "}"
                        formatted_line = formatted_line.replace(placeholder, str(value))
                    system_prompt = system_prompt + formatted_line
            self.logger.info(f"System Prompt: {system_prompt[0:50]}")
            return {"system_prompt":system_prompt}
        except Exception as e:
            self.logger.error(f"Error generating system prompt: {e}", exc_info=True)
            return {"system_prompt": ""}