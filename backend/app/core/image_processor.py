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

# Set the path to your Tesseract executable here
TESSERACT_EXECUTABLE_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

try:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXECUTABLE_PATH
except AttributeError:
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

def crop_and_extract_text(img_array: np.ndarray, text_blocks: List[Dict]) -> Dict[str, any]:
    """
    Crops image based on normalized bounding boxes and runs Tesseract 
    on the aggregated, cropped region for accurate text extraction.
    
    Args:
        img_array: NumPy array of the image (RGB)
        text_blocks: List of dicts with 'bbox_normalized' [xmin, ymin, xmax, ymax] keys
    
    Returns:
        Dict with 'text_content', 'word_count', and 'cropped_image_bytes'
    """
    # Handle empty or invalid input defensively
    if not text_blocks or not isinstance(text_blocks, list):
        return {
            'text_content': 'None',
            'word_count': 0,
            'cropped_image_bytes': b''
        }
    
    h, w, _ = img_array.shape
    min_x, min_y, max_x, max_y = w, h, 0, 0
    
    # 1. Aggregate all boxes into a single bounding box
    valid_boxes_found = False
    for block in text_blocks:
        # Defensive: check if required key exists
        if 'bbox_normalized' not in block:
            continue
            
        box = block['bbox_normalized']
        if not isinstance(box, list) or len(box) != 4:
            continue
        
        n_x1, n_y1, n_x2, n_y2 = box
        
        # Denormalize (assuming 0-1000 scale)
        x1 = int(n_x1 * w / 1000)
        y1 = int(n_y1 * h / 1000)
        x2 = int(n_x2 * w / 1000)
        y2 = int(n_y2 * h / 1000)
        
        # Ensure valid coordinates
        if x1 >= x2 or y1 >= y2:
            continue
        
        min_x = min(min_x, x1)
        min_y = min(min_y, y1)
        max_x = max(max_x, x2)
        max_y = max(max_y, y2)
        valid_boxes_found = True
    
    # If no valid boxes found, return empty result
    if not valid_boxes_found:
        return {
            'text_content': 'None',
            'word_count': 0,
            'cropped_image_bytes': b''
        }
    
    # 2. Add buffer and crop
    buffer = 15
    final_x1 = max(0, min_x - buffer)
    final_y1 = max(0, min_y - buffer)
    final_x2 = min(w, max_x + buffer)
    final_y2 = min(h, max_y + buffer)
    
    # Ensure valid crop region
    if final_x1 >= final_x2 or final_y1 >= final_y2:
        return {
            'text_content': 'None',
            'word_count': 0,
            'cropped_image_bytes': b''
        }
    
    cropped_img_array = img_array[final_y1:final_y2, final_x1:final_x2].copy()
    
    if cropped_img_array.size == 0:
        return {
            'text_content': 'None',
            'word_count': 0,
            'cropped_image_bytes': b''
        }
    
    # 3. Preprocess for OCR
    gray = cv2.cvtColor(cropped_img_array, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 4. Run OCR
    try:
        text = pytesseract.image_to_string(thresh, config='--psm 11').strip()
        word_count = len(text.split()) if text else 0
        
        # Encode the cropped image back to bytes (JPEG) for final Gemini step
        _, buffer_encoded = cv2.imencode('.jpeg', cv2.cvtColor(cropped_img_array, cv2.COLOR_RGB2BGR))
        
        return {
            'text_content': text if text else 'None',
            'word_count': word_count,
            'cropped_image_bytes': buffer_encoded.tobytes()
        }
    except Exception as e:
        print(f"❌ OCR error on cropped image: {e}")
        return {
            'text_content': 'OCR Failed',
            'word_count': 0,
            'cropped_image_bytes': b''
        }


# -----------------------------------------------------------
# ELEMENT TYPE CLASSIFIER
# -----------------------------------------------------------

def is_text_element(label: str) -> bool:
    """Check if an element is text-related."""
    label_lower = label.lower()
    text_keywords = ['text', 'caption', 'title', 'subtitle', 'overlay', 'word', 'letter']
    return any(keyword in label_lower for keyword in text_keywords)


def is_face_element(label: str) -> bool:
    """Check if an element is a face/person."""
    label_lower = label.lower()
    face_keywords = ['face', 'person', 'human', 'head', 'portrait']
    return any(keyword in label_lower for keyword in face_keywords)


# -----------------------------------------------------------
# FACE POSITION CALCULATION
# -----------------------------------------------------------

def calculate_face_position(bbox_normalized: List[int]) -> str:
    """
    Calculate the relative position of a face in the thumbnail.
    
    Args:
        bbox_normalized: [xmin, ymin, xmax, ymax] normalized to 0-1000
    
    Returns:
        Position string: 'top-left', 'top-center', 'top-right', 
                        'center-left', 'center', 'center-right',
                        'bottom-left', 'bottom-center', 'bottom-right'
    """
    # Calculate center of the bounding box
    center_x = (bbox_normalized[0] + bbox_normalized[2]) / 2
    center_y = (bbox_normalized[1] + bbox_normalized[3]) / 2
    
    # Determine horizontal position
    if center_x < 333:
        h_pos = "left"
    elif center_x < 666:
        h_pos = "center"
    else:
        h_pos = "right"
    
    # Determine vertical position
    if center_y < 333:
        v_pos = "top"
    elif center_y < 666:
        v_pos = "center"
    else:
        v_pos = "bottom"
    
    # Combine positions
    if v_pos == "center" and h_pos == "center":
        return "center"
    elif v_pos == "center":
        return f"center-{h_pos}"
    elif h_pos == "center":
        return f"{v_pos}-center"
    else:
        return f"{v_pos}-{h_pos}"


# -----------------------------------------------------------
# CONTRAST CALCULATION FOR OBJECTS
# -----------------------------------------------------------

def calculate_object_contrast(img_array: np.ndarray, bbox_normalized: List[int]) -> float:
    """
    Calculate contrast score for a detected object vs background.
    
    Args:
        img_array: NumPy array of the image (RGB)
        bbox_normalized: [xmin, ymin, xmax, ymax] normalized to 0-1000
    
    Returns:
        Contrast score (0-1), where higher means better contrast
    """
    h, w, _ = img_array.shape
    
    # Denormalize coordinates
    x1 = int(bbox_normalized[0] * w / 1000)
    y1 = int(bbox_normalized[1] * h / 1000)
    x2 = int(bbox_normalized[2] * w / 1000)
    y2 = int(bbox_normalized[3] * h / 1000)
    
    # Validate coordinates
    x1 = max(0, min(x1, w - 1))
    y1 = max(0, min(y1, h - 1))
    x2 = max(x1 + 1, min(x2, w))
    y2 = max(y1 + 1, min(y2, h))
    
    if x1 >= x2 or y1 >= y2:
        return 0.5  # Default neutral score for invalid boxes
    
    try:
        # Convert to grayscale for contrast calculation
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Extract object region
        object_region = gray[y1:y2, x1:x2]
        
        if object_region.size == 0:
            return 0.5
        
        # Calculate mean brightness of object
        object_mean = np.mean(object_region)
        
        # Create a background mask (exclude the object region)
        bg_mask = np.ones_like(gray, dtype=bool)
        bg_mask[y1:y2, x1:x2] = False
        
        # Calculate mean brightness of background
        bg_pixels = gray[bg_mask]
        if bg_pixels.size == 0:
            return 0.5
        
        bg_mean = np.mean(bg_pixels)
        
        # Calculate contrast as normalized absolute difference
        # Scale to 0-1 range (max difference is 255)
        contrast = abs(object_mean - bg_mean) / 255.0
        
        # Apply a sigmoid-like scaling to make scores more meaningful
        scaled_contrast = min(1.0, contrast * 2.5)
        
        return round(scaled_contrast, 3)
        
    except Exception as e:
        print(f"⚠️ Contrast calculation error: {e}")
        return 0.5


# -----------------------------------------------------------
# MAIN ANALYSIS ENTRY POINT (FIXED)
# -----------------------------------------------------------

def run_full_analysis(image_bytes: bytes, gemini_detections: List[Dict]) -> Dict:
    """
    Comprehensive analysis function that processes Gemini detections and performs CV analysis.
    
    This is the MAIN processing function that:
    1. Performs CV analysis (brightness, contrast, colors)
    2. Categorizes Gemini detections into text/faces/objects
    3. Processes text regions with OCR
    4. Calculates contrast scores and positions for all objects and faces
    5. Derives face_count and detected_emotion from faces
    
    Args:
        image_bytes: Raw image bytes
        gemini_detections: List of ALL detected elements from Gemini API (dicts)
    
    Returns:
        Comprehensive dictionary containing:
        - CV metrics (brightness, contrast, colors)
        - Text analysis (content, word_count, cropped_image_bytes)
        - Face data (face_count, detected_emotion, detected_faces list)
        - Object data (detected_objects list with contrast scores)
    """
    print(f"🔧 run_full_analysis called with {len(gemini_detections)} Gemini detections")
    
    # Load image (Convert to NumPy array, RGB format)
    img = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(img.convert('RGB'))
    img_height, img_width = img_array.shape[:2]
    
    print(f"🖼️ Image loaded: {img_width}x{img_height}")
    
    # ===== STEP 1: CV Metrics (Independent of detections) =====
    brightness_contrast = calculate_brightness_contrast(img_array)
    dominant_colors = extract_dominant_colors(img_array)
    
    print(f"✅ CV Metrics: Brightness={brightness_contrast['average_brightness']:.2f}, Contrast={brightness_contrast['contrast_level']:.2f}")
    
    # ===== STEP 2: Categorize Gemini Detections =====
    text_elements = []
    face_elements = []
    object_elements = []
    
    for detection in gemini_detections:
        label = detection.get('label', '')
        
        if is_text_element(label):
            text_elements.append(detection)
        elif is_face_element(label):
            face_elements.append(detection)
        else:
            # Everything else is a general object (elephant, logo, etc.)
            object_elements.append(detection)
    
    print(f"📊 Categorized: {len(text_elements)} text, {len(face_elements)} faces, {len(object_elements)} objects")
    
    # ===== STEP 3: Process Text Elements (OCR) =====
    text_blocks_for_ocr = []
    for text_elem in text_elements:
        if 'bbox_normalized' in text_elem:
            text_blocks_for_ocr.append({
                'bbox_normalized': text_elem['bbox_normalized'],
                'text_label': text_elem.get('label', 'text')
            })
    
    text_data = crop_and_extract_text(img_array, text_blocks_for_ocr)
    print(f"📝 OCR: '{text_data['text_content']}' ({text_data['word_count']} words)")
    
    # ===== STEP 4: Process Face Elements =====
    processed_faces = []
    face_count = len(face_elements)
    detected_emotion = None
    
    for face_elem in face_elements:
        face_copy = face_elem.copy()
        
        # Calculate contrast score
        if 'bbox_normalized' in face_copy:
            contrast_score = calculate_object_contrast(img_array, face_copy['bbox_normalized'])
            face_copy['contrast_score_vs_bg'] = contrast_score
            
            # Calculate position
            position = calculate_face_position(face_copy['bbox_normalized'])
            face_copy['position'] = position
        else:
            face_copy['contrast_score_vs_bg'] = 0.5
            face_copy['position'] = 'unknown'
        
        # Set element type
        face_copy['element_type'] = 'face'
        
        processed_faces.append(face_copy)
        
        # Extract dominant emotion (from first/most prominent face)
        if detected_emotion is None and 'emotion' in face_copy:
            detected_emotion = face_copy['emotion']
    
    print(f"👤 Processed {face_count} face(s), dominant emotion: {detected_emotion}")
    
    # ===== STEP 5: Process Object Elements (THE KEY FIX) =====
    processed_objects = []
    
    for obj_elem in object_elements:
        obj_copy = obj_elem.copy()
        
        # Calculate contrast score
        if 'bbox_normalized' in obj_copy:
            contrast_score = calculate_object_contrast(img_array, obj_copy['bbox_normalized'])
            obj_copy['contrast_score_vs_bg'] = contrast_score
            
            # Calculate position (optional, but helpful for objects too)
            position = calculate_face_position(obj_copy['bbox_normalized'])
            obj_copy['position'] = position
        else:
            obj_copy['contrast_score_vs_bg'] = 0.5
            obj_copy['position'] = 'unknown'
        
        # Set element type
        obj_copy['element_type'] = 'object'
        
        processed_objects.append(obj_copy)
    
    print(f"🎯 Processed {len(processed_objects)} object(s):")
    for obj in processed_objects:
        print(f"   - {obj.get('label', 'unknown')} (confidence: {obj.get('confidence', 0):.2f}, contrast: {obj.get('contrast_score_vs_bg', 0):.3f})")
    
    # ===== STEP 6: Compile Comprehensive Results =====
    analysis_result = {
        # CV Metrics
        'average_brightness': brightness_contrast['average_brightness'],
        'contrast_level': brightness_contrast['contrast_level'],
        'dominant_colors': dominant_colors,
        
        # Text Analysis
        'text_content': text_data['text_content'],
        'word_count': text_data['word_count'],
        'cropped_image_bytes': text_data['cropped_image_bytes'],
        
        # Face Data (derived from gemini_detections)
        'face_count': face_count,
        'detected_emotion': detected_emotion,
        'detected_faces': processed_faces,
        
        # Object Data (derived from gemini_detections) - NOW POPULATED CORRECTLY
        'detected_objects': processed_objects
    }
    
    print(f"✅ run_full_analysis complete: {face_count} faces, {len(processed_objects)} objects")
    
    return analysis_result


# Backward compatibility wrapper (if needed elsewhere)
def classify_element_type(label: str) -> str:
    """Legacy function for backward compatibility."""
    if is_face_element(label):
        return 'face'
    elif is_text_element(label):
        return 'text'
    else:
        return 'object'