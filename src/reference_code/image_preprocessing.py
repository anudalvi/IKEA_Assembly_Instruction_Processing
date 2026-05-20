import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import io
from typing import Tuple, Optional


#logger = logging.getLogger(__name__)

class IKEAImagePreprocessor:
    """
    Specialized preprocessor for IKEA assembly instruction images.
    Optimized for: line drawings, part numbers, symbols, multi-language text
    """
    
    def __init__(self, 
                 target_width: int = 1536,
                 enhance_contrast: bool = True,
                 denoise_strength: int = 8,
                 sharpen: bool = True,
                 clahe_clip: float = 2.0,
                 preserve_color: bool = False):
        """
        Initialize preprocessor with IKEA-specific defaults
        
        Args:
            target_width: Target width (1024-2048 recommended for part number readability)
            enhance_contrast: Enable CLAHE for line drawings
            denoise_strength: 5-10 for PDF artifacts (higher = more aggressive)
            sharpen: Enhance edges for better OCR/symbol detection
            clahe_clip: 1.5-3.0 (higher = more contrast)
            preserve_color: Keep color if True (mostly B&W for IKEA)
        """
        self.target_width = target_width
        self.enhance_contrast = enhance_contrast
        self.denoise_strength = denoise_strength
        self.sharpen = sharpen
        self.clahe_clip = clahe_clip
        self.preserve_color = preserve_color
        
    def preprocess(self, img_bytes: bytes, image_name: str = "unknown") -> bytes:
        """
        Main preprocessing pipeline for IKEA assembly images
        
        Args:
            img_bytes: Original image bytes from PDF
            image_name: Image identifier for logging
            
        Returns:
            Preprocessed image bytes (PNG format)
        """
        try:
            
            start_time = __import__('time').time()
            
            # Step 1: Convert bytes to PIL Image
            pil_img = Image.open(io.BytesIO(img_bytes))
            
            # Step 2: Convert mode if needed
            if not self.preserve_color:
                pil_img = pil_img.convert('L')  # Grayscale for IKEA B&W diagrams
            else:
                pil_img = pil_img.convert('RGB')
            
            # Step 3: Optimize scaling
            pil_img = self._optimize_scaling(pil_img)
            
            # Step 4: Convert to OpenCV for advanced processing
            if self.preserve_color:
                img_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            else:
                img_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_GRAY2BGR)
            
            # Step 5: Denoise (critical for PDF compression artifacts)
            img_cv = self._apply_denoising(img_cv)
            
            # Step 6: Enhance contrast using CLAHE
            if self.enhance_contrast:
                img_cv = self._apply_clahe(img_cv)
            
            # Step 7: Sharpen edges (makes part numbers & symbols clearer)
            if self.sharpen:
                img_cv = self._apply_sharpening(img_cv)
            
            # Step 8: Morphological cleanup (remove tiny noise)
            img_cv = self._apply_morphology(img_cv)
            
            # Step 9: Convert back to PIL
            if self.preserve_color:
                enhanced_img = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
            else:
                enhanced_img = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY))
            
            # Step 10: Final PIL enhancements
            enhanced_img = self._final_pil_enhancements(enhanced_img)
            
            # Step 11: Convert to bytes (PNG for lossless quality)
            img_byte_arr = io.BytesIO()
            enhanced_img.save(img_byte_arr, format='PNG', quality=95, optimize=True)
            img_byte_arr.seek(0)
            
            duration = __import__('time').time() - start_time

            
            return img_byte_arr.getvalue()
            
        except Exception as e:
            print(f"✗ Error preprocessing {image_name}: {e}")
            return img_bytes  # Return original on error
    
    def _optimize_scaling(self, img: Image.Image) -> Image.Image:
        """
        Resize image maintaining aspect ratio
        IKEA instructions need 1024-2048px width for part number readability
        """
        width, height = img.size
        
        if width < self.target_width:
            # Upscale small images (rare for PDFs but possible)
            scale_factor = self.target_width / width
            new_size = (self.target_width, int(height * scale_factor))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            print(f"  - Upscaled from {width}x{height} to {new_size[0]}x{new_size[1]}")
        elif width > 2048:
            # Downscale very large images
            scale_factor = 2048 / width
            new_size = (2048, int(height * scale_factor))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            print(f"  - Downscaled from {width}x{height} to {new_size[0]}x{new_size[1]}")
        
        return img
    
    def _apply_denoising(self, img_cv: np.ndarray) -> np.ndarray:
        """
        Remove PDF compression artifacts and scanning noise
        Uses fastNlMeansDenoising for optimal quality/speed
        """
        try:
            if len(img_cv.shape) == 3:  # Color image
                denoised = cv2.fastNlMeansDenoisingColored(
                    img_cv,
                    None,
                    h=self.denoise_strength,       # Luminance strength
                    hColor=self.denoise_strength,  # Color strength
                    templateWindowSize=7,
                    searchWindowSize=21
                )
            else:  # Grayscale
                denoised = cv2.fastNlMeansDenoising(
                    img_cv,
                    None,
                    h=self.denoise_strength,
                    templateWindowSize=7,
                    searchWindowSize=21
                )
            
            print(f"  - Applied denoising (strength={self.denoise_strength})")
            return denoised
            
        except Exception as e:
            print(f"  - Denoising failed: {e}, returning original")
            return img_cv
    
    def _apply_clahe(self, img_cv: np.ndarray) -> np.ndarray:
        """
        Contrast Limited Adaptive Histogram Equalization (CLAHE)
        Critical for IKEA line drawings with varying contrast
        """
        try:
            if len(img_cv.shape) == 3:
                # Convert to LAB color space
                lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                
                # Apply CLAHE to L channel
                clahe = cv2.createCLAHE(
                    clipLimit=self.clahe_clip,
                    tileGridSize=(8, 8)
                )
                enhanced_l = clahe.apply(l)
                
                # Merge back
                enhanced_lab = cv2.merge((enhanced_l, a, b))
                enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
            else:
                # Grayscale - direct CLAHE
                clahe = cv2.createCLAHE(
                    clipLimit=self.clahe_clip,
                    tileGridSize=(8, 8)
                )
                enhanced_bgr = clahe.apply(img_cv)
            
            print(f"  - Applied CLAHE (clip={self.clahe_clip})")
            return enhanced_bgr
            
        except Exception as e:
            print(f"  - CLAHE failed: {e}, returning original")
            return img_cv
    
    def _apply_sharpening(self, img_cv: np.ndarray) -> np.ndarray:
        """
        Sharpen edges for better part number and symbol detection
        Uses unsharp masking for controlled sharpening
        """
        try:
            # Unsharp masking
            gaussian = cv2.GaussianBlur(img_cv, (0, 0), 1.0)
            sharpened = cv2.addWeighted(img_cv, 1.5, gaussian, -0.5, 0)
            
            # Alternative: kernel-based sharpening for very blurry images
            # kernel = np.array([[-1, -1, -1],
            #                    [-1,  9, -1],
            #                    [-1, -1, -1]])
            # sharpened = cv2.filter2D(img_cv, -1, kernel)
            
            print("  - Applied sharpening (unsharp mask)")
            return sharpened
            
        except Exception as e:
            print(f"  - Sharpening failed: {e}, returning original")
            return img_cv
    
    def _apply_morphology(self, img_cv: np.ndarray) -> np.ndarray:
        """
        Morphological operations to clean noise and connect broken lines
        """
        try:
            if len(img_cv.shape) == 3:
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_cv
            
            # Threshold to binary
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Morphological close (fill small gaps)
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
            
            # Morphological open (remove small noise)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)
            
            # Convert back to original format
            if len(img_cv.shape) == 3:
                cleaned = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)
            
            print("  - Applied morphological cleanup")
            return cleaned
            
        except Exception as e:
            print(f"  - Morphology failed: {e}, returning original")
            return img_cv
    
    def _final_pil_enhancements(self, img: Image.Image) -> Image.Image:
        """
        Final PIL-based enhancements for fine-tuning
        """
        try:
            # Slight contrast boost
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.1)
            
            # Slight sharpness boost
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.15)
            
            # Slight brightness adjustment (if too dark)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.05)
            
            print("  - Applied final PIL enhancements")
            return img
            
        except Exception as e:
            print(f"  - PIL enhancements failed: {e}, returning original")
            return img


# Convenience function for quick preprocessing
def preprocess_ikea_image(
    img_bytes: bytes,
    image_name: str = "unknown",
    target_width: int = 1536,
    denoise_strength: int = 8,
    clahe_clip: float = 2.0
) -> bytes:
    """
    Quick preprocessing for IKEA assembly images
    
    Args:
        img_bytes: Original image bytes
        image_name: Image identifier
        target_width: Target width (1024-2048)
        denoise_strength: 5-10
        clahe_clip: 1.5-3.0
        
    Returns:
        Preprocessed image bytes
    """
    preprocessor = IKEAImagePreprocessor(
        target_width=target_width,
        denoise_strength=denoise_strength,
        clahe_clip=clahe_clip,
        enhance_contrast=True,
        sharpen=True,
        preserve_color=False  # IKEA diagrams are B&W
    )
    return preprocessor.preprocess(img_bytes, image_name)


        
        # PREPROCESS IMAGE
        

file_path = "/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/markdown_files/lack-wall-shelf-unit-black-blue__AA-2699149-1-100/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_6_10/lack-wall-shelf-unit-black-blue__AA-2699149-1-100_6_10_artifacts/image_000004_1d85988a1765e7d2284a09cbd6a869acc24d7a49f59bff252e42468a54fc50c9.png"

with open(file_path, "rb") as f:
    image_bytes = f.read()
    
img_bytes = preprocess_ikea_image(
            img_bytes=image_bytes,
            image_name="image_000004",
            target_width=2048,        # Good balance for part numbers
            denoise_strength=8,       # Moderate denoising for PDFs
            clahe_clip=2.0            # Good contrast for line drawings
        )

with open("/home/anu/RAG_AI_ML_Projects/IKEA_Assembly_Instruction_Processing/data/preprocessed_image.png", "wb") as f:
    f.write(img_bytes)