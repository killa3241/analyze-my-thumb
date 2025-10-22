// src/types/comparison.ts

export interface ThumbnailState {
  previewUrl: string | null;
  result: AnalysisResult | null;
  isAnalyzing: boolean;
  error: string | null;
  progress: number;
}

export interface ComparisonResult {
  winner: 'A' | 'B' | 'TIE';
  scoreA: number;
  scoreB: number;
  scoreDifference: number;
  metricBreakdown: {
    attractiveness: { A: number; B: number; winner: 'A' | 'B' | 'TIE' };
    contrast: { A: number; B: number; winner: 'A' | 'B' | 'TIE' };
    brightness: { A: number; B: number; winner: 'A' | 'B' | 'TIE' };
    wordCount: { A: number; B: number; winner: 'A' | 'B' | 'TIE' };
    facePresence: { A: boolean; B: boolean; winner: 'A' | 'B' | 'TIE' };
  };
  recommendations: string[];
}

export interface MetricComparison {
  label: string;
  valueA: number;
  valueB: number;
  unit: string;
  optimal: string;
  winner: 'A' | 'B' | 'TIE';
}

export interface AnalysisResult {
  attractiveness_score: number;
  contrast_level: number;
  average_brightness: number;
  word_count: number;
  face_count: number;
  detected_emotion?: string;
  dominant_colors?: string[];
  detected_objects?: Array<{ label: string; confidence: number }>;
  thumbnail_url?: string;
  text_content?: string;
}

// Helper function to calculate brightness score (optimal = 154)
export const calculateBrightnessScore = (brightness: number): number => {
  const optimal = 154;
  return Math.max(0, 100 - (Math.abs(brightness - optimal) / optimal) * 100);
};

// Helper function to calculate word count score
export const calculateWordCountScore = (wordCount: number): number => {
  if (wordCount >= 3 && wordCount <= 7) return 100;
  if (wordCount < 3) return Math.max(0, (wordCount / 3) * 100);
  return Math.max(0, 100 - ((wordCount - 7) * 10));
};

// Helper function to calculate face presence bonus
export const calculateFaceBonus = (
  faceCount: number,
  emotion?: string
): number => {
  if (faceCount === 0) return 0;
  if (emotion && emotion !== 'neutral') return 10;
  if (faceCount > 0) return 5;
  return 0;
};

// Main scoring calculation
export const calculateTotalScore = (result: AnalysisResult): number => {
  const attractivenessScore = result.attractiveness_score * 0.4;
  const contrastScore = result.contrast_level * 0.2;
  const brightnessScore = calculateBrightnessScore(result.average_brightness) * 0.15;
  const wordCountScore = calculateWordCountScore(result.word_count) * 0.15;
  const faceBonus = calculateFaceBonus(result.face_count, result.detected_emotion) * 0.1;

  return attractivenessScore + contrastScore + brightnessScore + wordCountScore + faceBonus;
};

// Compare two results and determine winner
export const calculateComparison = (
  resultA: AnalysisResult,
  resultB: AnalysisResult
): ComparisonResult => {
  const scoreA = calculateTotalScore(resultA);
  const scoreB = calculateTotalScore(resultB);
  const scoreDifference = Math.abs(scoreA - scoreB);

  // Determine winners for each metric
  const attractivenessWinner = 
    resultA.attractiveness_score > resultB.attractiveness_score ? 'A' :
    resultB.attractiveness_score > resultA.attractiveness_score ? 'B' : 'TIE';

  const contrastWinner = 
    resultA.contrast_level > resultB.contrast_level ? 'A' :
    resultB.contrast_level > resultA.contrast_level ? 'B' : 'TIE';

  const brightnessScoreA = calculateBrightnessScore(resultA.average_brightness);
  const brightnessScoreB = calculateBrightnessScore(resultB.average_brightness);
  const brightnessWinner = 
    brightnessScoreA > brightnessScoreB ? 'A' :
    brightnessScoreB > brightnessScoreA ? 'B' : 'TIE';

  const wordCountScoreA = calculateWordCountScore(resultA.word_count);
  const wordCountScoreB = calculateWordCountScore(resultB.word_count);
  const wordCountWinner = 
    wordCountScoreA > wordCountScoreB ? 'A' :
    wordCountScoreB > wordCountScoreA ? 'B' : 'TIE';

  const facePresenceA = resultA.face_count > 0;
  const facePresenceB = resultB.face_count > 0;
  const faceWinner = 
    facePresenceA && !facePresenceB ? 'A' :
    facePresenceB && !facePresenceA ? 'B' : 'TIE';

  // Generate recommendations
  const recommendations: string[] = [];
  const winner = scoreA > scoreB ? 'A' : scoreB > scoreA ? 'B' : 'TIE';

  if (winner !== 'TIE') {
    const loser = winner === 'A' ? 'B' : 'A';
    const loserResult = winner === 'A' ? resultB : resultA;

    if (loserResult.attractiveness_score < 70) {
      recommendations.push(`Thumbnail ${loser}: Improve visual appeal with better composition`);
    }
    if (loserResult.contrast_level < 50) {
      recommendations.push(`Thumbnail ${loser}: Increase contrast for better readability`);
    }
    if (loserResult.word_count < 3 || loserResult.word_count > 7) {
      recommendations.push(`Thumbnail ${loser}: Aim for 3-7 words in title text`);
    }
    if (loserResult.face_count === 0 && (resultA.face_count > 0 || resultB.face_count > 0)) {
      recommendations.push(`Thumbnail ${loser}: Consider adding a face for emotional connection`);
    }
  } else {
    recommendations.push('Both thumbnails are equally strong!');
  }

  return {
    winner,
    scoreA: Math.round(scoreA * 10) / 10,
    scoreB: Math.round(scoreB * 10) / 10,
    scoreDifference: Math.round(scoreDifference * 10) / 10,
    metricBreakdown: {
      attractiveness: {
        A: resultA.attractiveness_score,
        B: resultB.attractiveness_score,
        winner: attractivenessWinner as 'A' | 'B' | 'TIE'
      },
      contrast: {
        A: resultA.contrast_level,
        B: resultB.contrast_level,
        winner: contrastWinner as 'A' | 'B' | 'TIE'
      },
      brightness: {
        A: brightnessScoreA,
        B: brightnessScoreB,
        winner: brightnessWinner as 'A' | 'B' | 'TIE'
      },
      wordCount: {
        A: wordCountScoreA,
        B: wordCountScoreB,
        winner: wordCountWinner as 'A' | 'B' | 'TIE'
      },
      facePresence: {
        A: facePresenceA,
        B: facePresenceB,
        winner: faceWinner as 'A' | 'B' | 'TIE'
      }
    },
    recommendations
  };
};