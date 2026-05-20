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
class ParseProductDetailsAndManualDownload:
    def __init__(self,web_scrapping_config:dict,headers:dict,ikea_config,datasource_config):
        self.ikea_config = ikea_config
        self.logger = LoggerConfig().get_logger()
        self.web_scrapping_config = web_scrapping_config
        self.headers = headers
        self.datasource_config = datasource_config
    
    '''@component.output_types(product_details_and_manual_download=List[Dict[str, Any]])
    def run(self, product_links_data: Dict):
        """Synchronous fallback for the component."""
        try:
            # Check if an event loop is already running
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in a thread pool (which AsyncPipeline does for sync components),
                # we can't easily block. But if we're in the main thread, this is weird.
                # However, for Haystack AsyncPipeline with run_async available, this shouldn't be called.
                return asyncio.run_coroutine_threadsafe(self.run_async(product_links_data), loop).result()
            else:
                return asyncio.run(self.run_async(product_links_data))
        except RuntimeError:
            # No event loop, we can safely use asyncio.run
            return asyncio.run(self.run_async(product_links_data))'''

    @component.output_types(product_details_and_manual_download=List[Dict[str, Any]])
    def run(self, product_links_data: Dict):
        return asyncio.run(self.run_async(product_links_data))

    @component.output_types(product_details_and_manual_download=List[Dict[str, Any]])
    async def run_async(self, product_links_data: Dict):
        try:
            self.logger.info(f"Starting ParseProductDetailsAndManualDownload component")
            #self.logger.info(f"Product Links Data: {product_links_data}")
            df_product_links = pd.DataFrame(product_links_data)
            #df_product_links = df_product_links[df_product_links['link'].isin(['https://www.ikea.com/nl/en/p/lack-wall-shelf-unit-black-blue-00592870/','https://www.ikea.com/nl/en/p/kallax-shelving-unit-white-80275887/','https://www.ikea.com/nl/en/p/hemnes-glass-door-cabinet-with-3-drawers-grey-green-light-brown-stained-00596161/'])
            if self.web_scrapping_config["product_details"]["product_links_filter"]:
                df_product_links = df_product_links[df_product_links['link'].isin(self.web_scrapping_config["product_details"]["product_links_filter"]["link"])
                & df_product_links['title'].isin(self.web_scrapping_config["product_details"]["product_links_filter"]["title"])]
            self.logger.info(f"Total Records: {len(df_product_links)}")
            file_semaphore = asyncio.Semaphore(self.datasource_config.max_concurrent_files)
            tasks = []
            for _,row in df_product_links.iterrows():
                task=asyncio.create_task(self.parse_product_links_playwright(row,file_semaphore))
                tasks.append(task)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Filter out exceptions and log them
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error processing item {i}: {result}", exc_info=True)
                else:
                    valid_results.append(result)
            
            self.logger.info(f"Successfully processed {len(valid_results)} products")
            
            return {"product_details_and_manual_download": valid_results}
        except Exception as e:
            self.logger.error(f"Error parsing product details and manual download: {e}", exc_info=True)
            return {"product_details_and_manual_download": []}
    

    async def parse_product_links_playwright(self, product_links_data_row: pd.Series, semaphore: asyncio.Semaphore):
        container_children_details = []
        download_result = []
        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(product_links_data_row['link'])
                await page.wait_for_load_state('domcontentloaded')
                await page.wait_for_timeout(5000)
                
                product_name_container = page.locator(self.web_scrapping_config['product_details']['product_links_locators']['product_name_container']['locator'])
                all_divs = await product_name_container.all()
                if len(all_divs) > 1:
                    product_name = ''
                    for div in all_divs:
                        product_name = product_name + ' ' + await div.text_content()
                else:
                    product_name = await product_name_container.text_content()
                
                self.logger.info(f"Product Name: {product_name}")
                containers = await page.locator(self.web_scrapping_config['product_details']['product_links_locators']['containers_xpath']).all()
                for container in containers:
                    title_text = '' 
                    header_text = ''
                    instruction_pdf_link = []
                    children = await self.get_all_children(container)
                    self.logger.info(f"Children nodes: {len(children)}")
                    # self.logger.info(json.dumps(children, indent=2,ensure_ascii=False))
                    product_id_dict = {}
                    for child_node in children:
                        if self.web_scrapping_config['product_details']['product_links_locators']['product_id_label'] in child_node["class"]:
                            product_id_dict["label"] = child_node["text"]
                        if self.web_scrapping_config['product_details']['product_links_locators']['product_id_value'] in child_node["class"]:
                            product_id_dict["value"] = child_node["text"]
                        if child_node['tag'] in self.web_scrapping_config['product_details']['product_links_locators']['headers_tag']:
                            if len(title_text) > 0 and len(instruction_pdf_link) == 0:
                                container_children_details.append({"header": header_text.strip(), "text": title_text.strip()})
                            if len(instruction_pdf_link) > 0:
                                container_children_details.append({"header": header_text.strip(), "text": title_text.strip(), "instruction_pdf": instruction_pdf_link})
                                instruction_pdf_link = []
                            title_text = ''
                            header_text = child_node["text"]
                        elif child_node['tag'] not in self.web_scrapping_config['product_details']['product_links_locators']['headers_tag'] and len(child_node["text"]) > 0 and child_node["class"].find(self.web_scrapping_config['product_details']['product_links_locators']['product_identifier_keyword']) == -1:
                            title_text = title_text + " \n " + child_node["text"]
                        elif child_node['tag'] == 'a' and len(header_text) > 0:
                            instruction_pdf_link.append(child_node["href"])
                            download_result.append(await self.download_assembly_instruction_files(child_node["href"], header_text, self.datasource_config, product_links_data_row['link'], product_links_data_row['title'], product_name, semaphore)) 
                    
                    if len(header_text) > 0 and len(title_text) > 0 and len(instruction_pdf_link) > 0 and header_text not in [d['header'] for d in container_children_details]:
                        container_children_details.append({"header": header_text.strip(), "text": title_text.strip(), "instruction_pdf": instruction_pdf_link})
                    if len(product_id_dict) > 0:
                        container_children_details.append({"header": product_id_dict["label"].strip(), "text": product_id_dict["value"].strip()})
                    container_children_details.append({"header": "product_name", "text": product_name}) 
                    container_children_details.append({"header": "product_category", "text": product_links_data_row['title']}) 
                await browser.close()
                result = {"Product Details": container_children_details, "PDF File Details": download_result}   
                return result
        except Exception as e:
            if browser:
                await browser.close()
            self.logger.error(f"Error parsing product links: {product_links_data_row['link']}. Error: \n {e}", exc_info=True)
            return None

    async def get_all_children(self, container, depth=0, max_depth=20):
        nodes = []
        if depth > max_depth:
            return nodes
        try:
            children_container = container.locator("> *")
            children = await children_container.all()
            for child in children:
                tag = await child.evaluate("el => el.tagName.toLowerCase()")
                text = await child.evaluate("el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('\\n').trim()")
                text = text.encode('utf-8').decode('utf-8')
                class_name = await child.evaluate("el => el.className")
                href = await child.evaluate("el => el.href")
                nodes.append({
                    "tag": tag,
                    "text": text,
                    "depth": depth,
                    "class": class_name,
                    "href": href if href is not None else None
                })
                nodes.extend(await self.get_all_children(child, depth + 1, max_depth))
            return nodes
        except Exception as e:
            self.logger.error(f"Error getting all children: {e}", exc_info=True)
            return nodes
    

    async def download_assembly_instruction_files(self, url, header_text, datasource_config, product_link, product_title, product_name, semaphore):
        try:
            async with semaphore:
                download_dir = os.path.join(datasource_config.pfdfile_path, header_text)
                os.makedirs(download_dir, exist_ok=True)
                        
                pdf_file_name = url.split('/')[-1]
                pdf_file_path = os.path.join(download_dir, pdf_file_name.strip())

                # Use requests to download binary content directly
                # Running in a thread to avoid blocking the event loop
                def fetch_pdf():
                    response = requests.get(url, stream=True, timeout=30)
                    response.raise_for_status()
                    with open(pdf_file_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return pdf_file_path
                
                await asyncio.to_thread(fetch_pdf)
                pdf_file_size = os.path.getsize(pdf_file_path) / (1024 * 1024)
                
            return {
                    'pdf_file_path': os.path.abspath(pdf_file_path),
                    'pdf_file_name': pdf_file_name,
                    'pdf_file_size': f"{pdf_file_size:.2f} MB",
                    'pdf_file_url': url,
                    'product_link': product_link,
                    'product_category': product_title,
                    'product_name': product_name,
                    'pdf_type': header_text,
                    'Download Status': 'Success'
                }
        except Exception as e:
            self.logger.error(f"Error downloading assembly instruction files: {e}", exc_info=True)
            return {
                    'pdf_file_path': None,
                    'pdf_file_name': None,
                    'pdf_file_size': None,
                    'pdf_file_url': url,
                    'product_link': product_link,
                    'product_category': product_title,
                    'product_name': product_name,
                    'pdf_type': header_text,
                    'Download Status': 'Failed'
                }