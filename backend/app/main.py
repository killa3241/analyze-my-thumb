from dotenv import load_dotenv

# Load environment variables from the .env file immediately.
# This must happen before any imports that rely on environment variables (like llm_generator).
load_dotenv()

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from typing import Optional
import asyncio
import os
import traceback

from app.models.analysis_models import AnalysisResult, GeminiTextDetection
from app.core.image_processor import (
    extract_youtube_thumbnail_url,
    fetch_image_bytes,
    run_full_analysis
)
from app.core.llm_generator import generate_final_feedback, get_text_bounds_from_gemini

# Initialize FastAPI app
app = FastAPI(
    title="Thumblytics API",
    description="AI-Powered YouTube Thumbnail Analyzer",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize heavy models once at startup."""
    print("🚀 Initializing Thumblytics API...")
    
    # Check for the key here (redundant now, but a good final verification)
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ WARNING: GEMINI_API_KEY is not set in environment.")
    else:
        print("✓ GEMINI_API_KEY found")
    
    # TODO: Initialize YOLOv8n model here
    # global _yolo_model
    # _yolo_model = YOLO('yolov8n.pt')
    
    print("✓ API ready to analyze thumbnails!")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Thumblytics API",
        "version": "1.0.0"
    }


@app.post("/analyze-thumbnail", response_model=AnalysisResult)
async def analyze_thumbnail(
    youtube_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Analyze a YouTube thumbnail or uploaded image.
    
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
        # Get image bytes
        if youtube_url:
            print(f"📺 Extracting thumbnail from YouTube URL...")
            thumbnail_url = extract_youtube_thumbnail_url(youtube_url)
            if not thumbnail_url:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid YouTube URL format"
                )
            image_bytes = await fetch_image_bytes(thumbnail_url)
            print(f"✓ Thumbnail fetched: {len(image_bytes)} bytes")
        else:
            # Read uploaded file
            print(f"📁 Processing uploaded file: {file.filename}")
            image_bytes = await file.read()
            print(f"✓ File loaded: {len(image_bytes)} bytes")
        
        # --- STEP 1: Get text bounds from Gemini ---
        print("📝 Detecting text bounds with Gemini...")
        gemini_dict = await run_in_threadpool(get_text_bounds_from_gemini, image_bytes)
        
        # --- STEP 2: Validate and convert to Pydantic model ---
        try:
            gemini_text_bounds = GeminiTextDetection(**gemini_dict)
            detected_blocks = len(gemini_text_bounds.detected_text_blocks)
            print(f"✅ Gemini detected {detected_blocks} text block(s)")
        except Exception as e:
            print(f"⚠️ Gemini validation issue: {e}")
            traceback.print_exc()
            gemini_text_bounds = GeminiTextDetection(detected_text_blocks=[])
        
        # --- STEP 3: Run CV/DL analysis ---
        print("🔍 Running CV/DL analysis...")
        analysis_data = await run_in_threadpool(
            run_full_analysis, 
            image_bytes, 
            gemini_text_bounds.model_dump()  # Pass as dict to avoid serialization issues
        )
        print("✓ CV/DL analysis complete")
        
        # --- STEP 4: Generate LLM feedback ---
        print("🤖 Generating AI suggestions...")
        llm_result = await generate_final_feedback(image_bytes, analysis_data)
        print(f"✓ AI feedback generated (Score: {llm_result['attractiveness_score']}/100)")
        
        # --- STEP 5: Combine results ---
        final_result = AnalysisResult(
            average_brightness=analysis_data['average_brightness'],
            contrast_level=analysis_data['contrast_level'],
            dominant_colors=analysis_data['dominant_colors'],
            word_count=analysis_data['word_count'],
            text_content=analysis_data['text_content'],
            face_count=analysis_data['face_count'],
            detected_emotion=analysis_data['detected_emotion'],
            detected_objects=analysis_data['detected_objects'],
            attractiveness_score=llm_result['attractiveness_score'],
            ai_suggestions=llm_result['ai_suggestions']
        )
        
        print(f"✅ Analysis complete! Score: {final_result.attractiveness_score}/100")
        return final_result
        
    except HTTPException:
        raise
    except Exception as e:
        # Check if the error is due to the key being missing
        if "GEMINI_API_KEY" in str(e):
            print(f"❌ API Key Error: {e}")
            raise HTTPException(
                status_code=500,
                detail="API Key Error: GEMINI_API_KEY environment variable is not configured correctly."
            )
        
        print(f"❌ Analysis error: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    # Use 0.0.0.0 binding for robust local network access
    uvicorn.run(app, host="0.0.0.0", port=8000)