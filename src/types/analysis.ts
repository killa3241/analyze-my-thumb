// src/types/analysis.ts

// NOTE: All keys use snake_case to match the FastAPI/Pydantic JSON output

export interface ObjectAnalysis {
  label: string;
  confidence: number;
  bbox_normalized: number[]; // ✅ FIXED: Changed from bbox to bbox_normalized
  contrast_score_vs_bg: number;
  position?: string; // ✅ ADDED: top-left, center, etc.
  element_type?: string; // ✅ ADDED: object, face, etc.
  emotion?: string | null; // ✅ ADDED: for faces
}

export interface FaceAnalysis {
  label: string;
  bbox_normalized: number[];
  confidence: number;
  emotion: string;
  contrast_score_vs_bg: number;
  position: string;
  element_type: string;
}

export interface AnalysisResult {
  average_brightness: number;
  contrast_level: number;
  dominant_colors: string[];
  word_count: number; 
  text_content: string;
  
  face_count: number;
  detected_emotion: string | null;
  detected_faces: FaceAnalysis[]; // ✅ ADDED: Array of detected faces
  detected_objects: ObjectAnalysis[];
  
  attractiveness_score: number;
  ai_suggestions: string[]; 
}