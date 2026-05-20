from haystack import component
from config.log_config import LoggerConfig
from pathlib import Path
import os
import re
import json
import uuid

@component
class ChunkDataProcessor:
    def __init__(self,datasource_config,ikea_config,markdown_chunk_cfg):
        self.datasource_config = datasource_config
        self.ikea_config = ikea_config
        self.markdown_chunk_cfg = markdown_chunk_cfg
        self.logger = LoggerConfig().get_logger()
    
    def run(self,input):
        assembly_file_data = {}
        try:
            files_to_process = [item['pdf_file_name'] for item in input['PDF File Details'] if 'Assembly' in item.get('pdf_type', '')]
            for file_name in files_to_process:
                chunk_counter = 0
                pdf_chunks_arr = []
                pdf_file_path = os.path.join(self.datasource_config.markdown_files_path,file_name.replace(".pdf",''))
                for file in sorted(Path(pdf_file_path).rglob('*.md'), key=lambda x: x.stat().st_ctime):
                    self.logger.info(f"Processing file: {file}")
                    chunk_markdown_file_name = file.name.replace(".md",'')
                    start_page, end_page = self.__get_page_range(chunk_markdown_file_name)
                    self.logger.info(f"Start page: {start_page}, End page: {end_page}")
                    if start_page is None or end_page is None:
                        self.logger.warning(f"Skipping file {file}: could not determine page range")
                        continue
                    chunk_arr, chunk_counter = self.chunk_markdown_file(file,file_name,start_page,end_page,chunk_counter)
                    self.logger.info(f"Chunked file: {chunk_arr}")
                    if chunk_arr is None or len(chunk_arr) == 0:
                        self.logger.warning(f"Skipping file {file}: could not chunk file")
                        continue
                    pdf_chunks_arr.extend(chunk_arr)
                assembly_file_data[file_name] = pdf_chunks_arr
            self.logger.info(f"Assembly file data: {assembly_file_data}")
        except Exception as e:
            self.logger.error(f"Error processing file: {e}",exc_info=True)
            return None
        return assembly_file_data
    
    def __get_page_range(self,chunk_markdown_file_name):
        try:
            start_page = chunk_markdown_file_name.split("__")[1].split('_')[-2]
            end_page = chunk_markdown_file_name.split("__")[1].split('_')[-1]
            return start_page,end_page
        except Exception as e:
            self.logger.error(f"Error getting page range for {chunk_markdown_file_name} markdown file: {e}",exc_info=True)
            return None, None

    def chunk_markdown_file(self,file_path,file_name,start_page,end_page,chunk_counter):
        chunk_arr = []
        try:
            with open(file_path,'r',encoding='utf-8') as f:
                file_content = f.read()
        except Exception as e:
            self.logger.error(f"Error reading file: {e}",exc_info=True)
            return [], chunk_counter
        try:
            page_sections = file_content.split(self.markdown_chunk_cfg.page_sections_pattern)
            for page_num, page_section in enumerate(page_sections):
                for part in re.split(self.markdown_chunk_cfg.header_split_pattern,page_section):
                    if not part.split():
                        continue
                    
                    sub_parts = re.split(self.markdown_chunk_cfg.image_ref_pattern,part)
                    for sub_part in sub_parts:
                        clean_chunk = sub_part.strip()
                        if clean_chunk:
                            chunk_data = {}
                            chunk_counter += 1
                            chunk_data["chunk_id"] = f"{file_name.replace('.pdf','')}_chunk_{chunk_counter}"  
                            chunk_data["page_number"] = page_num + int(start_page)
                            chunk_data["assembly_instruction_file_name"] = file_name.replace(".pdf","")
                            if re.match(self.markdown_chunk_cfg.image_ref_pattern,clean_chunk):
                                chunk_data["image_file_path"] = clean_chunk
                                chunk_data["content"] = self.get_image_desc(clean_chunk) if self.get_image_desc(clean_chunk) else clean_chunk
                                chunk_data["type"] = "image"
                                chunk_data["image_id"] = self.get_image_id(clean_chunk) if self.get_image_id(clean_chunk) else ""
                            else:
                                chunk_data["image_file_path"] = ""
                                chunk_data["content"] = clean_chunk
                                chunk_data["type"] = "text"
                                chunk_data["image_id"] = ""
                            chunk_arr.append(chunk_data)
            return chunk_arr,chunk_counter                
        except Exception as e:
            self.logger.error(f"Error chunking file: {e}",exc_info=True)
            return [], chunk_counter
    
    def get_image_desc(self,chunk_content):
        try:
            image_file_path = chunk_content.split('\n')[0].replace("![Image](","").replace(")","")
            image_file_name = image_file_path.split("/")[-1]
            image_json_file_name = "_".join(image_file_name.split("_")[0:2]) + ".json"
            image_desc_folder_path = "/".join(image_file_path.split("/")[:-1]).replace("_artifacts","_image_desc")
            image_desc_file_path = os.path.join(image_desc_folder_path,image_json_file_name)
            if not os.path.exists(image_desc_file_path):
                self.logger.error(f"Image description file not found: {image_desc_file_path}")
                return None
            with open(image_desc_file_path,'r',encoding='utf-8') as f:
                image_desc = json.load(f)
            return image_desc
        except Exception as e:
            self.logger.error(f"Error reading image: {e}",exc_info=True)
            return None
    
    def get_image_id(self,chunk_content):
        try:
            image_file_path = chunk_content.split('\n')[0].replace("![Image](","").replace(")","")
            image_file_name = image_file_path.split("/")[-1]
            image_id = image_file_name.replace(".png","").split("_")[-1]
            return image_id
        except Exception as e:
            self.logger.error(f"Error getting image id: {e}",exc_info=True)
            return None
    