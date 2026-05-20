from pathlib import Path
import pymupdf
import requests
from config.config_settings import ConfigSettings
from config.log_config import LoggerConfig
import re
import pandas as pd
import asyncio
import threading
import os
import json
import re


class AssemblyInstructionDataExtractor:
    def __init__(self,logger=None,settings=None):
        self.logger = logger if logger is not None else LoggerConfig().get_logger()
        self.settings = settings if settings is not None else ConfigSettings()

    async def get_product_details_nodes(self,product_details_arr,pdf_file_details):
        key_arr = []
        product_details_node = {}
        instruction_manual_node =[]
        #manual_node_details = {}
        try:
            for pdf_file_detail in pdf_file_details:
                if pdf_file_detail['pdf_type'].find('Assembly')!=-1:
                    product_details_node['product_name']=pdf_file_detail['product_name'].split(',')[0]
                    product_details_node['product_color']=pdf_file_detail['product_name'].split(',')[1]
                    product_details_node['product_dimension']=pdf_file_detail['product_name'].split(',')[2]
                    product_details_node['assembly_instruction_file_path'] = pdf_file_detail['pdf_file_path']
                    product_details_node['product_category']=pdf_file_detail['product_category']
                    product_details_node['instruction_type']=pdf_file_detail['pdf_type']
                    pdf_file_name_arr = pdf_file_detail['pdf_file_name'].split("__")
                    product_details_node['assembly_instruction_filename'] = pdf_file_detail['pdf_file_name'].replace('.pdf','')
                    product_details_node['assembly_manual_id'] = pdf_file_name_arr[1].replace('.pdf','')
                    instruction_manual_node.append(
                        {
                            'manual_id' : pdf_file_detail['pdf_file_name'].split('__')[1].replace('.pdf',''),
                            'product_name' : pdf_file_detail['product_name'].split(',')[0],
                            'manual_file_path' : pdf_file_detail['pdf_file_path'],
                            'manual_file_name' : pdf_file_detail['pdf_file_name'].replace('.pdf',''),
                            'manual_type' : pdf_file_detail['pdf_type']
                        }
                    )

                else:
                    instruction_manual_node.append(
                        {
                            'manual_id': pdf_file_detail['pdf_file_name'].split('__')[1].replace('.pdf',''),
                            'product_name':pdf_file_detail['product_name'].split(',')[0],
                            'manual_file_path' : pdf_file_detail['pdf_file_path'],
                            'manual_file_name' : pdf_file_detail['pdf_file_name'].replace('.pdf',''),
                            'manual_type': pdf_file_detail['pdf_type']
                        }
                    )
                    
            for product_details in product_details_arr:
                if product_details['header'] not in ['Assembly instructions','Advice and care instructions']:
                    if product_details['header'] not in key_arr:
                        key_arr.append(product_details['header'])
                        product_details_node[product_details['header']] = product_details['text']
                    else:
                        product_details_node[product_details['header']] += product_details['text']
            return product_details_node,instruction_manual_node
        except Exception as e:
            self.logger.error(f"Error processing data for product details nodes for {pdf_file_detail['pdf_file_name']}: {e}", exc_info=True)
            return None,None    

    async def process_markdown_file(self,pdf_file_details):
        chunk_nodes_arr = []
        markdown_file_chunk_arr = []
        try:
            for pdf_file_detail in pdf_file_details:
                if pdf_file_detail['pdf_type'].find('Assembly')!=-1:
                    pdf_file_path = pdf_file_detail['pdf_file_path']
                    pdf_file_name = os.path.basename(pdf_file_path).replace('.pdf','')
                    markdown_folder_path = os.path.join(self.settings.datasource_config.markdown_files_path,pdf_file_name)  
                    if os.path.exists(markdown_folder_path):           
                        for markdown_file in Path(markdown_folder_path).rglob("*.md"):
                            markdown_file_start_page = markdown_file.name.replace('.md','').split("__")[1].split('_')[-2]
                            markdown_file_end_page = markdown_file.name.replace('.md','').split("__")[1].split('_')[-1]
                            markdown_file_chunk_arr.append(
                                {
                                    'manual_id' : pdf_file_name.split('__')[1].replace('.pdf',''),
                                    "pdf_file_name":pdf_file_name,
                                    "markdown_file_name":markdown_file.name.replace('.md',''),
                                    "markdown_chunk_file_path":os.path.join(markdown_folder_path,markdown_file),
                                    "markdown_file_start_page":markdown_file_start_page,
                                    "markdown_file_end_page":markdown_file_end_page
                                }
                            )
                            #self.logger.info(f"Markdown file under process: {markdown_file}")
                            markdown_file_path = os.path.join(markdown_folder_path,markdown_file)
                            chunks_arr = await self.chunk_markdown_file(markdown_file_path,markdown_file.name)
                            #self.logger.info(f"Chunks array: {chunks_arr}")
                            chunk_nodes = await self.get_markdown_data_chunk_nodes(chunks_arr,pdf_file_name,markdown_file.name,markdown_file_start_page,markdown_file_end_page)
                            #self.logger.info(f"Chunk nodes: {chunk_nodes}")
                            chunk_nodes_arr.append(chunk_nodes)
            return chunk_nodes_arr,markdown_file_chunk_arr
        except Exception as e:
            self.logger.error(f"Error processing data from markdown file: {e}", exc_info=True)
            return None,None
    
    async def get_markdown_data_chunk_nodes(self,chunks_arr,pdf_file_name,markdown_file_name,markdown_file_start_page,markdown_file_end_page):
        image_node_arr = []
        language_warning_node_arr = []
        text_node_arr = []
        try:
            for i in range(len(chunks_arr)):
                if chunks_arr[i]['type'] == 'image':
                    image_id = '_'.join(chunks_arr[i]['content'].split('/')[-1].replace('.png)','').split('_')[0:2])
                    img_node = {
                        'pdf_file_name':pdf_file_name,
                        'markdown_file_name':markdown_file_name.replace(".md",""),
                        'page_number' : chunks_arr[i]['page'] + int(markdown_file_start_page) - 1,
                        'image_id' : image_id,
                        'image_path' : chunks_arr[i]['content'].replace('![Image]','').replace(')','').replace('(',''),
                        'content':chunks_arr[i]['content'],
                        'image_hex_name' : chunks_arr[i]['content'].split('/')[-1].replace('.png)',''),
                        'type':chunks_arr[i]['type']
                    }
                    image_node_arr.append(img_node)
                elif chunks_arr[i]['type'] == 'text':
                    text_node = {
                        'pdf_file_name':pdf_file_name,
                        'markdown_file_name':markdown_file_name.replace(".md",""),
                        'page_number' : chunks_arr[i]['page'] + int(markdown_file_start_page) - 1,
                        'content' : chunks_arr[i]['content'],
                        'type':chunks_arr[i]['type']
                    }
                    text_node_arr.append(text_node)
                elif chunks_arr[i]['type'] == 'language_warning_text':
                    if chunks_arr[i+1]['type'] == 'image' and chunks_arr[i+2]['type'] == 'text' and i<=len(chunks_arr)-3:
                        chunks_arr[i]['content'] = chunks_arr[i]['content'] + ' ' + chunks_arr[i+2]['content']
                        #print("New Content: ",chunks_arr[i]['content'])
                    warning_language = chunks_arr[i]['content'].split("\n\n##")[0]
                    warning_text = chunks_arr[i]['content'].split("\n\n##")[1]
                    language_warning_node = {
                        'pdf_file_name':pdf_file_name,
                        'markdown_file_name':markdown_file_name.replace(".md",""),
                        'page_number' : chunks_arr[i]['page'] + int(markdown_file_start_page) - 1,
                        'language_warning' : warning_language,
                        'content' : warning_text,
                        'type':chunks_arr[i]['type']
                    }
                    #print("Language Warning Node: ",language_warning_node)
                    language_warning_node_arr.append(language_warning_node)
            return {
                'image_node_arr':image_node_arr,
                'language_warning_node_arr':language_warning_node_arr,
                'text_node_arr':text_node_arr
            }

        except Exception as e:
            self.logger.error(f"Error processing data from markdown file: {e}", exc_info=True)

    async def chunk_markdown_file(self,markdown_file_path,markdown_file_name):
        chunks_arr = []
        try:
            self.logger.info(f"Markdown file under process: {markdown_file_name}")
            with open(markdown_file_path,'r') as f:
                markdown_data = f.read()
            page_sections = markdown_data.split("<!-- Page Break -->")
            for page_num,page_section in enumerate(page_sections):
                #header_pattern = re.compile(r'((?:^.*\n)?)(##.*)')
                header_split_pattern = r'\n\n(?=[^\n]+\n\n##)'
                #parts = re.split(r'(^.*\n?##.*)', page_section, flags=re.MULTILINE)
                parts = re.split(header_split_pattern, page_section, flags=re.MULTILINE)
                for part in parts:
                    if not part.strip():
                        continue
                        
                    # 3. Further split by ![Image] tags
                    # This separates text chunks from image chunks within the same header section
                    sub_parts = re.split(r'(!\[Image\].*?\))', part)
            
                    for sub_part in sub_parts:
                        clean_chunk = sub_part.strip()
                        if clean_chunk:
                            chunk_data = {
                                "page": page_num + 1,
                                "content": clean_chunk,
                                "type": "image" if clean_chunk.startswith("![Image]") else "language_warning_text" if re.match(r"^[^\n]+\n\n##", clean_chunk) else "text"
                            }
                            chunks_arr.append(chunk_data)
            return chunks_arr
        except Exception as e:
            self.logger.error(f"Error chunking markdown file {markdown_file_name}: {e}", exc_info=True)
            return None
    
    async def process_json_image_description_file(self,result):
        image_json_node_arr = []
        try:
            for r in result.get('PDF File Details', []):
                if r['pdf_type'].find('Assembly')!=-1:
                    pdf_file_path = r['pdf_file_path']
                    pdf_file_name = os.path.basename(pdf_file_path).replace('.pdf','')
                    markdown_folder_path = os.path.join(self.settings.datasource_config.markdown_files_path,pdf_file_name)  
                    if os.path.exists(markdown_folder_path):  
                        self.logger.info(f"File under process: {markdown_folder_path}")               
                        for json_file in Path(markdown_folder_path).rglob("*.json"):
                            json_file_path = str(json_file.absolute())
                            json_data = None
                            try:
                                with open(json_file,'r') as f:
                                    json_data = json.load(f)
                            except json.JSONDecodeError:
                                self.logger.warning(f"Malformed JSON in {json_file}. Attempting robust extraction.")
                            # Fallback to your manual extraction only if standard load fails
                                with open(json_file, 'r', encoding='utf-8') as f:
                                    raw = f.read()
                                    start, end = raw.find('{'), raw.rfind('}')
                                    if start != -1 and end != -1:
                                        try:
                                            json_data = json.loads(raw[start:end+1])
                                        except:
                                            continue
                            if not json_data:
                                continue
                            
                            # Support legacy double-encoded JSON if any exists, and ensure base case is a dict
                            if isinstance(json_data, str):
                                self.logger.info(f"JSON Data is string, use loads to convert to dict.")
                                json_data = json.loads(json_data)
                            json_validation_result = await self.__validate_json_schema(json_data,json_file.name)
                            #self.logger.info(f"JSON Data: {json_data}")
                            #self.logger.info(f"JSON Validation Result: {json_validation_result}")
                            #self.logger.info(f"JSON file validation result: {json_validation_result[json_file.name]}")
                            if len(json_validation_result[json_file.name]) == 0:
                                image_json_node = await self.get_image_json_node_data(json_data, pdf_file_name, json_file)
                                if image_json_node:
                                    #self.logger.info(f"Image json node data: {image_json_node}")
                                    image_json_node_arr.append(image_json_node)
                            else:
                                self.logger.warning(f"JSON validation failed for file: {json_file_path}")
                                self.logger.warning(f"Missing fields: {json_validation_result[json_file.name]}")
            return image_json_node_arr
        except Exception as e:
            self.logger.error(f"Error processing data from json image description file: {e}", exc_info=True)
            return None
    
    async def get_image_json_node_data(self,json_data,pdf_file_name,json_file):
        image_json_node_data = {}
        try:
            # Normalize classification for comparison
            classification = str(json_data.get('classification', '')).lower()
            # Identification fields common to both types
            image_json_node_data['pdf_file_name'] = pdf_file_name
            image_json_node_data['markdown_file_name'] = json_file.parent.name # Cross-platform folder name
            image_json_node_data['image_id'] = json_file.stem # Gets filename without extension
            image_json_node_data['classification'] = json_data.get('classification')
            if "assembly" in classification:
                image_json_node_data['step_name'] = json_data.get('step_name', '')
                image_json_node_data['action'] = json_data.get('action', '')
                image_json_node_data['parts'] = json_data.get('parts', [])
                image_json_node_data['tools'] = json_data.get('tools', [])
                image_json_node_data['tools_str'] = ', '.join(json_data.get('tools', []))
                image_json_node_data['safety'] = json_data.get('safety') or json_data.get('safety_alert', '')
                image_json_node_data['difficulty'] = json_data.get('difficulty', [])
                image_json_node_data['difficulty_str'] = ', '.join(json_data.get('difficulty', []))
            elif "guidance" in classification:
                image_json_node_data['content_type'] = json_data.get('content_type', '')
                image_json_node_data['description'] = json_data.get('description', '')
                image_json_node_data['key_info'] = json_data.get('key_info', [])
                image_json_node_data['key_info_str']= ", ".join(f"{i+1}. {item}" for i,item in enumerate(json_data.get('key_info', [])))
                image_json_node_data['guidance'] = json_data.get('guidance', '')
            return image_json_node_data
        except Exception as e:
            self.logger.error(f"Error getting image json node data from json image description file: {e}", exc_info=True)
            return None

    async def __validate_json_schema(self,json_data,json_file_name):
        json_validation={}
        try:
            if isinstance(json_data,dict):
                classification = json_data.get('classification', '')
                if "assembly" in classification.lower():
                    required_fields = ["classification","step_name","action","parts","tools","difficulty"]
                    missing_fields = [field for field in required_fields if field not in json_data]
                    # Check for safety or safety_alert
                    if "safety" not in json_data and "safety_alert" not in json_data:
                        missing_fields.append("safety/safety_alert")
                elif "guidance" in classification.lower():
                    required_fields = ["classification","content_type","description","key_info","guidance"]
                    missing_fields = [field for field in required_fields if field not in json_data]
                else:
                    self.logger.error(f"Error validating json schema: 'classification' missing or invalid in {json_file_name}")
                    missing_fields=[f"Unknown classification: {classification}"]
            else:
                self.logger.error(f"Error validating json schema: data is not a dict in {json_file_name}")
                missing_fields=["Invalid json data"]
            json_validation[json_file_name]=missing_fields
            return json_validation        
        except Exception as e:
            self.logger.error(f"Unexpected error validating json schema for {json_file_name}: {e}", exc_info=True)
            return {json_file_name: [f"Validation error: {str(e)}"]}

     