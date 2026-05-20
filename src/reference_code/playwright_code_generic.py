from playwright.sync_api import sync_playwright
import requests
from haystack import component
from config.log_config import LoggerConfig
from typing import Dict, List   
import pandas as pd
import os   
import asyncio
import json
from config.config_settings import ConfigSettings

def read_config_file():
    with open("/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/Web_Scrapping_locator.json", 'r') as f:
        config = json.load(f)
    return config    

def product_manual_download():
    try:
        web_scrapping_config = read_config_file()
        settings = ConfigSettings()
        print(f"Starting ParseProductDetailsAndManualDownload component")
        df_product_links = pd.read_csv("/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/product_links.csv")
        #df_product_links = df_product_links[df_product_links['link'].isin(['https://www.ikea.com/nl/en/p/lack-wall-shelf-unit-black-blue-00592870/','https://www.ikea.com/nl/en/p/kallax-shelving-unit-white-80275887/','https://www.ikea.com/nl/en/p/hemnes-glass-door-cabinet-with-3-drawers-grey-green-light-brown-stained-00596161/'])
        if web_scrapping_config["product_details"]["product_links_filter"]:
            df_product_links = df_product_links[df_product_links['link'].isin(web_scrapping_config["product_details"]["product_links_filter"]["link"])
            & df_product_links['title'].isin(web_scrapping_config["product_details"]["product_links_filter"]["title"])]
        print(f"Total Records: {len(df_product_links)}")
        for _,row in df_product_links.iterrows():
            download_task = parse_product_links_playwright(row,settings,web_scrapping_config)
            print(download_task)
        '''file_semaphore = asyncio.Semaphore(settings.datasource_config.max_concurrent_files)
        tasks = []
        for _,row in df_product_links.iterrows():
            task=asyncio.create_task(parse_product_links_playwright(row,file_semaphore))
            tasks.append(task)
            results = await asyncio.gather(*tasks, return_exceptions=True)
        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error processing item {i}: {result}", exc_info=True)
            else:
                valid_results.append(result)
            
        print(f"Successfully processed {len(valid_results)} products")
            
        return {"product_details_and_manual_download": valid_results}'''
    except Exception as e:
        print(f"Error parsing product details and manual download: {e}", exc_info=True)
        return {"product_details_and_manual_download": []}


def parse_product_links_playwright(row,settings,web_scrapping_config):
    container_children_details = []
    download_result = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(row['link'])
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(5000)
            product_name_container = page.locator("xpath=//h1[@class='pipcom-text pipcom-typography-heading-s']")
            all_divs = product_name_container.all()
            if len(all_divs) > 1:
                product_name = ''
                for div in all_divs:
                    product_name = product_name + ' ' + div.text_content()
            else:
                product_name = product_name_container.text_content()
            print(f"Product Name: {product_name}")
            containers = page.locator("xpath=//div[@class='pipf-product-details-modal']").all()
            for container in containers:
                title_text = '' 
                header_text = ''
                instruction_pdf_link = []
                children = get_all_children(container)
                #print("Children nodes: ",len(children))
                #print(json.dumps(children, indent=2,ensure_ascii=False))
                product_id_dict = {}
                for child_node in children:
                    if 'pipf-product-identifier__label' in child_node["class"]:
                        product_id_dict["label"] = child_node["text"]
                    if 'pipf-product-identifier__value' in child_node["class"]:
                        product_id_dict["value"] = child_node["text"]
                    if child_node['tag'] in ['h2','h3','h4']:
                        if len(title_text) > 0 and len(instruction_pdf_link) == 0:
                            container_children_details.append({"header":header_text.strip(),"text":title_text.strip()})
                        if len(instruction_pdf_link) > 0:
                            container_children_details.append({"header":header_text.strip(),"text":title_text.strip(),"instruction_pdf":instruction_pdf_link})
                            instruction_pdf_link = []
                        title_text = ''
                        header_text = child_node["text"]
                    elif child_node['tag'] not in ['h2','h3','h4'] and len(child_node["text"]) > 0 and child_node["class"].find("pipf-product-identifier") == -1:
                        title_text = title_text + " \n " + child_node["text"]
                    elif child_node['tag'] == 'a' and len(header_text) > 0:
                        instruction_pdf_link.append(child_node["href"])
                        download_result.append(download_assembly_instruction_files(child_node["href"],header_text,settings,row['link'],row['title'],product_name)) 
                if len(header_text)>0 and len(title_text)>0 and len(instruction_pdf_link)>0 and header_text not in [d['header'] for d in container_children_details]:
                    container_children_details.append({"header":header_text.strip(),"text":title_text.strip(),"instruction_pdf":instruction_pdf_link})
                if len(product_id_dict) > 0:
                    container_children_details.append({"header":product_id_dict["label"].strip(),"text":product_id_dict["value"].strip()})
            result = {"Product Details":container_children_details,"PDF File Details":download_result}   
            #print("Results:",result)
            #print(json.dumps(container_children_details, indent=2,ensure_ascii=False))  
            return result
    except Exception as e:
        print(f"Error parsing product: {row['title']}: {e}", exc_info=True)
        return None

def get_all_children(container,depth = 0,max_depth = 20):
    nodes = []
    if depth > max_depth:
        return nodes
    try:
        children_container = container.locator("> *")
        for child in children_container.all():
            tag = child.evaluate("el => el.tagName.toLowerCase()")
            text = child.evaluate("el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('\\n').trim()")
            text = text.encode('utf-8').decode('utf-8')
            class_name = child.evaluate("el => el.className")
            href = child.evaluate("el => el.href")
            nodes.append({
                "tag": tag,
                "text":text,
                "depth":depth,
                "class":class_name,
                "href":href if href is not None else None
            })
            #"children":get_all_children(child,depth+1,max_depth)})
            nodes.extend(get_all_children(child,depth+1,max_depth))
        return nodes
    except Exception as e:
        print(f"Error getting all children: {e}", exc_info=True)
        return nodes


def download_assembly_instruction_files(url,header_text,settings,product_link,product_title,product_name):
    try:
        download_dir = os.path.join(settings.datasource_config.pfdfile_path, header_text)
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
        fetch_pdf()
        #await asyncio.to_thread(fetch_pdf)
        pdf_file_size = os.path.getsize(pdf_file_path)/(1024*1024)
        return {
                    'pdf_file_path': os.path.abspath(pdf_file_path),
                    'pdf_file_name': pdf_file_name,
                    'pdf_file_size': f"{pdf_file_size:.2f} MB",
                    'pdf_file_url': url,
                    'product_link': product_link,
                    'product_category': product_title,
                    'product_name': product_name,
                    'pdf_type':header_text,
                    'Download Status':'Success'
                }
    except Exception as e:
        print(f"Error downloading assembly instruction files: {e}", exc_info=True)


product_manual_download()