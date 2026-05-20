import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.docling_processing import DoclingProcessing
from config.config_settings import ConfigSettings
from config.log_config import LoggerConfig

async def test_chunk_processing():
    settings = ConfigSettings()
    logger = LoggerConfig().get_logger()
    
    # Sample prompts (simplified)
    system_prompt = "You are an IKEA assembly assistant. Describe the image."
    user_prompt = "Analyze the image and provide details."
    
    dp = DoclingProcessing(logger=logger, settings=settings, system_prompt=system_prompt, user_prompt=user_prompt)
    
    # Path to sample split PDF
    file_name_dir = "kallax-shelving-unit-white__AA-1055145-11-100"
    chunk_pdf_file_path = os.path.join(settings.datasource_config.pdf_file_split_folder, file_name_dir, f"{file_name_dir}_1_5.pdf")
    chunk_pdf_file_name = f"{file_name_dir}_1_5"
    
    if not os.path.exists(chunk_pdf_file_path):
        print(f"Error: PDF chunk not found at {chunk_pdf_file_path}")
        return

    print(f"Starting processing for {chunk_pdf_file_name}...")
    result = await dp.document_processing_extract(file_name_dir, chunk_pdf_file_path, chunk_pdf_file_name)
    print("Processing result:", result)

if __name__ == "__main__":
    asyncio.run(test_chunk_processing())
