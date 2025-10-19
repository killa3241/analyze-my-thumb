# backend/app/models/analysis_models.py

from pydantic import BaseModel, Field
from typing import List, Optional


# ----------------------------------------------------------------------
# GEMINI TEXT DETECTION MODELS
# ----------------------------------------------------------------------

class TextBlock(BaseModel):
    """Represents a single text block detected by Gemini."""
    box_normalized: List[int] = Field(..., description="Bounding box [xmin, ymin, xmax, ymax] normalized to 0-1000")
    text_label: str = Field(..., description="Exact text found in this region")


class GeminiTextDetection(BaseModel):
    """Response model for Gemini text detection."""
    detected_text_blocks: List[TextBlock] = Field(default_factory=list, description="List of detected text blocks")


# ----------------------------------------------------------------------
# GEMINI ALL DETECTION MODELS (Objects, Faces, Emotions)
# ----------------------------------------------------------------------

class DetectedObject(BaseModel):
    """Represents a single detected object."""
    label: str = Field(..., description="Object label (e.g., 'person', 'car', 'text_overlay')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    bbox: List[int] = Field(..., description="Bounding box [xmin, ymin, xmax, ymax] normalized to 0-1000")
    contrast_score_vs_bg: float = Field(..., ge=0.0, le=1.0, description="Contrast score vs background (0-1)")


class GeminiAllDetection(BaseModel):
    """Response model for comprehensive Gemini detection (objects + faces + emotions)."""
    detected_objects: List[DetectedObject] = Field(default_factory=list, description="All detected objects")
    face_count: int = Field(default=0, ge=0, description="Total number of faces detected")
    detected_emotion: Optional[str] = Field(None, description="Dominant emotion of the most prominent face")


# ----------------------------------------------------------------------
# LLM FEEDBACK MODEL
# ----------------------------------------------------------------------

class LLMFeedback(BaseModel):
    """Response model for final LLM analysis feedback."""
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
    
    # Face & Emotion (from Gemini)
    face_count: int = Field(..., description="Number of faces detected")
    detected_emotion: Optional[str] = Field(None, description="Dominant emotion")
    
    # Object Detection (from Gemini)
    detected_objects: List[DetectedObject] = Field(..., description="Detected objects with contrast scores")
    
    # AI Feedback
    attractiveness_score: int = Field(..., description="AI-generated attractiveness score (0-100)")
    ai_suggestions: List[str] = Field(..., description="5 actionable improvement suggestions")