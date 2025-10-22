# /backend/app/core/image_processor.py

import io
import re
import traceback
import cv2
import numpy as np
from PIL import Image
from typing import Optional, Dict, List
from sklearn.cluster import KMeans
import httpx
import os
import base64 

# --- New OCR.Space API Constants ---
OCR_SPACE_URL = "https://api.ocr.space/parse/image"
OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY")

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
# OCR.SPACE TEXT EXTRACTION
# -----------------------------------------------------------

def run_external_ocr(image_bytes: bytes) -> Dict[str, any]:
    """
    Performs OCR using the OCR.Space API via a direct HTTP POST request.
    Enhanced error handling and retry logic.
    """
    if not OCR_SPACE_API_KEY:
        print("❌ ERROR: OCR_SPACE_API_KEY not found in environment.")
        return {
            'text_content': 'None',  # Changed from 'OCR Failed'
            'word_count': 0
        }

    try:
        # Convert image to Base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Construct payload for OCR.Space
        payload = {
            'base64Image': f'data:image/jpeg;base64,{base64_image}',
            'language': 'eng',
            'isOverlayRequired': False,
            'detectOrientation': True,  # Better detection
            'scale': True,  # Improve accuracy
            'OCREngine': 2  # Use OCR Engine 2 (more accurate)
        }

        headers = {
            'apikey': OCR_SPACE_API_KEY,
        }

        print(f"🔍 Calling OCR.Space API...")
        
        # Make the API call with proper timeout
        response = httpx.post(
            OCR_SPACE_URL, 
            data=payload, 
            headers=headers, 
            timeout=30.0  # Increased timeout
        )
        
        print(f"📡 OCR.Space Response Status: {response.status_code}")
        
        response.raise_for_status()
        result = response.json()

        # Check for processing errors
        if result.get('IsErroredOnProcessing'):
            error_messages = result.get('ErrorMessage', [])
            error_msg = error_messages[0] if error_messages else 'Unknown OCR Error'
            print(f"❌ OCR.Space Processing Error: {error_msg}")
            
            # Check if it's a rate limit error
            if 'rate limit' in error_msg.lower() or 'quota' in error_msg.lower():
                print("⚠️ Rate limit detected - returning fallback")
            
            return {
                'text_content': 'None',  # Don't show error to user
                'word_count': 0
            }

        # Extract text from the result
        if result.get('ParsedResults') and len(result['ParsedResults']) > 0:
            parsed_text = result['ParsedResults'][0].get('ParsedText', '').strip()
            
            # Handle empty or whitespace-only results
            if not parsed_text or parsed_text.isspace():
                print("⚠️ OCR returned empty text")
                return {
                    'text_content': 'None',
                    'word_count': 0
                }
            
            # Clean up the text
            text_content = ' '.join(parsed_text.split())  # Normalize whitespace
            word_count = len(text_content.split()) if text_content else 0
            
            print(f"✅ OCR.Space successful: '{text_content[:50]}...' ({word_count} words)")
            
            return {
                'text_content': text_content,
                'word_count': word_count
            }
        else:
            print("⚠️ OCR.Space returned no ParsedResults")
            return {
                'text_content': 'None',
                'word_count': 0
            }

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error connecting to OCR.Space: {e}")
        print(f"   Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return {
            'text_content': 'None',
            'word_count': 0
        }
    except httpx.TimeoutException:
        print("❌ OCR.Space request timed out")
        return {
            'text_content': 'None',
            'word_count': 0
        }
    except Exception as e:
        print(f"❌ Unexpected OCR Error: {e}")
        traceback.print_exc()
        return {
            'text_content': 'None',
            'word_count': 0
        }


# -----------------------------------------------------------
# HELPER FUNCTIONS
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


def calculate_face_position(bbox_normalized: List[int]) -> str:
    """Calculate the position of a face/object in the thumbnail."""
    center_x = (bbox_normalized[0] + bbox_normalized[2]) / 2
    center_y = (bbox_normalized[1] + bbox_normalized[3]) / 2
    
    if center_x < 333:
        h_pos = "left"
    elif center_x < 666:
        h_pos = "center"
    else:
        h_pos = "right"
    
    if center_y < 333:
        v_pos = "top"
    elif center_y < 666:
        v_pos = "center"
    else:
        v_pos = "bottom"
    
    if v_pos == "center" and h_pos == "center":
        return "center"
    elif v_pos == "center":
        return f"center-{h_pos}"
    elif h_pos == "center":
        return f"{v_pos}-center"
    else:
        return f"{v_pos}-{h_pos}"


def calculate_object_contrast(img_array: np.ndarray, bbox_normalized: List[int]) -> float:
    """Calculate contrast score between object and background."""
    h, w, _ = img_array.shape
    
    x1 = int(bbox_normalized[0] * w / 1000)
    y1 = int(bbox_normalized[1] * h / 1000)
    x2 = int(bbox_normalized[2] * w / 1000)
    y2 = int(bbox_normalized[3] * h / 1000)
    
    x1 = max(0, min(x1, w - 1))
    y1 = max(0, min(y1, h - 1))
    x2 = max(x1 + 1, min(x2, w))
    y2 = max(y1 + 1, min(y2, h))
    
    if x1 >= x2 or y1 >= y2:
        return 0.5
    
    try:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        object_region = gray[y1:y2, x1:x2]
        
        if object_region.size == 0:
            return 0.5
        
        object_mean = np.mean(object_region)
        
        bg_mask = np.ones_like(gray, dtype=bool)
        bg_mask[y1:y2, x1:x2] = False
        
        bg_pixels = gray[bg_mask]
        if bg_pixels.size == 0:
            return 0.5
        
        bg_mean = np.mean(bg_pixels)
        
        contrast = abs(object_mean - bg_mean) / 255.0
        
        scaled_contrast = min(1.0, contrast * 2.5)
        
        return round(scaled_contrast, 3)
        
    except Exception as e:
        print(f"⚠️ Contrast calculation error: {e}")
        return 0.5


# -----------------------------------------------------------
# MAIN ANALYSIS ENTRY POINT
# -----------------------------------------------------------

def run_full_analysis(image_bytes: bytes, gemini_detections: List[Dict]) -> Dict:
    """
    Comprehensive analysis function using run_external_ocr for text extraction.
    """
    print(f"🔧 run_full_analysis called with {len(gemini_detections)} Gemini detections")
    
    # Load image (Convert to NumPy array, RGB format)
    img = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(img.convert('RGB'))
    img_height, img_width = img_array.shape[:2]
    
    print(f"🖼️ Image loaded: {img_width}x{img_height}")
    
    # ===== STEP 1: CV Metrics =====
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
            object_elements.append(detection)
    
    print(f"📊 Categorized: {len(text_elements)} text, {len(face_elements)} faces, {len(object_elements)} objects")
    
    # ===== STEP 3: Text Extraction with OCR.Space API =====
    text_data = run_external_ocr(image_bytes)
    
    print(f"📝 External OCR: '{text_data['text_content'][:100] if text_data['text_content'] else 'EMPTY'}' ({text_data['word_count']} words)")
    
    # ===== STEP 4: Process Face Elements =====
    processed_faces = []
    face_count = len(face_elements)
    detected_emotion = None
    
    for face_elem in face_elements:
        face_copy = face_elem.copy()
        
        if 'bbox_normalized' in face_copy:
            contrast_score = calculate_object_contrast(img_array, face_copy['bbox_normalized'])
            face_copy['contrast_score_vs_bg'] = contrast_score
            
            position = calculate_face_position(face_copy['bbox_normalized'])
            face_copy['position'] = position
        else:
            face_copy['contrast_score_vs_bg'] = 0.5
            face_copy['position'] = 'unknown'
        
        face_copy['element_type'] = 'face'
        
        processed_faces.append(face_copy)
        
        if detected_emotion is None and 'emotion' in face_copy:
            detected_emotion = face_copy['emotion']
    
    print(f"👤 Processed {face_count} face(s), dominant emotion: {detected_emotion}")
    
    # ===== STEP 5: Process Object Elements =====
    processed_objects = []
    
    for obj_elem in object_elements:
        obj_copy = obj_elem.copy()
        
        if 'bbox_normalized' in obj_copy:
            contrast_score = calculate_object_contrast(img_array, obj_copy['bbox_normalized'])
            obj_copy['contrast_score_vs_bg'] = contrast_score
            
            position = calculate_face_position(obj_copy['bbox_normalized'])
            obj_copy['position'] = position
        else:
            obj_copy['contrast_score_vs_bg'] = 0.5
            obj_copy['position'] = 'unknown'
        
        obj_copy['element_type'] = 'object'
        
        processed_objects.append(obj_copy)
    
    print(f"🎯 Processed {len(processed_objects)} object(s):")
    for obj in processed_objects:
        print(f"   - {obj.get('label', 'unknown')} (confidence: {obj.get('confidence', 0):.2f}, contrast: {obj.get('contrast_score_vs_bg', 0):.3f})")
    
    # ===== STEP 6: Compile Comprehensive Results =====
    # CRITICAL: Ensure text_data values are not None
    final_text_content = text_data.get('text_content', 'None')
    final_word_count = text_data.get('word_count', 0)
    
    # Debug: Verify the values before adding to dict
    print(f"🔍 PRE-DICT text_content: '{final_text_content[:100] if final_text_content else 'EMPTY'}'")
    print(f"🔍 PRE-DICT word_count: {final_word_count}")
    
    analysis_result = {
        'average_brightness': brightness_contrast['average_brightness'],
        'contrast_level': brightness_contrast['contrast_level'],
        'dominant_colors': dominant_colors,
        
        'text_content': final_text_content,
        'word_count': final_word_count,
        
        'face_count': face_count,
        'detected_emotion': detected_emotion,
        'detected_faces': processed_faces,
        
        'detected_objects': processed_objects
    }

    print(f"✅ run_full_analysis complete: {face_count} faces, {len(processed_objects)} objects")
    print(f"📤 POST-DICT text_content: '{analysis_result['text_content'][:100] if analysis_result['text_content'] else 'EMPTY'}'")
    print(f"📤 POST-DICT word_count: {analysis_result['word_count']}")
    
    return analysis_result


# Backward compatibility wrapper
def classify_element_type(label: str) -> str:
    """Legacy function for backward compatibility."""
    if is_face_element(label):
        return 'face'
    elif is_text_element(label):
        return 'text'
    else:
        return 'object'