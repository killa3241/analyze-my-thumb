import json
import os
from typing import Dict
from google import genai
from google.genai import types
from app.models.analysis_models import LLMFeedback, GeminiTextDetection, GeminiAllDetection

# --- Constants & Initialization ---
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")
client = genai.Client(api_key=API_KEY)


# ----------------------------------------------------------------------
# HELPER: Convert Pydantic model to clean JSON Schema
# ----------------------------------------------------------------------
def get_clean_schema_for_gemini(pydantic_model):
    """
    Converts a Pydantic model to a JSON Schema dict WITHOUT $defs references.
    Aggressively removes all problematic fields that cause Gemini API errors.
    """
    schema = pydantic_model.model_json_schema()
    
    # Inline any $defs if they exist
    if "$defs" in schema:
        defs = schema.pop("$defs")
        
        def resolve_refs(obj):
            if isinstance(obj, dict):
                if "$ref" in obj:
                    ref_path = obj["$ref"].split("/")[-1]
                    if ref_path in defs:
                        return resolve_refs(defs[ref_path].copy())
                return {k: resolve_refs(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [resolve_refs(item) for item in obj]
            return obj
        
        schema = resolve_refs(schema)
    
    # Recursively remove problematic fields
    def clean_schema(obj):
        if isinstance(obj, dict):
            # Remove all problematic keys
            keys_to_remove = [
                "title", 
                "additionalProperties", 
                "default",
                "$defs",
                "$ref"
            ]
            for key in keys_to_remove:
                obj.pop(key, None)
            
            # Recursively clean nested objects
            for key, value in list(obj.items()):
                obj[key] = clean_schema(value)
            
            return obj
        elif isinstance(obj, list):
            return [clean_schema(item) for item in obj]
        return obj
    
    return clean_schema(schema)


# ----------------------------------------------------------------------
# 1. TEXT DETECTION FUNCTION
# ----------------------------------------------------------------------
TEXT_DETECTION_SYSTEM_INSTRUCTION = (
    "You are an expert computer vision model specializing in YouTube thumbnail text detection. "
    "Your sole task is to accurately identify all distinct, human-readable text blocks in the image, "
    "ignoring small artifacts or watermarks. "
    "Provide the bounding box coordinates [xmin, ymin, xmax, ymax] normalized to a 0-1000 scale "
    "based on the image's dimensions. The 'text_label' field must contain the exact, case-sensitive text found in that box. "
    "Return a JSON object with a 'detected_text_blocks' array. Each item must have 'box_normalized' (array of 4 integers) "
    "and 'text_label' (string). If no text is found, return an empty array."
)


def get_text_bounds_from_gemini(image_bytes: bytes) -> Dict:
    """
    Uses Gemini to identify text regions and return structured bounding box data.
    Returns a dictionary to avoid schema conflicts.
    """
    image_part = types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')
    
    # Create a clean schema without problematic fields
    clean_schema = get_clean_schema_for_gemini(GeminiTextDetection)
    
    config = types.GenerateContentConfig(
        system_instruction=TEXT_DETECTION_SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=clean_schema,
        temperature=0.0
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[image_part],
            config=config
        )
        
        result = json.loads(response.text)
        
        if "detected_text_blocks" not in result:
            print("⚠️ Gemini response missing 'detected_text_blocks', returning empty")
            return {"detected_text_blocks": []}
        
        return result
        
    except Exception as e:
        print(f"❌ Gemini text detection error: {e}")
        return {"detected_text_blocks": []}


# ----------------------------------------------------------------------
# 2. OBJECT & EMOTION DETECTION FUNCTION
# ----------------------------------------------------------------------

DETECTION_SYSTEM_INSTRUCTION = (
    "You are a hyper-accurate Computer Vision analysis tool. Your sole purpose is to locate and label "
    "critical visual elements in the thumbnail. "
    "Identify and label all: **1) Faces**, **2) Text Overlays**, and **3) Main Objects** (e.g., zombie, baseball bat). "
    "For every face detected, infer the dominant **emotion** from a commercial thumbnail perspective. "
    "Use expressive labels like: **'Shocked', 'Excited', 'Determined', 'Smirking', 'Angry', or 'Fear'**. "
    "If the emotion is weak, use 'Neutral'. Place this in the 'emotion' field. "
    "Return the output in the requested JSON schema. All coordinates must be normalized to a 0-1000 scale."
)


def get_all_detection_data(image_bytes: bytes) -> Dict:
    """
    Uses Gemini to detect objects, faces, and emotions.
    Returns a dictionary with detected_objects, face_count, and detected_emotion.
    """
    image_part = types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')
    
    # Create clean schema
    clean_schema = get_clean_schema_for_gemini(GeminiAllDetection)
    
    config = types.GenerateContentConfig(
        system_instruction=DETECTION_SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=clean_schema,
        temperature=0.2
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[image_part],
            config=config
        )
        
        result = json.loads(response.text)
        
        # Validate expected structure
        if "detected_objects" not in result:
            result["detected_objects"] = []
        if "face_count" not in result:
            result["face_count"] = 0
        if "detected_emotion" not in result:
            result["detected_emotion"] = None
        
        return result
        
    except Exception as e:
        print(f"❌ Gemini detection error: {e}")
        return {
            "detected_objects": [],
            "face_count": 0,
            "detected_emotion": None
        }


# ----------------------------------------------------------------------
# 3. FINAL FEEDBACK FUNCTION
# ----------------------------------------------------------------------
def generate_final_feedback(
    image_bytes: bytes,
    analysis_data: Dict
) -> Dict[str, any]:
    """
    Generate attractiveness score and suggestions using Google Gemini API.
    This is a synchronous function that will be called via run_in_threadpool.
    """
    system_prompt = """You are an Expert YouTube Thumbnail Consultant. Analyze the provided visual and quantitative metrics to deliver actionable feedback.

Your task is to:
1. Evaluate the thumbnail's attractiveness based on proven YouTube best practices.
2. Provide exactly 5 concise, actionable suggestions to improve click-through rate.
3. Focus on: Brightness, Overall Contrast, Text readability (font, size, contrast, word count), Emotional impact, and Visual hierarchy.

Consider these industry best practices:
- Brightness: Optimal range is 80-200 (0=dark, 255=bright).
- Contrast: A high Weber contrast (especially for key objects vs. background) is critical for small screens.
- Faces with clear, expressive emotions get significantly higher engagement.
- Text should be 3-5 words maximum for mobile readability."""

    image_part = types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')

    # Get the CROPPED image bytes (for text focus)
    cropped_text_bytes = analysis_data.pop('cropped_image_bytes', b'')
    cropped_text_part = types.Part.from_bytes(data=cropped_text_bytes, mime_type='image/jpeg') if cropped_text_bytes else image_part
    
# In backend/app/core/llm_generator.py, within the generate_final_feedback function

    # 1. Build the Quantitative Data Payload (metrics_json)
    metrics_json = json.dumps({
        # Core Visual Metrics
        "average_brightness": round(analysis_data.get('average_brightness', 0), 2),
        "contrast_level": round(analysis_data.get('contrast_level', 0), 2),
        "dominant_colors": analysis_data.get('dominant_colors', []),
        
        # Text Metrics (Provided for Gemini to correct/validate)
        "word_count_ocr_RESULT": analysis_data.get('word_count', 0),
        "text_content_ocr_RESULT": analysis_data.get('text_content', 'None'), 
        
        # Emotion/Face Metrics (Derived from Gemini Detection)
        "face_count": analysis_data.get('face_count', 0),
        "dominant_emotion": analysis_data.get('detected_emotion', 'N/A'),
        
        # Key Object Contrast Metrics (For data-driven suggestions)
        "key_object_contrasts": [
            {
                "label": obj["label"],
                # Removed confidence, focusing on the highly actionable contrast score
                "contrast_vs_bg": round(obj.get("contrast_score_vs_bg", 0), 2)
            }
            for obj in analysis_data.get('detected_objects', [])
        ]
    }, indent=2)


    # 2. Build the User Prompt (Dynamic and Focused)
    user_prompt = f"""
    Analyze the composition and visual elements in the image. Use the provided original image and the cropped text image for visual context.

    **CRITICAL INSTRUCTION:** The raw OCR result is provided under 'text_content_ocr_RESULT'. **You must visually inspect the original image and the cropped text image to determine the actual, correct text on the thumbnail.** If the OCR result is inaccurate (e.g., 'YING LINQut'), use the corrected, intended text (e.g., 'DYING LIGHT IS PAIN') when formulating suggestions about word count or readability.

    **EMOTIONAL ANALYSIS FOCUS:** The detected emotion is '{analysis_data.get('detected_emotion', 'N/A')}'. Visually confirm this and generate suggestions to increase emotional impact, using more expressive states like 'Smirking', 'Determined', or 'Shocked'.

    QUANTITATIVE DATA:
    {metrics_json}

    Based on all inputs, provide your score and 5 specific, non-generic suggestions in the required JSON format.
    """
    # Use clean schema
    response_schema = get_clean_schema_for_gemini(LLMFeedback)
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[image_part, user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )
        
        result_json = json.loads(response.text)
        feedback = LLMFeedback(**result_json)
        
        return {
            'attractiveness_score': feedback.attractiveness_score,
            'ai_suggestions': feedback.ai_suggestions
        }
        
    except Exception as e:
        print(f"❌ Gemini API error during feedback generation: {e}")
        return {
            'attractiveness_score': 45,
            'ai_suggestions': [
                "AI feedback generation failed (API error or timeout).",
                "Ensure your key subject has maximum contrast against the background.",
                "Simplify text to 3-5 words for better mobile visibility.",
                "Use high-contrast color combinations (e.g., yellow text on black).",
                "Crop the main subject to fill at least 70% of the thumbnail area."
            ]
        }