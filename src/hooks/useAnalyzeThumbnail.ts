// src/hooks/useAnalyzeThumbnail.ts
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { fetchAnalysis } from '@/lib/api';
import { AnalysisResult } from '@/types/analysis';

interface AnalysisInput {
  youtubeUrl?: string;
  file?: File;
}

export const useAnalyzeThumbnail = () => {
  const [progress, setProgress] = useState(0);

  const mutation = useMutation<AnalysisResult, Error, AnalysisInput>({
    mutationFn: async (input) => {
      // Simulate progress
      setProgress(0);
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      try {
        let result: AnalysisResult;
        
        // Determine if submitting a URL or a File
        if (input.youtubeUrl) {
          result = await fetchAnalysis({ youtubeUrl: input.youtubeUrl });
        } else if (input.file) {
          result = await fetchAnalysis({ file: input.file });
        } else {
          throw new Error('No input provided for analysis.');
        }

        clearInterval(progressInterval);
        setProgress(100);
        return result;
      } catch (error) {
        clearInterval(progressInterval);
        setProgress(0);
        throw error;
      }
    },
    onSuccess: () => {
      setProgress(100);
    },
    onError: () => {
      setProgress(0);
    },
  });

  // Create the analyzeThumbnail function that matches the expected signature
  const analyzeThumbnail = async (input: string | File): Promise<AnalysisResult | null> => {
    try {
      let analysisInput: AnalysisInput;
      
      if (typeof input === 'string') {
        analysisInput = { youtubeUrl: input };
      } else {
        analysisInput = { file: input };
      }

      const result = await mutation.mutateAsync(analysisInput);
      return result;
    } catch (error) {
      console.error('Analysis failed:', error);
      return null;
    }
  };

  return {
    analyzeThumbnail,
    result: mutation.data ?? null,
    isAnalyzing: mutation.isPending,
    error: mutation.error?.message ?? null,
    progress,
    reset: mutation.reset,
  };
};