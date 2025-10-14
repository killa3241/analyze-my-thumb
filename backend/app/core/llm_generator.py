import json
from typing import Dict, List
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

# Placeholder path - assumes GGUF model is already downloaded
LLAMA_MODEL_PATH = "/path/to/your/quantized_mistral_7b.gguf"

# Global LLM instance (loaded once at startup)
_llm_instance = None


def initialize_llm():
    """Initialize the LLM once at application startup."""
    global _llm_instance
    if Llama is None:
        print("WARNING: llama-cpp-python not installed. Using mock LLM responses.")
        return
    
    try:
        _llm_instance = Llama(
            model_path=LLAMA_MODEL_PATH,
            n_threads=4,
            n_ctx=2048,
            verbose=False
        )
        print(f"✓ LLM loaded successfully from {LLAMA_MODEL_PATH}")
    except Exception as e:
        print(f"WARNING: Failed to load LLM: {e}. Using mock responses.")
        _llm_instance = None


def generate_thumbnail_feedback(analysis_data: Dict) -> Dict[str, any]:
    """
    Generate attractiveness score and suggestions using LLM.
    
    Args:
        analysis_data: Dictionary containing all CV/DL metrics
        
    Returns:
        Dictionary with 'attractiveness_score' (int) and 'ai_suggestions' (List[str])
    """
    
    # Build structured prompt
    system_prompt = """You are an Expert YouTube Thumbnail Consultant. Analyze the provided metrics and give actionable feedback.

Your response MUST be valid JSON with this exact structure:
{
  "attractiveness_score": <number 0-100>,
  "ai_suggestions": [
    "suggestion 1",
    "suggestion 2",
    "suggestion 3",
    "suggestion 4",
    "suggestion 5"
  ]
}

Provide exactly 5 concise, actionable suggestions to improve the thumbnail's click-through rate."""

    user_prompt = f"""Analyze this YouTube thumbnail:

METRICS:
- Brightness: {analysis_data.get('brightness', 0):.2f} (0=dark, 255=bright)
- Contrast: {analysis_data.get('contrast', 0):.2f} (higher=more contrast)
- Dominant Colors: {', '.join(analysis_data.get('dominant_colors', []))}
- Text Content: "{analysis_data.get('text_content', 'None')}" ({analysis_data.get('word_count', 0)} words)
- Faces Detected: {analysis_data.get('face_count', 0)}
- Dominant Emotion: {analysis_data.get('detected_emotion', 'N/A')}
- Detected Objects: {len(analysis_data.get('detected_objects', []))}

OBJECT DETAILS:
{_format_objects(analysis_data.get('detected_objects', []))}

Based on best practices for viral YouTube thumbnails, provide your analysis."""

    if _llm_instance is None:
        # Mock response when LLM not available
        return _generate_mock_response(analysis_data)
    
    try:
        # Generate response
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = _llm_instance(
            full_prompt,
            max_tokens=512,
            temperature=0.7,
            stop=["</s>", "\n\n\n"]
        )
        
        # Extract and parse JSON
        response_text = response['choices'][0]['text'].strip()
        
        # Try to find JSON in response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            # Validate structure
            if 'attractiveness_score' in result and 'ai_suggestions' in result:
                return {
                    'attractiveness_score': int(result['attractiveness_score']),
                    'ai_suggestions': result['ai_suggestions'][:5]  # Ensure max 5
                }
        
        # Fallback if parsing fails
        return _generate_mock_response(analysis_data)
        
    except Exception as e:
        print(f"LLM generation error: {e}")
        return _generate_mock_response(analysis_data)


def _format_objects(objects: List[Dict]) -> str:
    """Format detected objects for prompt."""
    if not objects:
        return "No objects detected"
    
    lines = []
    for i, obj in enumerate(objects[:10], 1):  # Limit to 10 objects
        lines.append(
            f"  {i}. {obj['label']} "
            f"(confidence: {obj['confidence']:.2f}, "
            f"contrast vs bg: {obj['contrast_score_vs_bg']:.2f})"
        )
    return '\n'.join(lines)


def _generate_mock_response(analysis_data: Dict) -> Dict[str, any]:
    """Generate rule-based mock response when LLM unavailable."""
    score = 50  # Base score
    suggestions = []
    
    # Brightness scoring
    brightness = analysis_data.get('brightness', 128)
    if brightness < 80:
        score -= 10
        suggestions.append("Increase overall brightness - thumbnails appear darker on mobile")
    elif brightness > 200:
        score -= 5
        suggestions.append("Reduce excessive brightness to avoid washed-out appearance")
    else:
        score += 10
    
    # Contrast scoring
    contrast = analysis_data.get('contrast', 0)
    if contrast < 30:
        score -= 15
        suggestions.append("Boost contrast to make elements pop - use darker backgrounds with brighter subjects")
    else:
        score += 10
    
    # Face detection
    face_count = analysis_data.get('face_count', 0)
    if face_count == 0:
        suggestions.append("Consider adding a human face - thumbnails with faces get 38% more clicks")
    elif face_count > 0:
        score += 15
        emotion = analysis_data.get('detected_emotion', 'neutral')
        if emotion in ['happy', 'surprise']:
            score += 5
    
    # Text analysis
    word_count = analysis_data.get('word_count', 0)
    if word_count == 0:
        suggestions.append("Add bold, large text (3-5 words max) highlighting the key benefit")
    elif word_count > 8:
        score -= 5
        suggestions.append("Reduce text to 3-5 impactful words - too much text reduces readability")
    else:
        score += 5
    
    # Object detection
    objects = analysis_data.get('detected_objects', [])
    if len(objects) > 10:
        suggestions.append("Simplify composition - too many elements create visual clutter")
    
    # Per-object contrast
    low_contrast_objects = [o for o in objects if o.get('contrast_score_vs_bg', 0) < 1.5]
    if low_contrast_objects:
        suggestions.append(f"Increase contrast around {low_contrast_objects[0]['label']} - add outline or shadow")
    
    # Fill remaining suggestions
    default_suggestions = [
        "Use the rule of thirds - position key elements at intersection points",
        "Test thumbnail at small sizes (120x90px) - it must be readable on mobile",
        "Add vibrant colors from the complementary color palette",
        "Create visual hierarchy - make one element clearly dominant",
        "Use arrows or circles to direct viewer attention to key elements"
    ]
    
    while len(suggestions) < 5:
        for s in default_suggestions:
            if s not in suggestions:
                suggestions.append(s)
                break
    
    # Clamp score
    score = max(0, min(100, score))
    
    return {
        'attractiveness_score': score,
        'ai_suggestions': suggestions[:5]
    }
