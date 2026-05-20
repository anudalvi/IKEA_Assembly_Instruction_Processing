from src.components.chunk_file_generator import ChunkFileGenerator
from haystack import Pipeline
from config.config_settings import ConfigSettings

def create_document_chunk_pipeline(settings:ConfigSettings):
    pipeline = Pipeline()
    pipeline.add_component("ChunkFileGenerator", ChunkFileGenerator(datasource_config=settings.datasource_config,chunkconfig=settings.chunkconfig,docling_config=settings.docling_config))
    return pipeline
