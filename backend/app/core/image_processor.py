# backend/app/core/image_processor.py

import io
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image
from typing import Optional, Dict, List
from sklearn.cluster import KMeans
import httpx
import pytesseract

# Set the path to your Tesseract executable here
# Replace the path with the exact folder where tesseract.exe is located on your machine.
TESSERACT_EXECUTABLE_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

try:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXECUTABLE_PATH
except AttributeError:
    # This may fail if the module isn't ready; ensure installation first.
    pass

# -----------------------------------------------------------
# CORE UTILITY FUNCTIONS (CV/Image Processing)
# -----------------------------------------------------------

def extract_youtube_thumbnail_url(youtube_url: str) -> Optional[str]:
    """Extract maxresdefault thumbnail URL from YouTube video URL."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^"&?\/\s]{11})',
        r'youtube\.com\/embed\/([^"&?\/\s]{11})',
        r'youtube\.com\/v\/([^"&?\/\s]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            video_id = match.group(1)
            return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    
    return None


async def fetch_image_bytes(url: str) -> bytes:
    """Fetch image bytes from URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=20.0)
        response.raise_for_status()
        return response.content


def calculate_brightness_contrast(img_array: np.ndarray) -> Dict[str, float]:
    """Calculate average brightness (HSV-V) and contrast (Grayscale Std Dev)."""
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    brightness = float(np.mean(hsv[:, :, 2]))
    
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    contrast = float(np.std(gray))
    
    return {
        'average_brightness': brightness,
        'contrast_level': contrast
    }


def extract_dominant_colors(img_array: np.ndarray, n_colors: int = 5) -> List[str]:
    """Extract dominant colors using k-means clustering."""
    small = cv2.resize(img_array, (100, 100))
    pixels = small.reshape(-1, 3)
    
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    kmeans.fit(pixels)
    
    colors = []
    for center in kmeans.cluster_centers_:
        r, g, b = center.astype(int)
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    
    return colors


# -----------------------------------------------------------
# HYBRID TEXT EXTRACTION (PyTesseract + Gemini Bounds)
# -----------------------------------------------------------

def crop_and_extract_text(img_array: np.ndarray, gemini_text_bounds: Dict) -> Dict[str, any]:
    """
    Crops image based on Gemini's normalized bounding boxes and runs Tesseract 
    on the aggregated, cropped region for accurate text extraction.
    """
    if not gemini_text_bounds or not gemini_text_bounds.get('detected_text_blocks'):
        return {'text_content': 'None', 'word_count': 0, 'cropped_image_bytes': b''}

    h, w, _ = img_array.shape
    min_x, min_y, max_x, max_y = w, h, 0, 0
    
    # 1. Aggregate all boxes into a single bounding box
    for block in gemini_text_bounds.get('detected_text_blocks', []):
        [n_x1, n_y1, n_x2, n_y2] = block['box_normalized']
        
        # Denormalize
        x1 = int(n_x1 * w / 1000)
        y1 = int(n_y1 * h / 1000)
        x2 = int(n_x2 * w / 1000)
        y2 = int(n_y2 * h / 1000)

        min_x = min(min_x, x1)
        min_y = min(min_y, y1)
        max_x = max(max_x, x2)
        max_y = max(max_y, y2)

    # 2. Add buffer and crop
    buffer = 15
    final_x1 = max(0, min_x - buffer)
    final_y1 = max(0, min_y - buffer)
    final_x2 = min(w, max_x + buffer)
    final_y2 = min(h, max_y + buffer)

    cropped_img_array = img_array[final_y1:final_y2, final_x1:final_x2].copy()
    
    if cropped_img_array.size == 0:
        return {'text_content': 'None', 'word_count': 0, 'cropped_image_bytes': b''}

    # 3. Preprocess for OCR
    gray = cv2.cvtColor(cropped_img_array, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 4. Run OCR
    try:
        text = pytesseract.image_to_string(thresh, config='--psm 11').strip()
        word_count = len(text.split()) if text else 0
        
        # Encode the cropped image back to bytes (JPEG) for final Gemini step
        _, buffer = cv2.imencode('.jpeg', cv2.cvtColor(cropped_img_array, cv2.COLOR_RGB2BGR))
        
        return {
            'text_content': text,
            'word_count': word_count,
            'cropped_image_bytes': buffer.tobytes()
        }
    except Exception as e:
        print(f"OCR error on cropped image: {e}")
        return {'text_content': 'OCR Failed', 'word_count': 0, 'cropped_image_bytes': b''}


# -----------------------------------------------------------
# MAIN ANALYSIS ENTRY POINT (CV Metrics Only)
# -----------------------------------------------------------

def run_full_analysis(image_bytes: bytes, gemini_text_bounds: Dict) -> Dict:
    """
    Synchronous function that performs CV analysis only.
    Object detection, face detection, and emotion analysis are now handled by Gemini.
    Called from main.py and expected to run in a threadpool.
    """
    # Load image (Convert to NumPy array, RGB format)
    img = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(img.convert('RGB'))
    
    # 1. Brightness & Contrast
    brightness_contrast = calculate_brightness_contrast(img_array)
    
    # 2. Dominant Colors
    dominant_colors = extract_dominant_colors(img_array)
    
    # 3. Targeted Text Extraction (uses Gemini bounds)
    text_data = crop_and_extract_text(img_array, gemini_text_bounds)
    
    # Return only CV metrics - object/face/emotion data will be added by main.py
    analysis_result = {
        'average_brightness': brightness_contrast['average_brightness'],
        'contrast_level': brightness_contrast['contrast_level'],
        'dominant_colors': dominant_colors,
        'text_content': text_data['text_content'],
        'word_count': text_data['word_count'],
        'cropped_image_bytes': text_data['cropped_image_bytes']
    }
    
    return analysis_result