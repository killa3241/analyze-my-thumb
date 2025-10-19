# backend/app/core/llm_generator.py

import json
import os
from typing import Dict, List, Tuple, Optional
from google import genai
from google.genai import types
from io import BytesIO

from app.models.analysis_models import LLMFeedback, GeminiAllDetection 

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
# 1. COMPREHENSIVE DETECTION FUNCTION (Phase 1)
# ----------------------------------------------------------------------

DETECTION_SYSTEM_INSTRUCTION = (
    "You are a hyper-accurate Computer Vision analysis tool specializing in YouTube thumbnail analysis. "
    "Your PRIMARY task is to identify and precisely locate ALL critical visual elements.\n\n"
    
    "**MANDATORY DETECTION CATEGORIES:**\n"
    "1. **FACES** - Detect ALL human faces/persons with high precision\n"
    "   - For EACH face, you MUST infer the dominant emotion\n"
    "   - Emotion labels: 'Shocked', 'Excited', 'Determined', 'Smirking', 'Angry', 'Fear', 'Happy', 'Sad', 'Surprised', 'Neutral'\n"
    "   - Label as 'face' or 'person'\n"
    "   - Include partial faces if visible\n\n"
    
    "2. **TEXT OVERLAYS** - All text regions (titles, captions, labels)\n"
    "   - Label as 'text_overlay' or include descriptive text label\n\n"
    
    "3. **MAIN OBJECTS** - Key visual elements that are CRITICAL to detect:\n"
    "   - **Animals** (elephant, lion, tiger, dog, cat, bird, dinosaur, fish, snake, etc.)\n"
    "   - **Logos and brands** (YouTube logo, OpenAI logo, company logos, brand marks)\n"
    "   - **Products and items** (phones, cameras, laptops, tools, weapons, gadgets, equipment)\n"
    "   - **Vehicles** (cars, planes, bikes, ships, trucks, motorcycles)\n"
    "   - **Natural elements** (fire, flames, water, mountains, trees, clouds, lightning)\n"
    "   - **Characters and creatures** (zombies, robots, monsters, aliens, superheroes)\n"
    "   - **Sports equipment** (soccer ball, basketball, baseball bat, tennis racket)\n"
    "   - **Visual effects and props** (arrows, circles, highlights, explosions, sparkles)\n"
    "   - **Food items** (pizza, burger, cake, etc.)\n"
    "   - Use descriptive, specific labels (e.g., 'elephant', 'baseball bat', 'fire effect', 'zombie character')\n\n"
    
    "**CRITICAL REQUIREMENTS:**\n"
    "- ALL bounding boxes MUST be normalized to 0-1000 scale (NOT 0-1, NOT pixel coordinates)\n"
    "- Provide accurate confidence scores (0.0-1.0)\n"
    "- For faces: emotion field is MANDATORY\n"
    "- DO NOT skip large, prominent objects - elephants, cars, logos MUST be detected\n"
    "- If an animal or object occupies >20% of the image, it MUST be in your response\n"
    "- Return valid JSON matching the exact schema provided\n"
    "- Prioritize detecting ALL visible elements, especially main subjects\n"
    "- When in doubt, include the object rather than excluding it\n\n"
    
    "**EXAMPLE OUTPUT:**\n"
    "For a thumbnail with an elephant and text:\n"
    "{\n"
    "  \"detected_objects\": [\n"
    "    {\n"
    "      \"label\": \"elephant\",\n"
    "      \"bbox_normalized\": [200, 400, 800, 900],\n"
    "      \"confidence\": 0.92\n"
    "    },\n"
    "    {\n"
    "      \"label\": \"text_overlay\",\n"
    "      \"bbox_normalized\": [300, 50, 700, 150],\n"
    "      \"confidence\": 0.88\n"
    "    }\n"
    "  ],\n"
    "  \"face_count\": 0,\n"
    "  \"detected_emotion\": null\n"
    "}"
)


def get_all_detection_data(image_bytes: bytes) -> Dict:
    """
    Uses Gemini to identify ALL objects, faces, and text regions.
    Returns a clean dictionary for main.py to process.
    
    Args:
        image_bytes: Raw image bytes
    
    Returns:
        Dictionary containing detected_objects list and face metadata
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
        
        # Ensure the result has the expected structure
        if "detected_objects" not in result:
            print("⚠️ Gemini returned result without 'detected_objects' key")
            result["detected_objects"] = []
        
        # Calculate face count and dominant emotion from detected objects
        faces = [
            obj for obj in result["detected_objects"] 
            if obj.get("label", "").lower() in ["face", "person", "human"]
        ]
        result["face_count"] = len(faces)
        
        # Get dominant emotion from the first face if available
        dominant_emotion = None
        if faces:
            # Prioritize faces with emotions
            for face in faces:
                if face.get("emotion") and face["emotion"].lower() != "neutral":
                    dominant_emotion = face["emotion"]
                    break
            # Fallback to first face emotion if all are neutral
            if not dominant_emotion and faces[0].get("emotion"):
                dominant_emotion = faces[0]["emotion"]
        
        result["detected_emotion"] = dominant_emotion
        
        print(f"✅ Gemini detection successful: {len(result['detected_objects'])} objects, {result['face_count']} faces")
        if faces:
            print(f"   👤 Faces detected with emotions: {[f.get('emotion', 'Unknown') for f in faces]}")
        
        # Log all detected objects for debugging
        if result['detected_objects']:
            print(f"   🎯 All detected elements:")
            for obj in result['detected_objects']:
                label = obj.get('label', 'unknown')
                confidence = obj.get('confidence', 0)
                print(f"      - {label} (confidence: {confidence:.2f})")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ Gemini response JSON parsing error: {e}")
        print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
        return {
            "detected_objects": [],
            "face_count": 0,
            "detected_emotion": None
        }
    except Exception as e:
        print(f"❌ Gemini all detection error: {e}")
        return {
            "detected_objects": [],
            "face_count": 0,
            "detected_emotion": None
        }


# ----------------------------------------------------------------------
# 2. FINAL FEEDBACK FUNCTION (Phase 2)
# ----------------------------------------------------------------------

def generate_final_feedback(
    image_bytes: bytes,
    analysis_data: Dict
) -> Dict[str, any]:
    """
    Generates attractiveness score and suggestions using the final, processed data.
    
    Args:
        image_bytes: Raw image bytes
        analysis_data: Dictionary containing all CV metrics and detection results
    
    Returns:
        Dictionary with 'attractiveness_score' and 'ai_suggestions'
    """
    
    # ----------------------------------------------------------------
    # DYNAMIC LABEL EXTRACTION: Inject specific object names into the prompt
    # ----------------------------------------------------------------
    detected_faces = analysis_data.get('detected_faces', [])
    detected_objects = analysis_data.get('detected_objects', [])
    
    # Construct dynamic narrative critique points for faces
    if len(detected_faces) >= 2:
        face_narrative = (
            f"Face 1 ({detected_faces[0].get('emotion', 'Unknown')} emotion, {detected_faces[0].get('position', 'unknown position')}): "
            f"Visually inspect and define a high-impact emotion.\n"
            f"Face 2 ({detected_faces[1].get('emotion', 'Unknown')} emotion, {detected_faces[1].get('position', 'unknown position')}): "
            f"Visually inspect and define a high-impact emotion.\n"
            "- **Critique the emotional disparity between the two subjects using specific marketing psychology principles.**"
        )
    elif len(detected_faces) == 1:
        face_narrative = (
            f"Face 1 ({detected_faces[0].get('emotion', 'Unknown')} emotion, {detected_faces[0].get('position', 'unknown position')}): "
            f"Visually inspect and define a high-impact emotion."
        )
    else:
        face_narrative = "No prominent faces detected. Focus on object composition and text readability."
    
    # ----------------------------------------------------------------
    # SYSTEM PROMPT: Maximally Refined
    # ----------------------------------------------------------------
    system_prompt = """You are an Elite YouTube Thumbnail Optimization AI. Your suggestions MUST be data-driven, highly specific, and focused exclusively on optimizing the Click-Through Rate (CTR) and visual psychology.

    CRITICAL INSTRUCTIONS:
    1. Provide an objective attractiveness score (0-100).
    2. Generate exactly 5 concise, actionable suggestions.
    3. **MANDATORY EXCLUSIONS:** Do NOT use the words 'vignette', 'sharpen', 'brightness', or 'highlight' as core verbs. Use professional, marketing-focused terms instead (e.g., 'Increase the visual disparity...', 'Amplify rim lighting...', 'Boost visibility...').
    4. **NARRATIVE FOCUS:** Analyze the emotional and visual contrast between the main subjects. Suggestions MUST address how to optimize the psychological tension.
    5. **DATA FOCUS:** If any Key Object Contrast Score is below 0.85, the first suggestion MUST be a technical fix to raise the contrast of that specific element.
    6. Use specific, quantifiable techniques (e.g., 'Isolate the subject with a 2-stop exposure drop in the background')."""

    image_part = types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')

    # Get the CROPPED image bytes (for text focus)
    cropped_text_bytes = analysis_data.get('cropped_image_bytes', b'')
    cropped_text_part = types.Part.from_bytes(data=cropped_text_bytes, mime_type='image/jpeg') if cropped_text_bytes else image_part
    
    # ----------------------------------------------------------------
    # USER PROMPT: Dynamic Input Payload
    # ----------------------------------------------------------------
    metrics_json = json.dumps({
        "average_brightness": round(analysis_data.get('average_brightness', 0), 2),
        "contrast_level": round(analysis_data.get('contrast_level', 0), 2),
        "dominant_colors": analysis_data.get('dominant_colors', []),
        "word_count_ocr_RESULT": analysis_data.get('word_count', 0),
        "text_content_ocr_RESULT": analysis_data.get('text_content', 'None'), 
        "face_count": analysis_data.get('face_count', 0),
        "dominant_emotion": analysis_data.get('detected_emotion', 'N/A'),
        "detected_faces": [
            {
                "emotion": face.get("emotion", "Unknown"),
                "position": face.get("position", "unknown"),
                "contrast_vs_bg": round(face.get("contrast_score_vs_bg", 0.5), 2)
            }
            for face in detected_faces
        ],
        "key_object_contrasts": [
            {
                "label": obj.get("label", "Unknown"),
                "contrast_vs_bg": round(obj.get("contrast_score_vs_bg", 0.5), 2)
            }
            for obj in detected_objects
        ]
    }, indent=2)

    user_prompt = f"""
    Analyze the visual composition in the image. Use the provided original image and the cropped text image for visual context.

    **CRITICAL INSTRUCTION:** (Self-Correction): Visually determine the actual text and critique its composition/readability based on that corrected text.

    **EMOTIONAL GROUNDING (Dynamic Subjects):**
    {face_narrative}

    QUANTITATIVE DATA:
    {metrics_json}

    Based on all inputs, provide your score and 5 specific, non-generic suggestions in the required JSON format.
    """
    
    # Use clean schema
    response_schema = get_clean_schema_for_gemini(LLMFeedback)
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[image_part, cropped_text_part, user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.8,
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
        
    except json.JSONDecodeError as e:
        print(f"❌ Gemini feedback JSON parsing error: {e}")
        print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
        return _get_fallback_feedback()
    except Exception as e:
        print(f"❌ Gemini API error during feedback generation: {e}")
        return _get_fallback_feedback()


def _get_fallback_feedback() -> Dict[str, any]:
    """Returns fallback feedback when Gemini API fails."""
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