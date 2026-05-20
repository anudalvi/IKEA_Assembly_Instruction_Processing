from src.components.chunk_data_process import ChunkDataProcessor
from haystack import Pipeline
from config.config_settings import ConfigSettings

def create_chunk_data_processing_pipeline(settings:ConfigSettings):
    pipeline = Pipeline()
    pipeline.add_component("ChunkDataProcessor", ChunkDataProcessor(datasource_config=settings.datasource_config,ikea_config=settings.ikea_config,markdown_chunk_cfg = settings.markdown_chunk_config))
    return pipeline
