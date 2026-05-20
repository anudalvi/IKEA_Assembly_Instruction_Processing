from src.tools.transformation_functions import TRANSFORM_REGISTRY
from docling.datamodel.settings import settings
from haystack import component
from config.log_config import LoggerConfig
from pathlib import Path
import os
import re
import json
import uuid
from typing import Any, Dict, Optional
from src.tools.transformation_functions import *

@component
class LanceDBProcessing:
    
    def __init__(self,  datasource_config,ikea_config, lancedb_config,embedding_chunk_text_config):
        self.datasource_config = datasource_config
        self.ikea_config = ikea_config
        self.lancedb_config = lancedb_config
        self.embedding_chunk_text_config = embedding_chunk_text_config  #Changed the logic to get the embedding text from the column mapping json file
        self.logger = LoggerConfig().get_logger()

    @component.output_types(table_data=Optional[Dict[str, Any]])
    def run(self, input: Any, assembly_instruction_chunk_data: Any) -> Dict[str, Any]:
        table_data = {}
        try:
            self.logger.info(f"Input Data under Processing: \n{input}")
            column_mapping_cfg = self.__get_column_mapping_details()
            if column_mapping_cfg is None:
                self.logger.error("Column mapping configuration could not be loaded.")
                return {"table_data": None}
            for column_map_cfg in column_mapping_cfg['extraction_pipeline']:
                records = []
                context_data = self.__get_context_data(column_map_cfg['source_dataset'],input,assembly_instruction_chunk_data)
                if context_data is None:
                    self.logger.error(f"Could not retrieve context data for dataset: {column_map_cfg['source_dataset']}")
                    continue
                self.logger.info(f"Length of Context Data: \n{len(context_data)}")
                if 'instruction_pdf_file_arr' in column_map_cfg:
                    field_data = context_data[column_map_cfg['instruction_pdf_file_arr']['source_column']]
                    #self.logger.info(f"Field Data: \n{field_data}")
                    if 'source_data_filter' in column_map_cfg['instruction_pdf_file_arr']:
                        instruction_pdf_file_list = self.__apply_transforms(field_data,column_map_cfg['instruction_pdf_file_arr']['source_data_filter'])
                        self.logger.info(f"Source Data Filter Output: \n{instruction_pdf_file_list}")
                        if instruction_pdf_file_list is None:
                            continue
                        for instruction_pdf_file in instruction_pdf_file_list:
                            data_row = self.__get_table_data_row(column_map_cfg,context_data,instruction_pdf_file,input)
                            if "embedding_columns_config" in column_map_cfg:
                                embed_column_config = column_map_cfg['embedding_columns_config']
                                if data_row is not None:
                                    data_embed_text = self.__add_embedding_data_text(data_row,embed_column_config)
                                    data_row[embed_column_config["embedding_text_column"]] = data_embed_text
                                    data_row["language"] = self.ikea_config.language    
                            records.append(data_row)
                if column_map_cfg["source_dataset"] == "_context.chunk_data":
                    for pdf_file_name,chunk_data in assembly_instruction_chunk_data.items():
                        for chunk in chunk_data:
                            data_row = self.__get_table_data_row(column_map_cfg,chunk,pdf_file_name,input)
                            self.logger.info(f"Chunk data row: \n {data_row}")
                            if "embedding_columns_config" in column_map_cfg:
                                embed_column_config = column_map_cfg['embedding_columns_config']
                                if data_row is not None:
                                    data_embed_text = self.__add_embedding_data_text(data_row,embed_column_config)
                                    data_row[embed_column_config["embedding_text_column"]] = data_embed_text
                                    data_row["language"] = self.ikea_config.language
                                    #self.logger.info(f"Data Embed Text: \n {data_row[embed_column_config['embedding_text_column']]}")
                            records.append(data_row)
                table_data[column_map_cfg['table_name']] = records
            self.logger.info(f"Tables Data: \n {len(table_data)}")
            return {"table_data": table_data}
        except Exception as e:
            self.logger.error(f"Error processing input: {e}",exc_info=True)
            return {"table_data": None}

    def __add_embedding_data_text(self,data_row,embed_column_config):
        embed_text_str = ""
        class_type = ''
        try:
            if "chunk_type_cases" in embed_column_config:
                for key,value in embed_column_config["chunk_type_cases"].items():
                    if data_row[embed_column_config["embedding_condition_column"]] == key:
                        for class_type, column_list in value["embedding_config_cases"].items():
                            class_type = '' if class_type == "is_blank" else class_type
                            if data_row[value["embedding_condition_column"]] == class_type:
                                embed_text_str = ", ".join(map(lambda x:f"{x.replace('_',' ')}: {data_row[x]}" if x in embed_column_config["special_text_format_columns"] else data_row[x],filter(lambda x:len(data_row[x]) > 0,column_list)))
            else:
                if "special_text_format_columns" in embed_column_config:
                    embed_text_str = ", ".join(f"{x.replace('_',' ')}: {data_row[x]}" for x in embed_column_config["special_text_format_columns"] if len(data_row[x])>0 and data_row[x] is not None)
                elif "embedding_columns" in embed_column_config:
                    embed_text_str = ", ".join(f"{data_row[x]}" for x in embed_column_config["embedding_columns"] if len(data_row[x])>0 and data_row[x] is not None)
                else:
                    self.logger.info(f"No embedding columns found in embed_column_config: {embed_column_config}")
            return embed_text_str
        except Exception as e: 
            self.logger.error(f"Error adding embedding data text for chunk type {data_row[embed_column_config['embedding_condition_column']] if 'embedding_condition_column' in embed_column_config else embed_column_config['embedding_text_column']} and class type {class_type if class_type != '' else 'N/A'}: {e}",exc_info=True)
            return None 

    def __get_column_mapping_details(self):
        try:
            column_mapping_cfg = {}
            with open(self.datasource_config.table_source_column_mapping_filepath, 'r') as f:
                column_mapping_cfg = json.load(f)
            return column_mapping_cfg
        except Exception as e:
            self.logger.error(f"Error getting column mapping details: {e}",exc_info=True)
            return None 

    def __get_context_data(self,source_dataset,input,assembly_instruction_chunk_data):
        try:
            if source_dataset == '_context.chunk_data':
                return assembly_instruction_chunk_data
            elif source_dataset == '_context.input':
                return input
            else:
                self.logger.error(f"Unknown source dataset: {source_dataset}",exc_info=True)
                return None 
        except Exception as e:
            self.logger.error(f"Error getting context data: {e}",exc_info=True)
            return None 

    def __apply_transforms(self,data,transforms,context=None):
        try:
            value = data
            for steps in transforms:
                fn_name = steps.get("name")
                args = steps.get("args",{})
                if fn_name in TRANSFORM_REGISTRY:
                    fn = TRANSFORM_REGISTRY[fn_name]
                    value = fn(field=value,args=args,context=context)
                    #self.logger.info(f"After Field:{value}")
                else:
                    self.logger.error(f"Unknown filter function: {fn_name}",exc_info=True)
                    return None 
            return value
        except Exception as e:
            self.logger.error(f"Error filtering source data: {e}",exc_info=True)
            return None 

    def __get_table_data_row(self,column_map_cfg,context_data,instruction_pdf_file,input):
        data_row = {}
        fld = ''
        try:
            print(f"Getting fields for file: {instruction_pdf_file}")
            for field in column_map_cfg['fields']:
                fld = field
                target_column = field['target_column']
                source_column = field['source_column'] if 'source_column' in field else None
                source_data = None
                if source_column in context_data:
                    source_data = context_data[source_column]
                elif source_column == "pdf_file_name":
                    source_data = instruction_pdf_file
                elif source_column in input:
                    source_data = input[source_column]
                if 'transform' in field:
                    target_value = self.__apply_transforms(source_data,field['transform'],context_data)
                else:
                    target_value = source_data
                data_row[target_column] = target_value
            return data_row
        except Exception as e:
            self.logger.error(f"Error getting table data row for file: {instruction_pdf_file} and field: {fld}: {e}",exc_info=True)
            return None 

    