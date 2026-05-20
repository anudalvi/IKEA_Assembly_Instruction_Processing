from src.components.lancedb_data_ingestion_process import LanceDBDataIngestionProcess
from src.components.data_chunk_to_document_conversion import DataChunkToDocumentConversion
from haystack import Pipeline
from config.config_settings import ConfigSettings

def create_lancedb_ingestion_pipeline(settings:ConfigSettings):
    converter = DataChunkToDocumentConversion(datasource_config=settings.datasource_config)
    ingester = LanceDBDataIngestionProcess(datasource_config=settings.datasource_config,ikea_config=settings.ikea_config,lancedb_config = settings.lancedb,doc_converter=converter)
    pipeline = Pipeline()
    pipeline.add_component("LanceDBDataIngestionProcess", ingester)
    return pipeline