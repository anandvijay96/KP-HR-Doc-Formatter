import cv2
import numpy as np
import pytesseract
from PIL import Image
import io
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from app.core.config import settings

class OCRProcessor:
    """OCR processing for scanned resumes and image-based documents"""
    
    def __init__(self):
        # Set Tesseract path if specified in config
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text from image using OCR"""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert PIL to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image
            processed_image = self.preprocess_image(opencv_image)
            
            # OCR configuration
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,;:!?@#$%^&*()_+-=[]{}|\\`~"\'<>/ \n\t'
            
            # Extract text
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            return text.strip()
            
        except Exception as e:
            logging.error(f"OCR processing failed: {str(e)}")
            return ""
    
    def detect_document_layout(self, image_data: bytes) -> Dict[str, Any]:
        """Detect document layout and structure"""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Find contours to detect text blocks
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by area to get text blocks
            text_blocks = []
            min_area = 100  # Minimum area for a text block
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > min_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    text_blocks.append({
                        'x': x, 'y': y, 'width': w, 'height': h,
                        'area': area
                    })
            
            # Sort text blocks by position (top to bottom, left to right)
            text_blocks.sort(key=lambda block: (block['y'], block['x']))
            
            return {
                'text_blocks': text_blocks,
                'total_blocks': len(text_blocks),
                'image_dimensions': {
                    'width': opencv_image.shape[1],
                    'height': opencv_image.shape[0]
                }
            }
            
        except Exception as e:
            logging.error(f"Layout detection failed: {str(e)}")
            return {'text_blocks': [], 'total_blocks': 0}
    
    def extract_structured_text(self, image_data: bytes) -> Dict[str, str]:
        """Extract text with structure information"""
        try:
            # Get layout information
            layout = self.detect_document_layout(image_data)
            
            # Extract text with bounding box information
            image = Image.open(io.BytesIO(image_data))
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Get detailed OCR data
            ocr_data = pytesseract.image_to_data(opencv_image, output_type=pytesseract.Output.DICT)
            
            # Group text by approximate sections
            sections = {
                'header': '',
                'body': '',
                'footer': ''
            }
            
            height = opencv_image.shape[0]
            header_threshold = height * 0.2  # Top 20%
            footer_threshold = height * 0.8   # Bottom 20%
            
            for i in range(len(ocr_data['text'])):
                if int(ocr_data['conf'][i]) > 30:  # Confidence threshold
                    text = ocr_data['text'][i].strip()
                    if text:
                        y_pos = ocr_data['top'][i]
                        
                        if y_pos < header_threshold:
                            sections['header'] += text + ' '
                        elif y_pos > footer_threshold:
                            sections['footer'] += text + ' '
                        else:
                            sections['body'] += text + ' '
            
            # Clean up sections
            for key in sections:
                sections[key] = sections[key].strip()
            
            return sections
            
        except Exception as e:
            logging.error(f"Structured text extraction failed: {str(e)}")
            return {'header': '', 'body': '', 'footer': ''}
    
    def is_scanned_document(self, file_path: Path) -> bool:
        """Determine if document appears to be scanned (image-based)"""
        try:
            # This is a simple heuristic - in practice, you might want more sophisticated detection
            # For now, we'll assume PDFs might be scanned and need OCR
            return file_path.suffix.lower() == '.pdf'
        except Exception:
            return False
