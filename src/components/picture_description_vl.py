from haystack.dataclasses import ChatMessage, TextContent, ImageContent
from typing import Dict, List, Any
from haystack import component
from config.log_config import LoggerConfig
from PIL import Image, ImageEnhance
import os
import io
from haystack.dataclasses import ByteStream
import base64
from haystack_integrations.components.generators.ollama import OllamaChatGenerator  # type: ignore
import json

@component
class PictureDescription:
    def __init__(self, datasource_config: Any, ikea_config: Any, docling_config: Any):
        self.logger = LoggerConfig().get_logger()
        self.datasource_config = datasource_config
        self.ikea_config = ikea_config
        self.docling_config = docling_config

    def __enhance_image_for_ocr(self, image: Image.Image, image_path: str) -> ByteStream:
        try:
            self.logger.info(f"Enhancing image {image_path} for OCR...")
            # Convert to grayscale
            image = image.convert("L")
            # Apply contrast enhancement
            image = ImageEnhance.Contrast(image).enhance(2.0)
            # Apply sharpening
            image = ImageEnhance.Sharpness(image).enhance(2.0)
            # Apply brightness adjustment
            image = ImageEnhance.Brightness(image).enhance(1.5)
            image.save(image_path)
            self.logger.info(f"Image {image_path} enhanced successfully.")
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            return ByteStream(data = buffer.getvalue(), mime_type="image/png")
        except Exception as e:
            self.logger.error(f"Error enhancing image {image_path}: {e}", exc_info=True)
            return None

    @component.output_types(picture_description_results=List[Dict[str, Any]])
    def run(self, input: Dict[str, Any], system_prompt: str, user_prompt: str, chunk_file_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        picture_description_results = []
        try:
            self.logger.info(f"Picture description pipeline started for pdf file {input.get('pdf_file_name', 'unknown')}...")
            '''print("System Prompt: ", system_prompt)
            print("User Prompt: ", user_prompt)'''
            for item in chunk_file_results:
                artifacts_path = item['markdown_file_path'].replace('.md', '_artifacts')
                if os.path.exists(artifacts_path):
                    for root, dirs, files in os.walk(artifacts_path):
                        for file in files:
                            if file.endswith(".png"):
                                image_path = os.path.join(root, file)
                                self.logger.info(f"Processing image: {image_path}") 
                                image = Image.open(image_path)
                                image_byte_stream = self.__enhance_image_for_ocr(image, image_path)
                                output_response = self.__generate_picture_description(image_byte_stream, system_prompt, user_prompt,image_path)
                                response_msg = output_response["replies"][0]
                                picture_description_response = response_msg._content[0].text
                                self.logger.info(f"Response Text: {picture_description_response}")
                                response_meta_details =  {
                                    "model_name":response_msg._meta["model"],
                                    "total_duration":response_msg._meta["total_duration"],
                                    "load_duration":response_msg._meta["load_duration"],
                                    "prompt_eval_duration":response_msg._meta["prompt_eval_duration"],
                                    "eval_duration":response_msg._meta["eval_duration"],
                                    "prompt_token":response_msg._meta["usage"]["prompt_tokens"],
                                    "completion_token":response_msg._meta["usage"]["completion_tokens"],
                                    "total_token":response_msg._meta["usage"]["total_tokens"]
                                }
                                if len(picture_description_response) > 0:
                                    image_file_details = self.__save_picture_description(picture_description_response, image_path)
                                    self.logger.info(f"Picture description for image {file}: {image_file_details}")
                                    image_description_details = {
                                        'markdown_file_path': item['markdown_file_path'],
                                        **image_file_details,
                                        "response_meta_details": response_meta_details 
                                    }
                                    picture_description_results.append(image_description_details)
            return {"picture_description_results": picture_description_results}
        except Exception as e:
            self.logger.error(f"Error generating picture description: {e}", exc_info=True)
            return {"picture_description_results": []}
    

    def __generate_picture_description(self, image_byte_stream: ByteStream, system_prompt: str, user_prompt: str, image_path: str) -> str:
        try:
            self.logger.info(f"Generating picture description for image...")
            generator = OllamaChatGenerator(model = self.docling_config.vision_model_name,
            url = self.ikea_config.ollama_url,
            generation_kwargs={"temperature": 0.7,
            "num_predict": 30000,
            "thinking": False
            })
            messages = [ChatMessage.from_system(system_prompt), ChatMessage.from_user(
                content_parts = [
                    TextContent(text=user_prompt),
                    ImageContent.from_file_path(image_path)
                ]
            )]
            response = generator.run(messages=messages)
            res_msg = response["replies"][0]
            res_text = res_msg._content[0].text
            #return res_text
            return response
        except Exception as e:
            self.logger.error(f"Error generating picture description: {e}", exc_info=True)
            return ""

    def __save_picture_description(self, picture_description: str, image_path: str):
        try:
            image_file_name = image_path.split('/')[-1]
            artifact_folder_name = image_path.split('/')[-2]
            chunk_folder_path = '/'.join(image_path.split('/')[:-2])
            os.makedirs(os.path.join(chunk_folder_path, artifact_folder_name.replace('_artifacts', '_image_desc')), exist_ok=True)
            image_file_name_arr = image_file_name.split('_')
            img_json_file_name = '_'.join(image_file_name_arr[0:2]) + '.json'
            image_json_file_path = os.path.join(chunk_folder_path, artifact_folder_name.replace('_artifacts', '_image_desc'), img_json_file_name)
            self.logger.info(f"Saving picture description for image {image_file_name}...")
            start_idx = picture_description.find('{')
            end_idx = picture_description.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                clean_json_str = picture_description[start_idx:end_idx+1].strip()
                try:
                    # Validate JSON content
                    json_data = json.loads(clean_json_str)
                    with open(image_json_file_path,"w",encoding="utf-8") as f:
                        json.dump(json_data, f, indent=4)
                    self.logger.info(f"Successfully saved validated JSON for {image_file_name}")
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON validation failed for {image_file_name}: {e}")
                    self.logger.error(f"Attempted to parse: {clean_json_str}")
                    return {"image_json_path": "",
                            "image_json_file_name": "",
                            "image_file_size": 0,
                            "image_desc_status":"FAILED"}
            else:
                self.logger.warning(f"No valid JSON object delimiters found in response for {image_file_name}")
                return {"image_json_path": "",
                        "image_json_file_name": "",
                        "image_file_size": 0,
                        "image_desc_status":"FAILED"}
            return {"image_json_path": image_json_file_path,
                    "image_json_file_name": img_json_file_name,
                    "image_file_size": os.path.getsize(image_json_file_path),
                    "image_desc_status":"SUCCESS"}
        except Exception as e:
            self.logger.error(f"Error saving picture description for image {image_path}: {e}", exc_info=True)
            return {"image_json_path": "",
                    "image_json_file_name": "",
                    "image_file_size": 0}
    