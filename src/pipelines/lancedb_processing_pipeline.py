from src.components.lancedb_data_processing import LanceDBProcessing
from haystack import Pipeline
from config.config_settings import ConfigSettings

def create_lancedb_pipeline(settings:ConfigSettings):
    pipeline = Pipeline()
    pipeline.add_component("LanceDBProcessing", LanceDBProcessing(datasource_config=settings.datasource_config,ikea_config=settings.ikea_config,lancedb_config = settings.lancedb,embedding_chunk_text_config=settings.embedding_chunk_text_config))
    return pipeline