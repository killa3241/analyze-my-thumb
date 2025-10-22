# Thumblytics - YouTube Thumbnail Analyzer

A full-stack application that analyzes YouTube thumbnails using computer vision and AI to provide actionable insights and improvement suggestions.

## Overview

Thumblytics combines computer vision techniques with Google Gemini AI to analyze YouTube thumbnails across multiple dimensions:

- **Visual Metrics**: Brightness, contrast, and dominant color analysis
- **Text Analysis**: OCR-based text extraction and word count
- **Object Detection**: YOLO-based object detection with contrast scoring
- **Emotion Detection**: Face detection and emotion analysis using DeepFace
- **AI Feedback**: Google Gemini-powered attractiveness scoring and improvement suggestions

---

## Architecture

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + shadcn-ui components
- **State Management**: TanStack Query
- **Backend Integration**: Supabase (Lovable Cloud)
- **Routing**: React Router DOM

### Backend
- **Framework**: FastAPI (Python)
- **Computer Vision**: OpenCV, PyTesseract
- **Machine Learning**: DeepFace, scikit-learn
- **AI Integration**: Google Gemini API (gemini-2.0-flash-exp)
- **Image Processing**: Pillow, NumPy

---

## Prerequisites

- **Node.js** (v18 or higher) - [Install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)
- **Python** (**v3.12.x is highly recommended for dependency stability**) 
- **Tesseract OCR** - Required for text extraction
  - macOS: `brew install tesseract`
  - Ubuntu: `sudo apt-get install tesseract-ocr`
  - Windows: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)

---

## Installation

### Frontend Setup

```bash
# Clone the repository
git clone <YOUR_GIT_URL>
cd <YOUR_PROJECT_NAME>

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:8080

### Backend Setup

**Note:** For stable dependency resolution (OpenCV, DeepFace, TensorFlow), you must use Python 3.12.

```bash
# Navigate to backend directory
cd backend

# Create virtual environment using Python 3.12
# On Windows, using the launcher (if py is on PATH):
py -3.12 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows (PowerShell):
 .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0
```

### Backend Requirements (requirements.txt)

**Note:** TensorFlow 2.20.0 requires the explicit installation of tf-keras on Python 3.12. NumPy is pinned to 1.x for OpenCV stability.

```txt
# ================================
# Computer Vision & ML Core
# ================================
# CRITICAL: NumPy 1.x is required for stable OpenCV 4.9.x on Python 3.12
numpy==1.26.4
opencv-python==4.9.0.80
scikit-learn==1.5.1

# CRITICAL: TensorFlow 2.20.0 requires tf-keras for Keras 3 compatibility on Python 3.12
tensorflow==2.20.0
tf-keras
deepface==0.0.87
Pillow==11.3.0

# ================================
# Web/API Dependencies
# ================================
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
pytesseract==0.3.10
google-genai==0.2.2
httpx==0.26.0
python-dotenv==1.0.0
```

```bash
# Start FastAPI server (Use the venv's Python executable explicitly for stability)
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The backend API will be available at http://localhost:8000

---

## Configuration

### Backend Environment Variables

Create a `.env` file in the backend directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Obtain your Gemini API key from: https://makersuite.google.com/app/apikey

### Frontend Environment Variables

The frontend environment variables are automatically configured via Lovable Cloud:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_PUBLISHABLE_KEY`
- `VITE_SUPABASE_PROJECT_ID`

---

## API Documentation

### POST /analyze-thumbnail

Analyzes a YouTube thumbnail from URL or uploaded file.

**Request Parameters:**

- `youtube_url` (optional): YouTube video URL
- `file` (optional): Direct image file upload

**Response Schema:**

```json
{
  "average_brightness": 128.5,
  "contrast_level": 45.2,
  "dominant_colors": ["#FF5733", "#33FF57"],
  "word_count": 5,
  "text_content": "SHOCKING RESULTS",
  "face_count": 1,
  "detected_emotion": "happy",
  "detected_objects": [
    {
      "label": "person",
      "confidence": 0.95,
      "bbox": [100, 100, 300, 400],
      "contrast_score_vs_bg": 0.65
    }
  ],
  "attractiveness_score": 78,
  "ai_suggestions": [
    "Increase text size for better readability",
    "Add more contrast between subject and background"
  ]
}
```

---

## Development

### Frontend Commands

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Lint code
```

### Backend Commands

```bash
# Run with auto-reload (using venv Python is recommended)
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Run with custom host/port
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── image_processor.py    # CV/ML analysis logic
│   │   │   └── llm_generator.py      # Gemini AI integration
│   │   ├── models/
│   │   │   └── analysis_models.py    # Pydantic schemas
│   │   └── main.py                   # FastAPI application
│   └── requirements.txt
├── src/
│   ├── components/
│   │   ├── AnalysisDashboard.tsx     # Results display
│   │   ├── ThumbnailInput.tsx        # Upload interface
│   │   └── ui/                       # shadcn components
│   ├── integrations/
│   │   └── supabase/                 # Supabase client
│   ├── pages/
│   │   └── Index.tsx                 # Main page
│   └── main.tsx
└── README.md
```

---

## Deployment

### Frontend

Deploy via Lovable by clicking the Publish button in the editor. Your application will be available at yoursite.lovable.app. Custom domains can be configured in Project > Settings > Domains (paid plan required).

### Backend

Deploy the FastAPI backend on platforms such as:

- Railway (https://railway.app)
- Render (https://render.com)
- DigitalOcean App Platform
- Google Cloud Run
- AWS Elastic Beanstalk

Ensure environment variables are properly configured in your deployment platform.

---

## Troubleshooting

### Tesseract Not Found Error
Ensure Tesseract is installed and accessible in your system PATH. Windows users may need to set the path explicitly in the code.

### GEMINI_API_KEY Not Set
Verify that a `.env` file exists in the backend directory with a valid Gemini API key.

### CORS Errors
The backend allows all origins in development mode. Update CORS settings in `backend/app/main.py` for production deployments.

### Python Version Conflicts
If you encounter dependency errors (e.g., NumPy, TensorFlow), ensure your virtual environment was created with Python 3.12.x, as described in the Backend Setup section.

---

## License

This project was built with Lovable

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Gemini API](https://makersuite.google.com/)
- [Lovable Documentation](https://docs.lovable.dev/)