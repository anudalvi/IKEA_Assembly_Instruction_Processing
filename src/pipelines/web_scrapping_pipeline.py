from haystack import AsyncPipeline,Pipeline
from config.config_settings import ConfigSettings
from config.log_config import LoggerConfig
from src.components.parse_product_category_links import ParseProductCategoryLinks
from src.components.parse_product_links import ParseProductLinks
from src.components.parse_product_details_and_manual_download import ParseProductDetailsAndManualDownload


def create_web_scrapping_pipeline(settings:ConfigSettings,headers:dict,web_scrapping_config:dict):
    pipeline = AsyncPipeline()
    parse_product_category_links = ParseProductCategoryLinks(web_scrapping_config,headers,ikea_config = settings.ikea_config)
    pipeline.add_component("parse_product_category_links", parse_product_category_links)
    pipeline.add_component("parse_product_links", ParseProductLinks(web_scrapping_config,headers,ikea_config = settings.ikea_config,datasource_config = settings.datasource_config))
    pipeline.add_component("parse_product_details_and_manual_download", ParseProductDetailsAndManualDownload(web_scrapping_config,headers,ikea_config = settings.ikea_config,datasource_config = settings.datasource_config))
    pipeline.connect("parse_product_category_links","parse_product_links")
    pipeline.connect("parse_product_links","parse_product_details_and_manual_download")
    return pipeline
    

