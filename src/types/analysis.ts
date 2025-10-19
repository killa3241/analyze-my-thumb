// src/types/analysis.ts

// NOTE: All keys use snake_case to match the FastAPI/Pydantic JSON output

export interface ObjectAnalysis {
  label: string;
  confidence: number;
  bbox: number[]; // [x1, y1, x2, y2]
  contrast_score_vs_bg: number; // Matches Python field
}

export interface AnalysisResult {
  average_brightness: number; // Matches Python field
  contrast_level: number; // Matches Python field
  dominant_colors: string[];
  word_count: number; 
  text_content: string;
  
  face_count: number;
  detected_emotion: string | null;
  detected_objects: ObjectAnalysis[];
  
  attractiveness_score: number; // Matches Python field
  ai_suggestions: string[]; 
}