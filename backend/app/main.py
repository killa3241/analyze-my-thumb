from dotenv import load_dotenv

# Load environment variables immediately
load_dotenv()

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from typing import Optional
import os
import traceback

from app.models.analysis_models import AnalysisResult, GeminiAllDetection
from app.core.image_processor import (
    extract_youtube_thumbnail_url,
    fetch_image_bytes,
    run_full_analysis
)
from app.core.llm_generator import (
    generate_final_feedback,
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
    allow_origins=[
        "http://localhost:5173",      # Local development
        "http://localhost:8080",      # Local development
        "http://localhost:3000",      # Local development
        "https://thumbnail-analyzer.netlify.app",  # Old Vercel URL (if needed)
        "https://*.netlify.app",        # All Vercel preview deployments
    ],
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
    """Analyze a YouTube thumbnail or uploaded image."""
    
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
                raise HTTPException(status_code=400, detail="Invalid YouTube URL format")
            image_bytes = await fetch_image_bytes(thumbnail_url)
            print(f"✅ Thumbnail fetched: {len(image_bytes)} bytes")
        else:
            print(f"📁 Processing uploaded file: {file.filename}")
            image_bytes = await file.read()
            print(f"✅ File loaded: {len(image_bytes)} bytes")
        
        # ===== STEP 1: Gemini Detection (Get ALL detections) =====
        print("🤖 Running Gemini detection for all elements (faces, objects, text)...")
        
        gemini_detection_dict = await run_in_threadpool(get_all_detection_data, image_bytes)
        
        try:
            # Validate the detection result
            detection_data = GeminiAllDetection(**gemini_detection_dict)
            detected_elements = detection_data.detected_objects
            
            print(f"✅ Gemini detected {len(detected_elements)} total elements")
            
        except Exception as e:
            print(f"⚠️ Detection validation issue: {e}")
            traceback.print_exc()
            # Fallback to empty data on validation failure
            detected_elements = []
        
        # Convert Pydantic models to dicts for processing
        gemini_detections_list = [elem.model_dump() for elem in detected_elements]
        
        print(f"📦 Passing {len(gemini_detections_list)} detections to run_full_analysis:")
        for det in gemini_detections_list[:5]:  # Show first 5
            print(f"   - {det.get('label', 'unknown')} (confidence: {det.get('confidence', 0):.2f})")
        if len(gemini_detections_list) > 5:
            print(f"   ... and {len(gemini_detections_list) - 5} more")
        
        # ===== STEP 2: Run Full CV Analysis + Processing =====
        # This function now handles EVERYTHING internally:
        # - CV metrics (brightness, contrast, colors)
        # - Text extraction (OCR)
        # - Face processing (count, emotion, contrast, position)
        # - Object processing (contrast calculation)
        # - Returns comprehensive analysis_data with ALL necessary fields
        print("🔍 Running comprehensive analysis (CV + Detection Processing)...")
        
        analysis_data = await run_in_threadpool(
            run_full_analysis,
            image_bytes,
            gemini_detections_list  # Pass the full list from Gemini
        )
        
        print("✅ Analysis complete!")
        print(f"   📊 Results:")
        print(f"      - Brightness: {analysis_data['average_brightness']:.2f}")
        print(f"      - Contrast: {analysis_data['contrast_level']:.2f}")
        print(f"      - Text: '{analysis_data['text_content']}'")
        print(f"      - Faces: {analysis_data['face_count']} (emotion: {analysis_data.get('detected_emotion', 'N/A')})")
        print(f"      - Objects: {len(analysis_data['detected_objects'])}")
        
        # Log detected objects for debugging
        if analysis_data['detected_objects']:
            print(f"   🎯 Detected Objects:")
            for obj in analysis_data['detected_objects']:
                print(f"      - {obj.get('label', 'unknown')} (contrast: {obj.get('contrast_score_vs_bg', 0):.3f})")
        else:
            print(f"   ⚠️ No objects detected")
        
        # ===== STEP 3: Generate AI Feedback =====
        print("💡 Generating AI suggestions...")
        
        llm_result = await run_in_threadpool(generate_final_feedback, image_bytes, analysis_data)
        
        print(f"✅ AI feedback generated (Score: {llm_result['attractiveness_score']}/100)")
        
        # ===== STEP 4: Construct Final Result =====
        # Now we simply use the comprehensive analysis_data directly
        # NO need to derive face_count/detected_emotion here - image_processor already did it!
        final_result = AnalysisResult(
            # CV Metrics
            average_brightness=analysis_data['average_brightness'],
            contrast_level=analysis_data['contrast_level'],
            dominant_colors=analysis_data['dominant_colors'],
            
            # Text Analysis
            word_count=analysis_data['word_count'],
            text_content=analysis_data['text_content'],
            
            # Face Data (now comes directly from run_full_analysis)
            face_count=analysis_data['face_count'],
            detected_emotion=analysis_data['detected_emotion'],
            detected_faces=analysis_data['detected_faces'],
            
            # Object Data (now properly populated from run_full_analysis)
            detected_objects=analysis_data['detected_objects'],
            
            # AI Feedback
            attractiveness_score=llm_result['attractiveness_score'],
            ai_suggestions=llm_result['ai_suggestions']
        )
        
        print(f"🎉 Analysis complete! Score: {final_result.attractiveness_score}/100")
        print(f"   📊 Final counts: {final_result.face_count} faces, {len(final_result.detected_objects)} objects")
        
        if final_result.detected_objects:
            print(f"   🔍 Objects being returned to frontend:")
            for obj in final_result.detected_objects:
                print(f"      - {obj.label} (confidence: {obj.confidence:.2f}, contrast: {obj.contrast_score_vs_bg:.3f})")
        else:
            print(f"   ⚠️ WARNING: No objects in final result!")
        
        return final_result
        
    except HTTPException:
        raise
    except Exception as e:
        if "GEMINI_API_KEY" in str(e) or "authentication" in str(e).lower():
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY environment variable is not configured correctly or is invalid."
            )
        
        print(f"❌ Critical Analysis Error: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)