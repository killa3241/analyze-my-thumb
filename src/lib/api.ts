// src/lib/api.ts

import { AnalysisResult } from '@/types/analysis'; // We'll define this type next

// ⚠️ CHANGE THIS TO YOUR FASTAPI BACKEND URL ⚠️
const API_BASE_URL = process.env.REACT_APP_API_URL ||'http://localhost:8000'; 

/**
 * Fetches the analysis result from the FastAPI backend.
 * Handles both URL submission and file upload.
 */
export async function fetchAnalysis(
  input: { youtubeUrl: string } | { file: File }
): Promise<AnalysisResult> {
  const endpoint = `${API_BASE_URL}/analyze-thumbnail`;
  const formData = new FormData();

  if ('youtubeUrl' in input) {
    // 1. YouTube URL submission (sends as Form field)
    formData.append('youtube_url', input.youtubeUrl);
  } else {
    // 2. File upload submission (sends as File field)
    formData.append('file', input.file);
  }

  const response = await fetch(endpoint, {
    method: 'POST',
    // Do NOT set Content-Type header; FormData handles it automatically for multipart/form-data
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = 'Analysis failed due to an unknown error.';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      // If response is not JSON
      errorDetail = `Server error: ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<AnalysisResult>;
}