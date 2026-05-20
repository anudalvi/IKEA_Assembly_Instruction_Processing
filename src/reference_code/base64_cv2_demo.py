import io
import base64
import cv2 as cv
import numpy as np
#from docling.document import PictureItem

def picture_item_to_base64(file_path,preprocess:bool = True,rescale:float = 2.0) -> str:
    """
    Convert Docling PictureItem to base64 string for Ollama.
    
    Args:
        picture_item: Docling PictureItem object
        preprocess: If True, apply binary threshold + dilate for line drawings
    
    Returns:
        Base64 encoded image string (without data:image prefix)
    """
    # 1. Extract image from PictureItem
    # Docling stores image as PIL.Image in picture_item.image
    pic_item = cv.imread(file_path)
    
    # 2. Convert PIL to OpenCV format
    img_array = np.array(pic_item)
    
    # Convert RGB to BGR for OpenCV (if color)
    if len(img_array.shape) == 3:
        img = cv.cvtColor(img_array, cv.COLOR_RGB2BGR)
    else:
        img = img_array
    
    # Convert to grayscale for line drawings
    if len(img.shape) == 3:
        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    
    # 3. Preprocess for assembly diagrams (optional but recommended)
    if preprocess:
        # Binary threshold: make lines BLACK, background WHITE
        _, binary = cv.threshold(img, 200, 255, cv.THRESH_BINARY)
        '''binary = cv.bitwise_not(binary)
        _, binary = cv.threshold(binary, 50, 255, cv.THRESH_BINARY)
        binary = cv.bitwise_not(binary)'''
        kernel_sharp = np.array([[-1, -1, -1],
                                  [-1,  9, -1],
                                  [-1, -1, -1]])
        img = cv.filter2D(binary, -1, kernel_sharp)
        
        # Clip values to valid range
        img = np.clip(img, 0, 255).astype(np.uint8)
        
        # Final clean threshold after sharpening
        _, img = cv.threshold(img, 128, 255, cv.THRESH_BINARY)
        # Dilate: thicken thin lines for small models
        kernel = np.ones((1, 1), np.uint8)
        img = cv.dilate(img, kernel, iterations=1)
    
    if rescale != 1.0:
        h, w = img.shape
        new_w, new_h = int(w * rescale), int(h * rescale)
        
        # Use INTER_NEAREST for pixel-art/line drawings (preserves sharp edges)
        # Use INTER_LINEAR for photos/smooth images
        img = cv.resize(img, (new_w, new_h), interpolation=cv.INTER_NEAREST)
    
    # 4. Encode to PNG bytes
    _, buffer = cv.imencode('.png', img)
    png_bytes = buffer.tobytes()
    
    # 5. Convert to base64 (Ollama wants raw base64, no prefix)
    base64_str = base64.b64encode(png_bytes).decode('utf-8')

    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]
    
    # Decode base64 to bytes
    img_bytes = base64.b64decode(base64_str)
    
    # Convert bytes to numpy array
    nparr = np.frombuffer(img_bytes, np.uint8)
    
    # Decode to image
    img = cv.imdecode(nparr, cv.IMREAD_UNCHANGED)
    
    output_path = "/home/anu/RAG_AI_ML_Projects/demo_enhanced_img.png"
    # Save as PNG
    cv.imwrite(output_path, img)
    
    print(f"✓ Saved: {output_path}")
    print(f"  Dimensions: {img.shape}")
    
    return True



b64 = picture_item_to_base64("/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_6_10/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_6_10_artifacts/image_000000_feaa5d1172b55ee52d20965d3cb4221fb910de345da4335ca115bf56e2e29e35.png",
    preprocess=True,
    rescale=2.0)
