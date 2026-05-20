import asyncio
import json
import os
import sys
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.docling_processing import DoclingProcessing
from config.config_settings import ConfigSettings
from config.log_config import LoggerConfig

async def test_verification():
    # Mock settings and logger
    settings = ConfigSettings()
    logger = LoggerConfig().get_logger()
    
    # Mock DocumentConverter to avoid PDF processing
    with patch('src.docling_processing.DocumentConverter') as MockConverter:
        mock_converter_inst = MockConverter.return_value
        
        # Instantiate DoclingProcessing
        dp = DoclingProcessing(logger=logger, settings=settings, system_prompt="Test System", user_prompt="Test User")
        
        # Test case 1: Ollama returns JSON with 'safety_alert' (which we found in prompt)
        mock_response = MagicMock()
        mock_response.message.content = '{"classification": "Assembly", "safety_alert": "Warning!", "step_name": "Test Step", "action": "1. Do stuff", "parts": [], "tools": [], "difficulty": "Easy"}'
        
        with patch('ollama.chat', return_value=mock_response):
            # We need to mock the PDF and image processing parts of document_processing_extract
            # or just test the logic inside it.
            # Let's test the extraction logic directly if possible, or mock the iterate_items.
            
            # Since we want to verify 'document_processing_extract', let's mock the 'result' from converter
            mock_result = MagicMock()
            mock_element = MagicMock()
            from docling_core.types.doc import PictureItem
            # We can't easily mock isinstance(element, PictureItem) if it's imported in the file
            # but we can try to mock the iterate_items return value.
            
            # For simplicity, let's just use a dedicated test for the picture_description_extraction and the JSON saving logic
            print("\n--- Testing JSON extraction and field mismatch ---")
            
            picture_description = mock_response.message.content
            start_idx = picture_description.find('{')
            end_idx = picture_description.rfind('}')
            clean_json = picture_description[start_idx:end_idx+1].strip()
            
            print(f"Extracted JSON: {clean_json}")
            
            data = json.loads(clean_json)
            if 'safety_alert' in data and 'safety' not in data:
                print("ISSUE DETECTED: Found 'safety_alert' instead of 'safety' field!")
            
            # Test case 2: Malformed JSON (unbalanced braces)
            mock_response_malformed = '{"classification": "Assembly", "broken": '
            print(f"\n--- Testing malformed JSON logic ---")
            print(f"Input: {mock_response_malformed}")
            start_idx = mock_response_malformed.find('{')
            end_idx = mock_response_malformed.rfind('}')
            if start_idx != -1 and end_idx != -1:
                clean_json_malformed = mock_response_malformed[start_idx:end_idx+1].strip()
                print(f"Extracted string: '{clean_json_malformed}'")
                try:
                    json.loads(clean_json_malformed)
                except json.JSONDecodeError as e:
                    print(f"JSON persistence would fail/save invalid JSON: {e}")

if __name__ == "__main__":
    asyncio.run(test_verification())
