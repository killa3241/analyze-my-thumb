# backend/app/models/analysis_models.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

# --- RAW DETECTION MODEL (OUTPUT OF GEMINI CALL 1 - Before local CV processing) ---

class DetectedElement(BaseModel):
    """
    Represents a single element detected by Gemini. 
    This model is simple to avoid conflict and allows the contrast field to be optional
    because contrast is calculated *locally* later.
    """
    label: str = Field(..., description="Element label (e.g., 'face', 'OpenAI logo', 'text_overlay')")
    bbox_normalized: List[int] = Field(..., description="Bounding box [xmin, ymin, xmax, ymax] normalized to 0-1000")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    emotion: Optional[str] = Field(None, description="Dominant emotion if label is 'face'")
    contrast_score_vs_bg: Optional[float] = Field(None, description="Contrast score vs background (0-1), calculated locally")
    position: Optional[str] = Field(None, description="Position in thumbnail (e.g., 'left', 'center', 'right')")
    element_type: Optional[str] = Field(None, description="Type of element: 'face', 'object', or 'text'")


class DetectedFace(BaseModel):
    """
    Represents a detected face with emotion and position data.
    """
    label: str = Field(default="face", description="Always 'face' or 'person'")
    bbox_normalized: List[int] = Field(..., description="Bounding box [xmin, ymin, xmax, ymax] normalized to 0-1000")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    emotion: str = Field(..., description="Detected emotion (e.g., 'Shocked', 'Excited', 'Neutral')")
    contrast_score_vs_bg: Optional[float] = Field(None, description="Contrast score vs background (0-1)")
    position: Optional[str] = Field(None, description="Position in thumbnail (e.g., 'left', 'center', 'right')")


class GeminiAllDetection(BaseModel):
    """
    Response model for comprehensive Gemini detection (RAW DATA). 
    This model now serves the output of the initial detection step.
    """
    model_config = ConfigDict(extra='allow')
    detected_objects: List[DetectedElement] = Field(default_factory=list, description="All detected elements")
    face_count: int = Field(default=0, ge=0, description="Total number of faces detected")
    detected_emotion: Optional[str] = Field(None, description="Dominant emotion of the most prominent face")


# ----------------------------------------------------------------------
# GEMINI TEXT DETECTION MODELS (Used for PyTesseract cropping)
# ----------------------------------------------------------------------

class TextBlock(BaseModel):
    """Represents a single text block detected by Gemini."""
    box_normalized: List[int] = Field(..., description="Bounding box [xmin, ymin, xmax, ymax] normalized to 0-1000")
    text_label: str = Field(..., description="Exact text found in this region")

class GeminiTextDetection(BaseModel):
    """Response model for Gemini text detection."""
    model_config = ConfigDict(extra='allow')
    detected_text_blocks: List[TextBlock] = Field(default_factory=list, description="List of detected text blocks")


# ----------------------------------------------------------------------
# LLM FEEDBACK MODEL
# ----------------------------------------------------------------------

class LLMFeedback(BaseModel):
    """Response model for final LLM analysis feedback."""
    model_config = ConfigDict(extra='allow')
    attractiveness_score: int = Field(..., ge=0, le=100, description="Overall attractiveness score (0-100)")
    ai_suggestions: List[str] = Field(..., min_length=5, max_length=5, description="Exactly 5 actionable suggestions")


# ----------------------------------------------------------------------
# FINAL ANALYSIS RESULT (API Response)
# ----------------------------------------------------------------------

class AnalysisResult(BaseModel):
    """Complete analysis result returned to the client."""
    # CV Metrics
    average_brightness: float = Field(..., description="Average brightness (0-255)")
    contrast_level: float = Field(..., description="Overall contrast (std dev of grayscale)")
    dominant_colors: List[str] = Field(..., description="Top 5 dominant colors as hex codes")
    
    # Text Analysis
    word_count: int = Field(..., description="Number of words detected in thumbnail")
    text_content: str = Field(..., description="Extracted text content")
    
    # Face & Emotion (from Gemini/Processed)
    face_count: int = Field(..., description="Number of faces detected")
    detected_emotion: Optional[str] = Field(None, description="Dominant emotion")
    detected_faces: List[DetectedElement] = Field(default_factory=list, description="List of detected faces with emotions and positions")
    
    # Object Detection (Analyzed data ready for API) - NOW INCLUDES ALL NON-FACE, NON-TEXT OBJECTS
    detected_objects: List[DetectedElement] = Field(..., description="Detected objects (non-face, non-text) with contrast scores")
    
    # AI Feedback
    attractiveness_score: int = Field(..., description="AI-generated attractiveness score (0-100)")
    ai_suggestions: List[str] = Field(..., description="5 actionable improvement suggestions")