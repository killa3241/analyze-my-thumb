import json
import os
from typing import Dict
from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch

from app.models.analysis_models import LLMFeedback


async def generate_thumbnail_feedback(analysis_data: Dict) -> Dict[str, any]:
    """
    Generate attractiveness score and suggestions using Google Gemini API.
    
    Args:
        analysis_data: Dictionary containing all CV/DL metrics
        
    Returns:
        Dictionary with 'attractiveness_score' (int) and 'ai_suggestions' (List[str])
    """
    
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    
    # Initialize Gemini client
    client = genai.Client(api_key=api_key)
    
    # Build structured prompt
    system_prompt = """You are an Expert YouTube Thumbnail Consultant. Analyze the provided metrics and give actionable feedback.

Your task is to:
1. Evaluate the thumbnail's attractiveness based on proven YouTube best practices
2. Provide exactly 5 concise, actionable suggestions to improve click-through rate
3. Focus on: Brightness, Contrast (especially per-object contrast vs background), Text readability, Emotional impact, and Visual hierarchy

Consider these factors:
- Brightness: Optimal range is 80-200 (0=dark, 255=bright)
- Contrast: Higher is better, especially for key elements vs background
- Faces with expressive emotions get 38% more clicks
- Text should be 3-5 words maximum for mobile readability
- Clear visual hierarchy with one dominant element"""

    # Format metrics as structured JSON
    metrics_json = json.dumps({
        "brightness": round(analysis_data.get('brightness', 0), 2),
        "contrast": round(analysis_data.get('contrast', 0), 2),
        "dominant_colors": analysis_data.get('dominant_colors', []),
        "text_content": analysis_data.get('text_content', 'None'),
        "word_count": analysis_data.get('word_count', 0),
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
    
    user_prompt = f"""Analyze this YouTube thumbnail based on the following metrics:

{metrics_json}

Provide your expert analysis with an attractiveness score (0-100) and exactly 5 actionable suggestions."""

    # Define response schema for structured output
    response_schema = {
        "type": "object",
        "properties": {
            "attractiveness_score": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "Overall attractiveness score from 0 to 100"
            },
            "ai_suggestions": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 5,
                "maxItems": 5,
                "description": "Exactly 5 concise, actionable suggestions"
            }
        },
        "required": ["attractiveness_score", "ai_suggestions"]
    }
    
    try:
        # Generate response with structured output
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=f"{system_prompt}\n\n{user_prompt}",
            config=GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )
        
        # Parse JSON response
        result_json = json.loads(response.text)
        
        # Validate with Pydantic
        feedback = LLMFeedback(**result_json)
        
        return {
            'attractiveness_score': feedback.attractiveness_score,
            'ai_suggestions': feedback.ai_suggestions
        }
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        # Return a fallback response instead of failing
        return {
            'attractiveness_score': 50,
            'ai_suggestions': [
                "Unable to generate AI suggestions - API error occurred",
                "Ensure your thumbnail has good contrast between elements",
                "Use bold, large text (3-5 words max) for mobile readability",
                "Consider adding a human face with expressive emotion",
                "Test thumbnail at small sizes (120x90px) for mobile visibility"
            ]
        }
