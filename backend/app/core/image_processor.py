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
from io import BytesIO

# --- DeepFace Import ---
try:
    # We rely on DeepFace and its dependencies being installed correctly
    from deepface import DeepFace
except ImportError:
    # Fallback structure for DeepFace if import fails
    DeepFace = None
    print("WARNING: DeepFace not imported. Face detection will use mock data.")

# Placeholder for YOLOv8n - Actual model loading is often complex, using mock for now
_yolo_model = None 


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
        # Use a longer timeout for fetching large thumbnails
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
    
    # K-means initialization suppression
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10) 
    kmeans.fit(pixels)
    
    colors = []
    for center in kmeans.cluster_centers_:
        r, g, b = center.astype(int)
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    
    return colors


# -----------------------------------------------------------
# DEEP LEARNING / MOCK FUNCTIONS
# -----------------------------------------------------------

def calculate_object_contrast(img_array: np.ndarray, bbox: List[int]) -> float:
    """MOCK/Placeholder: Calculate Weber contrast of the object vs. its background."""
    # In a real scenario, this involves complex region analysis.
    # For now, return a placeholder score.
    return 0.75 


def detect_objects_yolo(img_array: np.ndarray) -> List[Dict]:
    """
    MOCK Object Detection: Placeholder for YOLOv8n inference.
    
    Args:
        img_array: The image data.
        
    Returns:
        List of detected objects with label, confidence, bbox, and contrast.
    """
    # NOTE: If you install ultralytics and uncomment the global model loading, 
    # replace this function with your actual YOLO inference code.
    
    # Mock data for reliable API testing:
    return [
        {
            'label': 'person',
            'confidence': 0.98,
            'bbox': [100, 50, 450, 700], # [xmin, ymin, xmax, ymax]
            'contrast_score_vs_bg': calculate_object_contrast(img_array, [100, 50, 450, 700])
        },
        {
            'label': 'text_overlay',
            'confidence': 0.85,
            'bbox': [500, 750, 950, 950],
            'contrast_score_vs_bg': calculate_object_contrast(img_array, [500, 750, 950, 950])
        }
    ]


def detect_faces_and_emotion(img_array: np.ndarray) -> Dict[str, any]:
    """
    Detects faces and determines the dominant emotion using DeepFace.
    """
    if DeepFace is None:
        print("MOCK: DeepFace not available. Using mock emotion data.")
        return {'face_count': 1, 'detected_emotion': 'happy'}

    try:
        # DeepFace uses BGR, so convert from our internal RGB array
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR) 

        # We only need analysis for faces and emotion
        analysis = DeepFace.analyze(
            img_path=img_bgr,
            actions=('face', 'emotion'),
            detector_backend='retinaface', # Often works well for thumbnails
            enforce_detection=False # Don't raise error if no face found
        )
        
        if not analysis or isinstance(analysis, list) and not analysis[0]:
            return {'face_count': 0, 'detected_emotion': None}

        # DeepFace returns a list of dictionaries for multiple faces
        first_face = analysis[0]
        
        return {
            'face_count': len(analysis),
            'detected_emotion': first_face['dominant_emotion']
        }
        
    except Exception as e:
        print(f"DeepFace analysis failed: {e}")
        # Return fallback data on failure
        return {'face_count': 0, 'detected_emotion': 'Neutral'} 


# -----------------------------------------------------------
# CRITICAL HYBRID TEXT EXTRACTION FUNCTION (PyTesseract + Gemini Bounds)
# -----------------------------------------------------------

def crop_and_extract_text(img_array: np.ndarray, gemini_text_bounds: List[Dict]) -> Dict[str, any]:
    """
    Crops image based on Gemini's normalized bounding boxes and runs Tesseract 
    on the aggregated, cropped region for accurate text extraction.
    """
    # The required gemini_text_bounds argument is passed by main.py
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
# MAIN ANALYSIS ENTRY POINT
# -----------------------------------------------------------

def run_full_analysis(image_bytes: bytes, gemini_text_bounds: Dict) -> Dict:
    """
    Synchronous function that performs complete CV/DL analysis.
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
    
    # 4. Object Detection with Per-Object Contrast (MOCK/REAL)
    detected_objects = detect_objects_yolo(img_array)
    
    # 5. Face & Emotion Detection (DEEPFACE/MOCK)
    face_emotion = detect_faces_and_emotion(img_array)
    
    # Combine all metrics
    analysis_result = {
        'average_brightness': brightness_contrast['average_brightness'],
        'contrast_level': brightness_contrast['contrast_level'],
        'dominant_colors': dominant_colors,
        
        # Text data includes the cropped bytes for the final Gemini step
        'text_content': text_data['text_content'],
        'word_count': text_data['word_count'],
        'cropped_image_bytes': text_data['cropped_image_bytes'], 
        
        'face_count': face_emotion['face_count'],
        'detected_emotion': face_emotion['detected_emotion'],
        'detected_objects': detected_objects
    }
    
    return analysis_result