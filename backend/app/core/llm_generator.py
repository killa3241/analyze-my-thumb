# backend/app/core/llm_generator.py - IMPROVED VERSION

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
# 1. COMPREHENSIVE DETECTION FUNCTION (Phase 1) - IMPROVED
# ----------------------------------------------------------------------

DETECTION_SYSTEM_INSTRUCTION = """You are a YouTube Thumbnail Object Detection AI. Your ONLY job is to detect and locate ALL visible objects, text, and faces in the image.

**CORE MISSION: DETECT EVERYTHING YOU SEE**

YOU MUST DETECT (in order of priority):

1. **PEOPLE & FACES** (HIGHEST PRIORITY)
   - ANY human face, person, or human-like figure
   - Partial faces, side profiles, back of heads
   - Multiple people in the same image
   - For each face/person, provide emotion: 'Shocked', 'Excited', 'Determined', 'Smirking', 'Angry', 'Fear', 'Happy', 'Sad', 'Surprised', 'Neutral'
   - Label: 'face', 'person', or 'human'

2. **CREATURES & CHARACTERS**
   - Zombies, monsters, aliens, robots, superheroes, villains
   - Fantasy creatures, animals (lions, elephants, dogs, cats, birds, dinosaurs)
   - Animated characters, cartoon figures
   - Label with specific name: 'zombie', 'monster', 'alien', 'robot', 'lion', 'elephant', etc.

3. **TEXT OVERLAYS** (CRITICAL)
   - ALL visible text regions, titles, captions, words
   - Even single words or letters
   - Label as: 'text_overlay' or 'text'

4. **OBJECTS & ITEMS**
   - Weapons (guns, swords, bats, knives)
   - Vehicles (cars, planes, motorcycles, trucks)
   - Electronics (phones, cameras, computers, controllers)
   - Tools and equipment
   - Sports items (balls, rackets, bats)
   - Food items
   - Label with specific name

5. **LOGOS & BRANDING**
   - YouTube logo, brand logos, company marks
   - Social media icons
   - Label: 'youtube_logo', 'brand_logo', etc.

6. **VISUAL EFFECTS**
   - Fire, explosions, smoke, lightning
   - Arrows, circles, highlights, annotations
   - Glowing effects, particle effects
   - Label descriptively: 'fire_effect', 'arrow_pointer', etc.

**CRITICAL RULES:**

✅ **SIZE THRESHOLD**: If ANY object occupies more than 15% of the image area, you MUST detect it
✅ **VISIBILITY THRESHOLD**: If you can see it, detect it - no exceptions
✅ **PROMINENCE RULE**: The most prominent/largest objects are TOP PRIORITY
✅ **MULTIPLE INSTANCES**: If there are 2 zombies, detect both separately
✅ **TEXT RULE**: If there's ANY readable text, detect the text region(s)

❌ **NEVER skip large, obvious subjects** - this is your #1 priority
❌ **NEVER return empty detected_objects if there are visible elements**
❌ **NEVER ignore the main subject of the thumbnail**

**BOUNDING BOX FORMAT:**
- Use normalized coordinates: [x_min, y_min, x_max, y_max]
- Scale: 0-1000 (NOT 0-1, NOT pixels)
- Example: [100, 200, 600, 800] means object spans from 10% to 60% horizontally

**CONFIDENCE SCORES:**
- 0.95-1.0: Extremely clear and obvious
- 0.85-0.94: Very clear
- 0.70-0.84: Clear but partially obscured
- 0.60-0.69: Visible but challenging

**OUTPUT FORMAT EXAMPLE:**
For a thumbnail with a zombie and a person with text:
```json
{
  "detected_objects": [
    {
      "label": "zombie",
      "bbox_normalized": [50, 100, 600, 900],
      "confidence": 0.95
    },
    {
      "label": "person",
      "bbox_normalized": [650, 200, 950, 850],
      "confidence": 0.92,
      "emotion": "Fear"
    },
    {
      "label": "text_overlay",
      "bbox_normalized": [100, 50, 500, 200],
      "confidence": 0.88
    }
  ],
  "face_count": 1,
  "detected_emotion": "Fear"
}
```

**SELF-CHECK BEFORE RESPONDING:**
1. Did I detect the LARGEST object in the image? ✓
2. Did I detect ALL visible faces/people? ✓
3. Did I detect ALL text regions? ✓
4. Is detected_objects empty when there are obvious elements? ✗ (This should NEVER happen)

REMEMBER: Your goal is MAXIMUM DETECTION, not minimal detection. When in doubt, INCLUDE the object."""


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
    
    # IMPROVED: Add explicit user prompt to force detection
    user_prompt = """Analyze this YouTube thumbnail image carefully. 

MANDATORY TASKS:
1. Identify and locate EVERY visible object, character, person, and text region
2. The LARGEST/most prominent subjects MUST be detected first
3. Provide bounding boxes for ALL elements you can see
4. For any faces/people, specify their emotion

START your analysis by describing what you see, then provide the JSON with ALL detections.

Remember: Empty detected_objects array is ONLY acceptable if the image is completely blank."""
    
    config = types.GenerateContentConfig(
        system_instruction=DETECTION_SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=clean_schema,
        temperature=0.1,  # Lower temperature for more consistent detection
        top_p=0.95,
        top_k=40
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[image_part, user_prompt],  # Added explicit prompt
            config=config
        )
        
        result = json.loads(response.text)
        
        # Ensure the result has the expected structure
        if "detected_objects" not in result:
            print("⚠️ Gemini returned result without 'detected_objects' key")
            result["detected_objects"] = []
        
        # WARNING: If no objects detected, log it prominently
        if len(result["detected_objects"]) == 0:
            print("⚠️⚠️⚠️ WARNING: Gemini returned ZERO detected objects!")
            print("⚠️⚠️⚠️ This likely indicates a detection failure. Consider:")
            print("   1. Image may be corrupted or unreadable")
            print("   2. Gemini API may be having issues")
            print("   3. Image format may not be compatible")
        
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
                bbox = obj.get('bbox_normalized', [])
                print(f"      - {label} (confidence: {confidence:.2f}, bbox: {bbox})")
        else:
            print("   ⚠️ NO OBJECTS DETECTED - This may indicate an issue")
        
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
        import traceback
        traceback.print_exc()
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