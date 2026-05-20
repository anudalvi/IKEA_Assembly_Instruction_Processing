'''str = 'lack-wall-shelf-unit-black-blue__AA-2699149-1-100_6_10.md'
print(str.replace('.md','').split("__")[1].split('_')[-1])
print(str.replace('.md','').split("__")[1].split('_')[-2])
str1 = '![Image](/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_6_10/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_6_10_artifacts/image_000004_1d85988a1765e7d2284a09cbd6a869acc24d7a49f59bff252e42468a54fc50c9.png)'
print('_'.join(str1.split('/')[-1].replace('.png)','').split('_')[0:2]))'''

import cv2
import numpy as np
from PIL import Image,ImageEnhance, ImageOps
import io
import os
from pathlib import Path
from falkordb import FalkorDB
import pandas as pd

def optimize_image_scaling(pil_img, target_dpi=150):
    """
    IKEA assembly images need balance between:
    - Text readability (part numbers, quantities)
    - Processing speed
    - Vision model input limits
    """
    width, height = pil_img.size
    
    # Calculate optimal size
    # IKEA instructions typically have small text (6-8 digit part numbers)
    # Need minimum 1024px width for OCR readability
    
    if width < 1024:
        # Upscale small images
        scale_factor = 1024 / width
        new_size = (1024, int(height * scale_factor))
        pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
    elif width > 2048:
        # Downscale very large images (slow processing)
        scale_factor = 2048 / width
        new_size = (2048, int(height * scale_factor))
        pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
    
    return pil_img

def enhance_image_for_ocr(image_file_path):
    pil_img = Image.open(image_file_path)
    try:
        
        # Step 1: Convert to RGB if needed
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        
        # Step 2: Optimize scaling (1024-2048px width)
        pil_img = optimize_image_scaling(pil_img, target_dpi=150)
        
        # Step 3: Convert to OpenCV for advanced processing
        img_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        # Step 4: Denoise (critical for PDF artifacts)
        img_cv = cv2.fastNlMeansDenoisingColored(
            img_cv, None, 
            h=10, hColor=10,  # Moderate denoising
            templateWindowSize=7, 
            searchWindowSize=21
        )
        
        # Step 5: Enhance contrast (IKEA diagrams are line drawings)
        # Use CLAHE for adaptive contrast enhancement
        lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced_l = clahe.apply(l)
        enhanced_lab = cv2.merge((enhanced_l, a, b))
        img_cv = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # Step 6: Sharpen edges (makes part numbers clearer)
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        img_cv = cv2.filter2D(img_cv, -1, kernel)
        
        # Step 7: Convert back to PIL
        enhanced_img = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        
        # Step 8: Final quality enhancement
        enhanced_img = ImageEnhance.Contrast(enhanced_img).enhance(1.3)
        enhanced_img = ImageEnhance.Sharpness(enhanced_img).enhance(1.2)
        enhanced_img.save("/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/enhanced_scale_image.png")
        
        return enhanced_img
        
    except Exception as e:
        print(f"Error enhancing image: {e}")
        return pil_img  # Return original on error



'''str1 = "/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100"
print(os.listdir(str1))
for json_file in Path(str1).rglob("*.json"):
    print(str(json_file.parent).split('/')[-1])'''
#enhance_image_for_ocr("/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_6_10/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_6_10_artifacts/image_000004_1d85988a1765e7d2284a09cbd6a869acc24d7a49f59bff252e42468a54fc50c9.png")
import json
import os
def index_data():
    falkordb = FalkorDB(host='localhost', port=6379)
    graph = falkordb.select_graph("IKEA_CatalogDB")
    result = graph.query("CALL db.indexes()")
    print(f"Header: {result.header}")
    for record in result.result_set:
        print(record)
    header_names = [h[1] for h in result.header]
    data = [list(record) for record in result.result_set]
    df_indexes = pd.DataFrame(data, columns=header_names)
    df_indexes.to_csv("indexes.csv", index=False)
    print(df_indexes[["label","properties"]])
    if 'MarkdownText' in df_indexes['label'].values:
        print("Index already exists")
    else:
        print("Index does not exist")

def read_json_file():
    with open("/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/graph_vector_metadata/image_guidance_step_ddl.json") as f:
        data = json.load(f)
    for node in data['nodes']:
        for k,v in node['mapping_details']['key_column'].items():
            print(k,v)


#index_data() 
read_json_file()
