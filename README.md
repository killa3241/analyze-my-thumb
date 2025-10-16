# Thumblytics - YouTube Thumbnail Analyzer

A full-stack application that analyzes YouTube thumbnails using computer vision and AI to provide actionable insights and improvement suggestions.

## 📋 Project Overview

Thumblytics combines computer vision techniques with Google Gemini AI to analyze YouTube thumbnails across multiple dimensions:

- **Visual Metrics**: Brightness, contrast, and dominant color analysis
- **Text Analysis**: OCR-based text extraction and word count
- **Object Detection**: YOLO-based object detection with contrast scoring
- **Emotion Detection**: Face detection and emotion analysis using DeepFace
- **AI Feedback**: Google Gemini-powered attractiveness scoring and improvement suggestions

## 🏗️ Architecture

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

## 🚀 Getting Started

### Prerequisites

- **Node.js** (v18 or higher) - [Install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)
- **Python** (v3.9 or higher)
- **Tesseract OCR** - Required for text extraction
  - macOS: `brew install tesseract`
  - Ubuntu: `sudo apt-get install tesseract-ocr`
  - Windows: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)

### Environment Variables

#### Backend
Create a `.env` file in the `backend` directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your Gemini API key from: https://makersuite.google.com/app/apikey

#### Frontend
The frontend environment variables are automatically configured via Lovable Cloud:
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_PUBLISHABLE_KEY`
- `VITE_SUPABASE_PROJECT_ID`

## 📦 Installation

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

The frontend will be available at `http://localhost:8080`

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
python -m app.main
```

The backend API will be available at `http://localhost:8000`

## 🔧 Development Commands

### Frontend

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Backend

```bash
# Run FastAPI with auto-reload
uvicorn app.main:app --reload

# Run with custom host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 API Endpoints

### `POST /analyze-thumbnail`

Analyzes a YouTube thumbnail from URL or uploaded file.

**Request:**
- `youtube_url` (optional): YouTube video URL
- `file` (optional): Direct image file upload

**Response:**
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
    "Add more contrast between subject and background",
    "Consider warmer color palette",
    "Optimize face positioning in rule of thirds",
    "Simplify background elements"
  ]
}
```

## 🔑 Key Features

1. **Multi-Source Analysis**: Accept YouTube URLs or direct file uploads
2. **Comprehensive Metrics**: 10+ visual and content metrics
3. **AI-Powered Insights**: Context-aware suggestions using Gemini AI
4. **Structured Output**: Strictly validated JSON responses via Pydantic
5. **Async Processing**: Non-blocking analysis for better performance

## 🛠️ Technologies Used

### Frontend Stack
- React 18.3.1
- TypeScript
- Vite
- Tailwind CSS
- shadcn-ui
- TanStack Query
- Supabase Client
- React Router DOM
- Recharts (for data visualization)

### Backend Stack
- FastAPI 0.109.0
- OpenCV 4.9.0
- PyTesseract 0.3.10
- DeepFace 0.0.87
- Google Gemini AI (google-genai 0.2.2)
- Pillow 10.2.0
- NumPy 1.26.3
- scikit-learn 1.4.0
- httpx 0.26.0

## 📁 Project Structure

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

## 🚢 Deployment

### Frontend Deployment
This project is deployed via Lovable:
1. Click the **Publish** button in the Lovable editor
2. Your app will be available at `yoursite.lovable.app`
3. Connect a custom domain in Project > Settings > Domains (requires paid plan)

### Backend Deployment
The FastAPI backend needs to be deployed separately on platforms like:
- **Railway**: https://railway.app
- **Render**: https://render.com
- **DigitalOcean App Platform**: https://www.digitalocean.com/products/app-platform
- **Google Cloud Run**: https://cloud.google.com/run
- **AWS Elastic Beanstalk**: https://aws.amazon.com/elasticbeanstalk

## 📝 License

This project was built with [Lovable](https://lovable.dev)

## 🔗 Useful Links

- [Lovable Documentation](https://docs.lovable.dev/)
- [Lovable Project URL](https://lovable.dev/projects/744d8771-2b0d-44e6-9c36-6ea0d68fc64d)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Gemini API](https://ai.google.dev/)

## 🐛 Troubleshooting

### Tesseract Not Found Error
If you get a "Tesseract not found" error:
- Ensure Tesseract is installed and in your PATH
- On Windows, you may need to set the path explicitly in code

### GEMINI_API_KEY Not Set
Make sure you've created a `.env` file in the `backend` directory with your Gemini API key.

### CORS Errors
The backend is configured to allow all origins in development. For production, update the CORS settings in `backend/app/main.py`.

## 💡 Support

For issues and questions:
- Check the [Lovable Documentation](https://docs.lovable.dev/)
- Join the [Lovable Discord Community](https://discord.com/channels/1119885301872070706/1280461670979993613)
