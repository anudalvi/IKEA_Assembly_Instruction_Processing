from docling.datamodel.pipeline_options import PictureDescriptionVlmEngineOptions
import asyncio
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, PictureDescriptionApiOptions,TableStructureOptions,TableFormerMode,PictureDescriptionVlmEngineOptions
from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend, DoclingParseDocumentBackend
from docling.datamodel.base_models import InputFormat, BoundingBox
from docling_core.types.doc import DocItemLabel, PictureItem, PageItem,TextItem, ImageRefMode
from config.log_config import LoggerConfig
from config.config_settings import ConfigSettings
from docling.datamodel.vlm_engine_options import ApiVlmEngineOptions, VlmEngineType
from docling.datamodel.pipeline_options import PipelineOptions
import os
import time


class DoclingProc():
    def __init__(self,logger:LoggerConfig=None ,settings: ConfigSettings = None,system_prompt:str=None,user_prompt:str=None):
        self.logger = LoggerConfig().get_logger() if logger is None else logger
        self.settings = ConfigSettings() if settings is None else settings
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.converter = self.__init_converter()
    

    def __init_converter(self):
        pipeline_options = self.__init_pipeline_options()
        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options, backend=DoclingParseDocumentBackend)
            }
        )
    
    def __init_pipeline_options(self):
        # Prepare custom params for VLM
        custom_params = {
            "model": self.settings.docling_config.vision_model_name,
            "system": f"{self.system_prompt}\n\n{self.user_prompt}",
            "temperature": 0.1,
            "top_p": 0.9,
        }
        pipeline_options = PdfPipelineOptions()
        pipeline_options.accelerator_options = AcceleratorOptions(num_threads=1, device='cpu')
        pipeline_options.do_table_structure = self.settings.docling_config.do_table_structure
        pipeline_options.do_picture_description = self.settings.docling_config.do_picture_description
        pipeline_options.generate_picture_images = self.settings.docling_config.generate_picture_images
        pipeline_options.do_ocr = self.settings.docling_config.do_ocr
        pipeline_options.table_structure_options=TableStructureOptions(mode=TableFormerMode.ACCURATE)
        pipeline_options.enable_remote_services=self.settings.docling_config.enable_remote_services
        pipeline_options.generate_page_images = self.settings.docling_config.generate_page_images
        pipeline_options.images_scale = self.settings.docling_config.images_scale
        pipeline_options.table_structure_options.do_cell_matching = self.settings.docling_config.do_cell_matching
        # Configure VLM options
        vlm_engine_options = ApiVlmEngineOptions(
            runtime_type=VlmEngineType.API_OLLAMA,
            url=self.settings.ikea_config.ollama_url,
            params=custom_params,
            timeout = 120
        )
        
        # Use from_preset to initialize picture description options
        picture_desc_options = PictureDescriptionVlmEngineOptions.from_preset(
            "qwen", 
            engine_options=vlm_engine_options
        )
        pipeline_options.picture_description_options = picture_desc_options
        return pipeline_options
    
    def document_processing_extract(self,chunk_pdf_file_path: str,chunk_pdf_file_name:str):
        try:
            start_time = time.time()
            self.logger.info(f"Document processing initiated for PDF File Name: {chunk_pdf_file_path}")
            result = self.converter.convert(chunk_pdf_file_path)
            doc=result.document
            for element, _level in doc.iterate_items():
                if isinstance(element, PictureItem):
                    self.logger.info(
                        f"Picture {element.self_ref}\n"
                        f"Caption: {element.caption_text(doc)}\n"
                        f"Meta: {element.meta}\n"
                    ) 
            chunk_pdf_markdown_filepath = os.path.join(self.settings.datasource_config.markdown_files_path,f"{chunk_pdf_file_name}.md")
            doc.save_as_markdown(chunk_pdf_markdown_filepath,image_mode=ImageRefMode.REFERENCED,page_break_placeholder="<!-- Page Break -->")
            self.logger.info(f"Duration:{time.time()-start_time}") 
        except Exception as e:  
            self.logger.error(f"Error in document_processing_extract: {e}", exc_info=True)
