from haystack import Pipeline
from config.config_settings import ConfigSettings
from config.log_config import LoggerConfig
from src.components.system_prompt_generation import SystemPromptGeneration
from src.components.user_prompt_generation import UserPromptGeneration


def create_vl_model_client_pipeline(settings:ConfigSettings):
    pipeline = Pipeline()
    pipeline.add_component("UserPromptGeneration", UserPromptGeneration(datasource_config = settings.datasource_config))
    pipeline.add_component("SystemPromptGeneration", SystemPromptGeneration(datasource_config = settings.datasource_config))
    return pipeline