// src/hooks/useCompareThumbnails.ts
import { useState, useEffect } from 'react';
import { ThumbnailState, ComparisonResult, AnalysisResult, calculateComparison } from '../types/comparison';
import { API_BASE_URL } from '@/lib/api';

interface AnalyzeInput {
  type: 'url' | 'file';
  url?: string;
  file?: File;
}

export const useCompareThumbnails = () => {
  const [thumbnailA, setThumbnailA] = useState<ThumbnailState>({
    previewUrl: null,
    result: null,
    isAnalyzing: false,
    error: null,
    progress: 0
  });

  const [thumbnailB, setThumbnailB] = useState<ThumbnailState>({
    previewUrl: null,
    result: null,
    isAnalyzing: false,
    error: null,
    progress: 0
  });

  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);

  // Auto-calculate comparison when both analyses complete
  useEffect(() => {
    if (thumbnailA.result && thumbnailB.result) {
      const comparison = calculateComparison(thumbnailA.result, thumbnailB.result);
      setComparisonResult(comparison);
    } else {
      setComparisonResult(null);
    }
  }, [thumbnailA.result, thumbnailB.result]);

  const fetchAnalysis = async (input: AnalyzeInput): Promise<AnalysisResult> => {
    const formData = new FormData();

    if (input.type === 'url' && input.url) {
      formData.append('youtube_url', input.url);
    } else if (input.type === 'file' && input.file) {
      formData.append('file', input.file);
    } else {
      throw new Error('Invalid input: provide either URL or file');
    }

    const response = await fetch(`${API_BASE_URL}/analyze-thumbnail`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Analysis failed: ${response.statusText}`);
    }

    return await response.json();
  };

  const analyzeThumbnailA = async (input: AnalyzeInput) => {
    setThumbnailA(prev => ({ 
      ...prev, 
      isAnalyzing: true, 
      error: null, 
      progress: 0 
    }));

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setThumbnailA(prev => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90)
        }));
      }, 200);

      const result = await fetchAnalysis(input);
      
      clearInterval(progressInterval);
      
      setThumbnailA(prev => ({ 
        ...prev, 
        result, 
        isAnalyzing: false,
        progress: 100,
        error: null
      }));
    } catch (error) {
      setThumbnailA(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Analysis failed', 
        isAnalyzing: false,
        progress: 0
      }));
    }
  };

  const analyzeThumbnailB = async (input: AnalyzeInput) => {
    setThumbnailB(prev => ({ 
      ...prev, 
      isAnalyzing: true, 
      error: null, 
      progress: 0 
    }));

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setThumbnailB(prev => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90)
        }));
      }, 200);

      const result = await fetchAnalysis(input);
      
      clearInterval(progressInterval);
      
      setThumbnailB(prev => ({ 
        ...prev, 
        result, 
        isAnalyzing: false,
        progress: 100,
        error: null
      }));
    } catch (error) {
      setThumbnailB(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Analysis failed', 
        isAnalyzing: false,
        progress: 0
      }));
    }
  };

  const setPreviewUrlA = (url: string | null) => {
    setThumbnailA(prev => ({ ...prev, previewUrl: url }));
  };

  const setPreviewUrlB = (url: string | null) => {
    setThumbnailB(prev => ({ ...prev, previewUrl: url }));
  };

  const resetComparison = () => {
    setThumbnailA({
      previewUrl: null,
      result: null,
      isAnalyzing: false,
      error: null,
      progress: 0
    });
    setThumbnailB({
      previewUrl: null,
      result: null,
      isAnalyzing: false,
      error: null,
      progress: 0
    });
    setComparisonResult(null);
  };

  return {
    thumbnailA,
    thumbnailB,
    comparisonResult,
    analyzeThumbnailA,
    analyzeThumbnailB,
    setPreviewUrlA,
    setPreviewUrlB,
    resetComparison
  };
};