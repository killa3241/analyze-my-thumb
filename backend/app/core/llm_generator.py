import json
import os
from typing import Dict, List, Tuple
from google import genai
from google.genai import types
from io import BytesIO
from app.models.analysis_models import LLMFeedback, GeminiTextDetection

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
    Gemini can't handle $ref pointers properly.
    """
    # Get the raw schema
    schema = pydantic_model.model_json_schema()
    
    # Inline any $defs if they exist
    if "$defs" in schema:
        defs = schema.pop("$defs")
        
        def resolve_refs(obj):
            if isinstance(obj, dict):
                if "$ref" in obj:
                    # Extract the definition name
                    ref_path = obj["$ref"].split("/")[-1]
                    if ref_path in defs:
                        return resolve_refs(defs[ref_path].copy())
                return {k: resolve_refs(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [resolve_refs(item) for item in obj]
            return obj
        
        schema = resolve_refs(schema)
    
    # Remove Pydantic-specific keys that Gemini doesn't need
    schema.pop("title", None)
    schema.pop("additionalProperties", None)
    
    return schema


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
    Returns a dictionary (not a Pydantic model) to avoid schema conflicts.
    """
    image_part = types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')
    
    # Create a clean schema without $defs
    clean_schema = get_clean_schema_for_gemini(GeminiTextDetection)
    
    config = types.GenerateContentConfig(
        system_instruction=TEXT_DETECTION_SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=clean_schema,  # ✅ Now using a dict, not a Pydantic model
        temperature=0.0
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[image_part],
            config=config
        )
        
        # Parse as dict first
        result = json.loads(response.text)
        
        # Validate it matches our expected structure
        if "detected_text_blocks" not in result:
            print("⚠️ Gemini response missing 'detected_text_blocks', returning empty")
            return {"detected_text_blocks": []}
        
        return result
        
    except Exception as e:
        print(f"❌ Gemini text detection error: {e}")
        # Return safe fallback
        return {"detected_text_blocks": []}


# ----------------------------------------------------------------------
# 2. FINAL FEEDBACK FUNCTION
# ----------------------------------------------------------------------
async def generate_final_feedback(
    image_bytes: bytes, 
    analysis_data: Dict
) -> Dict[str, any]:
    """
    Generate attractiveness score and suggestions using Google Gemini API.
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
    
    metrics_json = json.dumps({
        "brightness": round(analysis_data.get('average_brightness', 0), 2),
        "contrast_level": round(analysis_data.get('contrast_level', 0), 2),
        "dominant_colors": analysis_data.get('dominant_colors', []),
        "word_count": analysis_data.get('word_count', 0),
        "text_content_extracted": analysis_data.get('text_content', 'None'),
        "face_count": analysis_data.get('face_count', 0),
        "detected_emotion": analysis_data.get('detected_emotion', 'N/A'),
        "detected_objects": [
            {
                "label": obj["label"],
                "confidence": round(obj["confidence"], 2),
                "contrast_vs_bg": round(obj["contrast_score_vs_bg"], 2)
            }
            for obj in analysis_data.get('detected_objects', [])
        ]
    }, indent=2)
    
    user_prompt = f"Analyze this YouTube thumbnail based on the following pre-calculated metrics:\n\n{metrics_json}\n\nDeliver your expert analysis with an attractiveness score (0-100) and exactly 5 actionable suggestions in the required JSON format."

    # Use clean schema for feedback too
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
        print(f"Gemini API error during feedback generation: {e}")
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