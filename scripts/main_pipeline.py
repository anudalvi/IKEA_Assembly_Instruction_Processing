from torch import device
from sentence_transformers import SentenceTransformer
from haystack import AsyncPipeline
from haystack.document_stores.in_memory import InMemoryDocumentStore
from src.pipelines.web_scrapping_pipeline import create_web_scrapping_pipeline
from src.pipelines.system_user_prompts_generation import create_vl_model_client_pipeline
from src.pipelines.document_chunk_generation import create_document_chunk_pipeline
from src.pipelines.chunk_data_processing import create_chunk_data_processing_pipeline
from src.pipelines.lancedb_processing_pipeline import create_lancedb_pipeline 
from src.pipelines.lancedb_data_ingestion import create_lancedb_ingestion_pipeline
from config.config_settings import ConfigSettings
from config.log_config import LoggerConfig
import json
import asyncio
from src.pipelines.picture_description_pipeline import create_picture_description_pipeline

async def main():
    headers = {
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language":"en-US,en;q=0.9",
            "Sec-Fetch-Dest":"document",
            "Sec-Fetch-Mode":"navigate",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0",
            "Cookie":"guest=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImVxSFFLR3duR3hfV3dJZkx0RGpaeDA5MTUzS2xSam5fVE1nVUlMYlJ5RncifQ.eyJpc3MiOiJodHRwczovL2FwaS5pbmdrYS5pa2VhLmNvbS9ndWVzdCIsInN1YiI6IjZhODgzMDJlLTc1NjQtNDcxNi05YzNjLWE2YTNmYzlkNTFiYyIsInJldGFpbFVuaXQiOiJubCIsImlhdCI6MTc3MjQwNjgyMiwiZXhwIjoxNzc0OTk4ODIyfQ.PRoyk_UF_XH5QAdJl07t7eL5uuQPfoauDs2tZd2LHlqqcNVGJGRGVdIpbXZ_Y0H-raS1_KG70KksGwg0fL5yKazhnW5OhLW2niOjj-mkFY-bPWEyCHV9e2a-4_9rOLkoJG-cLT2HGGIv5f0bVEUc6KpC-HMJZgHZ2DGFBuYJID0; ikea_geo=NL; _cs_mk_ga=0.4831464114045395_1772408086967; FPGSID=1.1772408087.1772408087.G-S4EX53B760.uP0KiX7UO841fYn2ajMqWA; _rdt_uuid=1771803493114.a508122e-9754-4932-9c37-a8390a988dbf; tfpsi=5ec8ed3a-d445-40d8-967f-daa195df57ed; _uetsid=3d097da015c711f19aa3fd4b495c318f; _uetvid=8e27d6c0104711f186952d9d53d01d19"
        }
    settings = ConfigSettings()
    logger_config = LoggerConfig()
    logger = logger_config.get_logger()
    logger.info("Starting web scrapping pipeline")
    with open(settings.ikea_config.web_scrapping_config_file_path, 'r') as f:
        web_scrapping_config = json.load(f)
    # Save Embedding Model to local machine
    model = SentenceTransformer(settings.lancedb.embedding_model,device='cpu')
    model.save(str(settings.lancedb.embedding_model_save_path))
    logger.info(f"Embedding model saved to {settings.lancedb.embedding_model_save_path}")
    web_scrapping_pipeline = create_web_scrapping_pipeline(settings,headers,web_scrapping_config)
    results = await web_scrapping_pipeline.run_async({'parse_product_details_and_manual_download':{}})
    logger.info(f"Web scrapping pipeline completed: {results}")
    #vl_model_client_pipeline = create_vl_model_client_pipeline(settings)
    for input in results['parse_product_details_and_manual_download']['product_details_and_manual_download']:
        '''output = vl_model_client_pipeline.run({'UserPromptGeneration':{'result':input},'SystemPromptGeneration':{'result':input}})
        #logger.info(f"VL model client pipeline completed for product :\n {output}")
        #logger.info(f"VL model client pipeline completed for product {input['Product Details']['product_name']}:\n User Prompt: {output['UserPromptGeneration']['user_prompt']}\n System Prompt: {output['SystemPromptGeneration']['system_prompt']}")
        chunk_file_generator_pipeline = create_document_chunk_pipeline(settings)
        chunk_file_results = chunk_file_generator_pipeline.run({'ChunkFileGenerator':{'input':input}})
        logger.info(f"Chunk file generator pipeline completed: {chunk_file_results}")  
        picture_description_pipeline = create_picture_description_pipeline(settings)
        picture_description_results = picture_description_pipeline.run({'PictureDescription':{'input':input,'system_prompt':output['SystemPromptGeneration']['system_prompt'],
                                                                                                'user_prompt':output['UserPromptGeneration']['user_prompt'], 
                                                                                                'chunk_file_results':chunk_file_results['ChunkFileGenerator']['markdown_chunk_results']}})
        logger.info(f"Picture description pipeline completed: {picture_description_results}")''' 
        chunk_data_processing_pipeline = create_chunk_data_processing_pipeline(settings)
        chunk_data_processing_results = chunk_data_processing_pipeline.run({'ChunkDataProcessor':{'input':input}})
        logger.info(f"Chunk data processing pipeline completed: {chunk_data_processing_results}")
        lancedb_pipeline = create_lancedb_pipeline(settings)
        lancedb_results = lancedb_pipeline.run({'LanceDBProcessing':{'input':input,'assembly_instruction_chunk_data':chunk_data_processing_results['ChunkDataProcessor']}}) 
        logger.info(f"LanceDB processing pipeline completed: {lancedb_results}")
        lancedb_ingestion_pipeline = create_lancedb_ingestion_pipeline(settings)
        lancedb_ingestion_results = lancedb_ingestion_pipeline.run({'LanceDBDataIngestionProcess':{'input':input,'table_data':lancedb_results['LanceDBProcessing']['table_data']}}) 
        logger.info(f"LanceDB ingestion pipeline completed: {lancedb_ingestion_results}")

if __name__ == "__main__":
    asyncio.run(main())