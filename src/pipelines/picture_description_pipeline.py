from src.components.picture_description_vl import PictureDescription
from haystack import Pipeline
from config.config_settings import ConfigSettings

def create_picture_description_pipeline(settings:ConfigSettings):
    pipeline = Pipeline()
    pipeline.add_component("PictureDescription", PictureDescription(datasource_config=settings.datasource_config,ikea_config=settings.ikea_config,docling_config = settings.docling_config))
    return pipeline
