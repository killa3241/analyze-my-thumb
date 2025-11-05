// src/lib/api.ts

import { AnalysisResult } from '@/types/analysis';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
//export const API_BASE_URL = 'http://localhost:8000';

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
    formData.append('youtube_url', input.youtubeUrl);
  } else {
    formData.append('file', input.file);
  }

  console.log('🚀 Sending request to:', endpoint);

  const response = await fetch(endpoint, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = 'Analysis failed due to an unknown error.';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      errorDetail = `Server error: ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  // ✅ CRITICAL DEBUG: Log raw response before parsing
  const rawText = await response.text();
  console.log('📦 Raw API Response (first 500 chars):', rawText.substring(0, 500));

  // Parse the response
  const jsonData = JSON.parse(rawText);
  
  // ✅ CRITICAL DEBUG: Log the parsed JSON
  console.log('📊 Parsed JSON - text_content:', jsonData.text_content);
  console.log('📊 Parsed JSON - word_count:', jsonData.word_count);
  console.log('📊 Full parsed object keys:', Object.keys(jsonData));

  // ✅ CRITICAL DEBUG: Check if the data is being lost during type casting
  const result = jsonData as AnalysisResult;
  console.log('🔄 After type cast - text_content:', result.text_content);
  console.log('🔄 After type cast - word_count:', result.word_count);

  return result;
}