from dotenv import load_dotenv

# Load environment variables immediately
load_dotenv()

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from typing import Optional
import os
import traceback

from app.models.analysis_models import AnalysisResult, GeminiTextDetection, GeminiAllDetection
from app.core.image_processor import (
    extract_youtube_thumbnail_url,
    fetch_image_bytes,
    run_full_analysis
)
from app.core.llm_generator import (
    generate_final_feedback,
    get_text_bounds_from_gemini,
    get_all_detection_data
)

# Initialize FastAPI app
app = FastAPI(
    title="Thumblytics API",
    description="AI-Powered YouTube Thumbnail Analyzer",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize and verify API configuration."""
    print("🚀 Initializing Thumblytics API v2.0...")
    
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ WARNING: GEMINI_API_KEY is not set in environment.")
    else:
        print("✅ GEMINI_API_KEY found")
    
    print("✅ API ready to analyze thumbnails with full Gemini integration!")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Thumblytics API",
        "version": "2.0.0",
        "detection": "Gemini-powered (no local DL models)"
    }


@app.post("/analyze-thumbnail", response_model=AnalysisResult)
async def analyze_thumbnail(
    youtube_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Analyze a YouTube thumbnail or uploaded image using Gemini AI.
    
    Accepts either:
    - youtube_url: YouTube video URL (extracts thumbnail)
    - file: Direct image upload
    """
    
    # Validate input
    if not youtube_url and not file:
        raise HTTPException(
            status_code=400,
            detail="Either youtube_url or file must be provided"
        )
    
    try:
        # ===== STEP 0: Get Image Bytes =====
        if youtube_url:
            print(f"📺 Extracting thumbnail from YouTube URL...")
            thumbnail_url = extract_youtube_thumbnail_url(youtube_url)
            if not thumbnail_url:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid YouTube URL format"
                )
            image_bytes = await fetch_image_bytes(thumbnail_url)
            print(f"✅ Thumbnail fetched: {len(image_bytes)} bytes")
        else:
            print(f"📁 Processing uploaded file: {file.filename}")
            image_bytes = await file.read()
            print(f"✅ File loaded: {len(image_bytes)} bytes")
        
        # ===== STEP 1: Get Text Bounds from Gemini =====
        print("📝 Detecting text bounds with Gemini...")
        gemini_text_dict = await run_in_threadpool(get_text_bounds_from_gemini, image_bytes)
        
        try:
            gemini_text_bounds = GeminiTextDetection(**gemini_text_dict)
            detected_blocks = len(gemini_text_bounds.detected_text_blocks)
            print(f"✅ Gemini detected {detected_blocks} text block(s)")
        except Exception as e:
            print(f"⚠️ Text bounds validation issue: {e}")
            gemini_text_bounds = GeminiTextDetection(detected_text_blocks=[])
        
        # ===== STEP 2: Run CV Analysis (Brightness, Contrast, Colors, OCR) =====
        print("🔍 Running CV analysis (brightness, contrast, colors)...")
        cv_analysis_data = await run_in_threadpool(
            run_full_analysis,
            image_bytes,
            gemini_text_bounds.model_dump()
        )
        print("✅ CV analysis complete")
        
        # ===== STEP 3: Get Object & Emotion Detection from Gemini =====
        print("🤖 Detecting objects, faces, and emotions with Gemini...")
        detection_dict = await run_in_threadpool(get_all_detection_data, image_bytes)
        
        try:
            detection_data = GeminiAllDetection(**detection_dict)
            print(f"✅ Detected {len(detection_data.detected_objects)} objects, "
                  f"{detection_data.face_count} face(s), "
                  f"emotion: {detection_data.detected_emotion or 'None'}")
        except Exception as e:
            print(f"⚠️ Detection validation issue: {e}")
            traceback.print_exc()
            detection_data = GeminiAllDetection(
                detected_objects=[],
                face_count=0,
                detected_emotion=None
            )
        
        # ===== STEP 4: Merge CV + Detection Data =====
        analysis_data = {
            **cv_analysis_data,
            'detected_objects': [obj.model_dump() for obj in detection_data.detected_objects],
            'face_count': detection_data.face_count,
            'detected_emotion': detection_data.detected_emotion
        }
        
        # ===== STEP 5: Generate Final LLM Feedback =====
        print("💡 Generating AI suggestions...")
        llm_result = await run_in_threadpool(generate_final_feedback, image_bytes, analysis_data)
        print(f"✅ AI feedback generated (Score: {llm_result['attractiveness_score']}/100)")
        
        # ===== STEP 6: Combine & Return Final Result =====
        final_result = AnalysisResult(
            average_brightness=analysis_data['average_brightness'],
            contrast_level=analysis_data['contrast_level'],
            dominant_colors=analysis_data['dominant_colors'],
            word_count=analysis_data['word_count'],
            text_content=analysis_data['text_content'],
            face_count=analysis_data['face_count'],
            detected_emotion=analysis_data['detected_emotion'],
            detected_objects=detection_data.detected_objects,
            attractiveness_score=llm_result['attractiveness_score'],
            ai_suggestions=llm_result['ai_suggestions']
        )
        
        print(f"🎉 Analysis complete! Score: {final_result.attractiveness_score}/100")
        return final_result
        
    except HTTPException:
        raise
    except Exception as e:
        if "GEMINI_API_KEY" in str(e):
            print(f"❌ API Key Error: {e}")
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY environment variable is not configured correctly."
            )
        
        print(f"❌ Analysis error: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)