import requests
from haystack import component
from config.log_config import LoggerConfig
from typing import Dict, List, Any   
import pandas as pd
import os   
import asyncio
from playwright.async_api import async_playwright
import json

@component
class UserPromptGeneration:
    def __init__(self,datasource_config:dict):
        self.logger = LoggerConfig().get_logger()
        self.datasource_config = datasource_config
    
    @component.output_types(user_prompt=str)
    def run(self, result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with open(self.datasource_config.user_prompt_filepath, 'r') as f:
                user_prompt = f.read()
            self.logger.info(f"User Prompt: {user_prompt[0:20]}")
            return {"user_prompt":user_prompt}
        except Exception as e:
            self.logger.error(f"Error generating user prompt: {e}", exc_info=True)
            return {"user_prompt": ""}