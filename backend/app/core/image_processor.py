import io
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image
from typing import Optional, Dict, List
from sklearn.cluster import KMeans
import httpx

try:
    from deepface import DeepFace
except ImportError:
    DeepFace = None

# Placeholder for YOLOv8n - would be loaded globally at startup
# from ultralytics import YOLO
# _yolo_model = YOLO('yolov8n.pt')  # Nano model for CPU
_yolo_model = None


def extract_youtube_thumbnail_url(youtube_url: str) -> Optional[str]:
    """Extract maxresdefault thumbnail URL from YouTube video URL."""
    # Match various YouTube URL formats
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
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.content


def calculate_brightness_contrast(img_array: np.ndarray) -> Dict[str, float]:
    """Calculate average brightness (HSV-V) and contrast (Grayscale Std Dev)."""
    # Brightness: Mean of V channel in HSV
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    brightness = float(np.mean(hsv[:, :, 2]))
    
    # Contrast: Standard deviation of grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    contrast = float(np.std(gray))
    
    return {
        'brightness': brightness,
        'contrast': contrast
    }


def extract_dominant_colors(img_array: np.ndarray, n_colors: int = 5) -> List[str]:
    """Extract dominant colors using k-means clustering."""
    # Downsample for speed
    small = cv2.resize(img_array, (100, 100))
    pixels = small.reshape(-1, 3)
    
    # K-means clustering
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    kmeans.fit(pixels)
    
    # Convert to hex colors
    colors = []
    for center in kmeans.cluster_centers_:
        r, g, b = center.astype(int)
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    
    return colors


def extract_text_with_ocr(img_array: np.ndarray) -> Dict[str, any]:
    """Extract text using pytesseract with Otsu's thresholding."""
    # Convert to grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Apply Otsu's thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # OCR
    try:
        text = pytesseract.image_to_string(thresh, config='--psm 6')
        text = text.strip()
        word_count = len(text.split()) if text else 0
        
        return {
            'text_content': text,
            'word_count': word_count
        }
    except Exception as e:
        print(f"OCR error: {e}")
        return {
            'text_content': '',
            'word_count': 0
        }


def detect_objects_yolo(img_array: np.ndarray) -> List[Dict]:
    """
    Detect objects using YOLOv8n and calculate per-object contrast.
    
    NOTE: This is a placeholder implementation. In production:
    1. Load YOLOv8n globally: _yolo_model = YOLO('yolov8n.pt')
    2. Call: results = _yolo_model(img_array)
    """
    if _yolo_model is None:
        # Mock detection for demonstration
        return _mock_object_detection(img_array)
    
    # Real YOLOv8n implementation would be:
    # results = _yolo_model(img_array, conf=0.25)
    # objects = []
    # for r in results:
    #     boxes = r.boxes
    #     for box in boxes:
    #         x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
    #         conf = float(box.conf[0])
    #         cls = int(box.cls[0])
    #         label = _yolo_model.names[cls]
    #         
    #         # Calculate per-object contrast
    #         contrast = calculate_object_contrast(img_array, x1, y1, x2, y2)
    #         
    #         objects.append({
    #             'label': label,
    #             'confidence': conf,
    #             'bbox': [x1, y1, x2, y2],
    #             'contrast_score_vs_bg': contrast
    #         })
    # return objects
    
    return []


def calculate_object_contrast(img_array: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> float:
    """
    Calculate Weber contrast ratio between object and background.
    
    Weber Contrast = (L_foreground - L_background) / L_background
    """
    h, w = img_array.shape[:2]
    
    # Extract foreground (object bounding box)
    fg = img_array[y1:y2, x1:x2]
    if fg.size == 0:
        return 0.0
    
    fg_gray = cv2.cvtColor(fg, cv2.COLOR_RGB2GRAY)
    fg_mean = np.mean(fg_gray)
    
    # Extract background (margin around object)
    margin = 10
    bg_x1 = max(0, x1 - margin)
    bg_y1 = max(0, y1 - margin)
    bg_x2 = min(w, x2 + margin)
    bg_y2 = min(h, y2 + margin)
    
    # Background mask (exclude foreground)
    bg_region = img_array[bg_y1:bg_y2, bg_x1:bg_x2].copy()
    
    # Create mask for foreground within bg_region
    fg_in_bg_y1 = y1 - bg_y1
    fg_in_bg_x1 = x1 - bg_x1
    fg_in_bg_y2 = fg_in_bg_y1 + (y2 - y1)
    fg_in_bg_x2 = fg_in_bg_x1 + (x2 - x1)
    
    mask = np.ones(bg_region.shape[:2], dtype=bool)
    mask[fg_in_bg_y1:fg_in_bg_y2, fg_in_bg_x1:fg_in_bg_x2] = False
    
    bg_gray = cv2.cvtColor(bg_region, cv2.COLOR_RGB2GRAY)
    bg_pixels = bg_gray[mask]
    
    if bg_pixels.size == 0:
        return 0.0
    
    bg_mean = np.mean(bg_pixels)
    
    # Weber contrast
    if bg_mean == 0:
        return 0.0
    
    contrast = abs(fg_mean - bg_mean) / bg_mean
    return float(contrast)


def _mock_object_detection(img_array: np.ndarray) -> List[Dict]:
    """Mock object detection for testing without YOLOv8n."""
    h, w = img_array.shape[:2]
    
    # Simulate 2-3 detected objects
    mock_objects = [
        {
            'label': 'person',
            'confidence': 0.87,
            'bbox': [int(w*0.3), int(h*0.2), int(w*0.7), int(h*0.8)],
            'contrast_score_vs_bg': 0.0
        },
        {
            'label': 'text',
            'confidence': 0.92,
            'bbox': [int(w*0.1), int(h*0.1), int(w*0.5), int(h*0.3)],
            'contrast_score_vs_bg': 0.0
        }
    ]
    
    # Calculate actual contrast for mock objects
    for obj in mock_objects:
        x1, y1, x2, y2 = obj['bbox']
        obj['contrast_score_vs_bg'] = calculate_object_contrast(img_array, x1, y1, x2, y2)
    
    return mock_objects


def detect_faces_and_emotion(img_array: np.ndarray) -> Dict[str, any]:
    """Detect faces and dominant emotion using DeepFace."""
    if DeepFace is None:
        return {
            'face_count': 0,
            'detected_emotion': 'N/A'
        }
    
    try:
        # Convert to BGR for DeepFace (it expects OpenCV format)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Analyze with lightweight detector
        # Using 'opencv' detector and 'Emotion' model (lightweight)
        results = DeepFace.analyze(
            img_bgr,
            actions=['emotion'],
            detector_backend='opencv',
            enforce_detection=False,
            silent=True
        )
        
        if isinstance(results, list):
            face_count = len(results)
            if face_count > 0:
                # Get dominant emotion from first face
                emotions = results[0].get('emotion', {})
                dominant_emotion = max(emotions, key=emotions.get) if emotions else 'neutral'
            else:
                dominant_emotion = 'N/A'
        else:
            face_count = 1 if results else 0
            emotions = results.get('emotion', {}) if results else {}
            dominant_emotion = max(emotions, key=emotions.get) if emotions else 'neutral'
        
        return {
            'face_count': face_count,
            'detected_emotion': dominant_emotion
        }
        
    except Exception as e:
        print(f"Face detection error: {e}")
        return {
            'face_count': 0,
            'detected_emotion': 'N/A'
        }


def run_full_analysis(image_bytes: bytes) -> Dict:
    """
    Synchronous function that performs complete CV/DL analysis.
    This will be wrapped in FastAPI's threadpool.
    """
    # Load image
    img = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(img.convert('RGB'))
    
    # 1. Brightness & Contrast
    brightness_contrast = calculate_brightness_contrast(img_array)
    
    # 2. Dominant Colors
    dominant_colors = extract_dominant_colors(img_array)
    
    # 3. Text Extraction
    text_data = extract_text_with_ocr(img_array)
    
    # 4. Object Detection with Per-Object Contrast
    detected_objects = detect_objects_yolo(img_array)
    
    # 5. Face & Emotion Detection
    face_emotion = detect_faces_and_emotion(img_array)
    
    # Combine all metrics
    analysis_result = {
        'brightness': brightness_contrast['brightness'],
        'contrast': brightness_contrast['contrast'],
        'dominant_colors': dominant_colors,
        'text_content': text_data['text_content'],
        'word_count': text_data['word_count'],
        'face_count': face_emotion['face_count'],
        'detected_emotion': face_emotion['detected_emotion'],
        'detected_objects': detected_objects
    }
    
    return analysis_result
