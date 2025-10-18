# backend/analysis_models.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


# --- 1. Specialized Text Detection Model (For Gemini Call 1) ---
class TextBoundingBox(BaseModel):
    """Bounding box and text content detected by Gemini."""
    # Allow any extra metadata Gemini may add (e.g., $defs references)
    model_config = ConfigDict(extra='allow')

    box_normalized: List[int] = Field(..., description="[xmin, ymin, xmax, ymax] normalized to 0–1000.")
    text_label: str = Field(..., description="The raw text content extracted by Gemini for this box.")


class GeminiTextDetection(BaseModel):
    """Structured output for Gemini’s text detection step."""
    # Allow unknown or schema-related keys like $defs, properties, etc.
    model_config = ConfigDict(extra='allow')

    detected_text_blocks: Optional[List[TextBoundingBox]] = Field(
        default_factory=list,
        description="List of text bounding boxes detected by Gemini."
    )


# --- 2. Final Feedback Model (For Gemini Call 2) ---
class LLMFeedback(BaseModel):
    """Model for the final, synthesized output from Gemini."""
    model_config = ConfigDict(extra='allow')

    attractiveness_score: int = Field(..., ge=0, le=100,
        description="Final attractiveness score from 0 to 100.")
    ai_suggestions: List[str] = Field(..., min_length=5, max_length=5,
        description="Exactly 5 concise, actionable suggestions for improvement.")


# --- 3. Object Analysis Model ---
class ObjectAnalysis(BaseModel):
    """Analysis details for a single detected object."""
    model_config = ConfigDict(extra='allow')

    label: str
    confidence: float
    bbox: List[int]
    contrast_score_vs_bg: float


# --- 4. Final Combined API Response ---
class AnalysisResult(BaseModel):
    """Final combined response returned by the /analyze-thumbnail API."""
    # Allow extra keys to prevent Pydantic errors from any schema-like content
    model_config = ConfigDict(extra='allow')

    # Core Metrics (OpenCV/PyTesseract)
    average_brightness: float
    contrast_level: float
    dominant_colors: List[str]
    word_count: int
    text_content: str

    # DL/CV Metrics (DeepFace/YOLO/OpenCV)
    face_count: int
    detected_emotion: Optional[str] = None
    detected_objects: List[ObjectAnalysis]

    # LLM Output (Gemini)
    attractiveness_score: int
    ai_suggestions: List[str]

def clean_gemini_schema(data):
    """
    Clean Gemini API responses that accidentally return JSON schema-like structures.
    - Removes $defs, properties, anyOf, etc.
    - Returns a dictionary that fits GeminiTextDetection.
    """
    if not isinstance(data, dict):
        return {}

    # --- Case 1: Gemini returned an OpenAPI-like schema ---
    if "properties" in data or "$defs" in data or "anyOf" in str(data):
        print("⚠️ Gemini returned a schema definition, cleaning it up...")

        # Try to salvage any real data nested under it
        if "detected_text_blocks" in data.get("properties", {}):
            # If it has a nested schema, remove it and start clean
            return {"detected_text_blocks": []}

        # Just wipe it clean — no real data exists
        return {"detected_text_blocks": []}

    # --- Case 2: Normal response but with extra junk ---
    cleaned = {}
    for k, v in data.items():
        if k in ("$defs", "additionalProperties", "type", "properties"):
            continue
        if isinstance(v, dict):
            cleaned[k] = clean_gemini_schema(v)
        elif isinstance(v, list):
            cleaned[k] = [clean_gemini_schema(i) if isinstance(i, dict) else i for i in v]
        else:
            cleaned[k] = v

    # Always ensure detected_text_blocks is a list
    if "detected_text_blocks" not in cleaned:
        cleaned["detected_text_blocks"] = []

    return cleaned
