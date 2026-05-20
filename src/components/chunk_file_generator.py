import pymupdf
from docling.document_converter import DocumentConverter,PdfFormatOption
import fitz
import os
from config.log_config import LoggerConfig
from typing import Dict, List, Any   
from haystack import component
from haystack.dataclasses import ByteStream
#from docling_haystack.converter import DoclingConverter,ExportType 
from docling.datamodel.pipeline_options import PdfPipelineOptions, PictureDescriptionApiOptions,TableStructureOptions,TableFormerMode
from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.backend.docling_parse_v4_backend import DoclingParseDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling_core.types.doc import ImageRefMode
import concurrent.futures
import gc
from docling.datamodel.base_models import DocumentStream
from io import BytesIO


@component
class ChunkFileGenerator:

    def __init__(self, datasource_config: Any, chunkconfig: Any, docling_config: Any):
        self.logger = LoggerConfig().get_logger()
        self.datasource_config = datasource_config
        self.chunk_config = chunkconfig
        self.docling_config = docling_config

    def _generate_chunk_file(self, file_to_chunk_path: str):
        markdown_result = []
        try:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.accelerator_options = AcceleratorOptions(num_threads=1, device='cpu')
            pipeline_options.do_table_structure = self.docling_config.do_table_structure
            pipeline_options.do_picture_description = self.docling_config.do_picture_description
            pipeline_options.generate_picture_images = self.docling_config.generate_picture_images
            pipeline_options.do_ocr = self.docling_config.do_ocr
            pipeline_options.table_structure_options = TableStructureOptions(mode=TableFormerMode.ACCURATE)
            pipeline_options.enable_remote_services = self.docling_config.enable_remote_services
            pipeline_options.generate_page_images = self.docling_config.generate_page_images
            pipeline_options.images_scale = self.docling_config.images_scale
            pipeline_options.table_structure_options.do_cell_matching = self.docling_config.do_cell_matching
            
            doc_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options, backend=DoclingParseDocumentBackend)
                }
            )
            
            with pymupdf.open(file_to_chunk_path) as doc:
                for i in range(0, doc.page_count, self.chunk_config.page_chunk_split_length):
                    end_page = min(i + self.chunk_config.page_chunk_split_length, doc.page_count)
                    pdf_file_name = os.path.basename(file_to_chunk_path).replace('.pdf', '')
                    chunk_pdf_markdown_filepath = os.path.join(self.datasource_config.markdown_files_path, pdf_file_name, f"{pdf_file_name}_{i+1}_{end_page}.md")
                    os.makedirs(os.path.dirname(chunk_pdf_markdown_filepath), exist_ok=True)
                    
                    self.logger.info(f"Chunking process started for pdf file {pdf_file_name} from page {i+1} to {end_page}...")
                    
                    with pymupdf.open() as chunk_doc:
                        chunk_doc.insert_pdf(doc, from_page=i, to_page=end_page - 1)
                        chunk_pdf_bytes = chunk_doc.tobytes()
                    
                    # Convert only the chunked PDF bytes
                    stream = ByteStream(data=chunk_pdf_bytes, mime_type="application/pdf")
                    # We need a file-like object or path for doc_converter.convert if we're not using the internal converter
                    # Docling's DocumentConverter.convert can take a DocumentStream
                    
                    
                    doc_stream = DocumentStream(name=f"{pdf_file_name}_{i+1}_{end_page}.pdf", stream=BytesIO(chunk_pdf_bytes))
                    docling_conversion_doc = doc_converter.convert(doc_stream)
                    
                    pdf_docling_doc = docling_conversion_doc.document
                    pdf_docling_doc.save_as_markdown(chunk_pdf_markdown_filepath, image_mode=ImageRefMode.REFERENCED, page_break_placeholder="<!-- Page Break -->")
                    
                    markdown_result.append({
                        "markdown_file_path": chunk_pdf_markdown_filepath,
                        "markdown_file_name": os.path.basename(chunk_pdf_markdown_filepath),
                        "markdown_chunk_start_page": i + 1,
                        "markdown_chunk_end_page": end_page,
                        "pdf_file_name": pdf_file_name
                        
                    })
            
            gc.collect()
            return markdown_result
        except Exception as e:
            self.logger.error(f"Error generating chunk file: {e}", exc_info=True)
            return None

    @component.output_types(markdown_chunk_results=List[Dict[str, Any]])
    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        results = []
        try:
            files_to_chunk_path = [item['pdf_file_path'] for item in input['PDF File Details'] if 'Assembly' in item.get('pdf_type', '')]
            self.logger.info(f"PDF file paths to be split: {files_to_chunk_path}")
            
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.chunk_config.process_max_workers) as executor:
                future_to_file = {executor.submit(self._generate_chunk_file, path): path for path in files_to_chunk_path}
                for future in concurrent.futures.as_completed(future_to_file):
                    res = future.result()
                    if res:
                        results.extend(res)
            
            return {"markdown_chunk_results": results}
        except Exception as e:
            self.logger.error(f"Error generating chunk streams: {e}", exc_info=True)
            return {"markdown_chunk_results": []}
