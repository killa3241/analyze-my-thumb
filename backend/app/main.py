from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from typing import Optional
import asyncio

from app.models.analysis_models import AnalysisResult
from app.core.image_processor import (
    extract_youtube_thumbnail_url,
    fetch_image_bytes,
    run_full_analysis
)
from app.core.llm_generator import generate_thumbnail_feedback

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
            thumbnail_url = extract_youtube_thumbnail_url(youtube_url)
            if not thumbnail_url:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid YouTube URL format"
                )
            image_bytes = await fetch_image_bytes(thumbnail_url)
        else:
            # Read uploaded file
            image_bytes = await file.read()
        
        # Run CPU-intensive analysis in threadpool
        print("🔍 Running CV/DL analysis...")
        analysis_data = await run_in_threadpool(run_full_analysis, image_bytes)
        
        # Generate LLM feedback (async)
        print("🤖 Generating AI suggestions...")
        llm_result = await generate_thumbnail_feedback(analysis_data)
        
        # Combine results
        final_result = AnalysisResult(
            average_brightness=analysis_data['brightness'],
            contrast_level=analysis_data['contrast'],
            dominant_colors=analysis_data['dominant_colors'],
            word_count=analysis_data['word_count'],
            text_content=analysis_data['text_content'],
            face_count=analysis_data['face_count'],
            detected_emotion=analysis_data['detected_emotion'],
            detected_objects=analysis_data['detected_objects'],
            attractiveness_score=llm_result['attractiveness_score'],
            ai_suggestions=llm_result['ai_suggestions']
        )
        
        print(f"✓ Analysis complete! Score: {final_result.attractiveness_score}/100")
        return final_result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
