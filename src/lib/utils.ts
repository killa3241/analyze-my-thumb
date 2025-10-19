// src/lib/utils.ts

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility function for merging Tailwind CSS classes
 * Used by shadcn/ui components
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const getObjectIcon = (label: string): string => {
  const lowerLabel = label.toLowerCase();
  if (lowerLabel.includes('face') || lowerLabel.includes('person')) return '👤';
  if (lowerLabel.includes('animal') || lowerLabel.includes('cat') || lowerLabel.includes('dog')) return '🦁';
  if (lowerLabel.includes('text') || lowerLabel.includes('word')) return '📝';
  if (lowerLabel.includes('car') || lowerLabel.includes('vehicle')) return '🚗';
  if (lowerLabel.includes('food')) return '🍔';
  return '🎯';
};

export const getEmotionEmoji = (emotion: string | null): string => {
  if (!emotion) return '😐';
  const lower = emotion.toLowerCase();
  if (lower.includes('happy') || lower.includes('joy')) return '😊';
  if (lower.includes('sad')) return '😢';
  if (lower.includes('angry')) return '😠';
  if (lower.includes('surprise')) return '😮';
  if (lower.includes('fear')) return '😨';
  if (lower.includes('disgust')) return '🤢';
  if (lower.includes('neutral')) return '😐';
  return '😐';
};

export const getEmotionColor = (emotion: string | null): string => {
  if (!emotion) return 'bg-gray-500';
  const lower = emotion.toLowerCase();
  if (lower.includes('happy')) return 'bg-green-500';
  if (lower.includes('sad')) return 'bg-blue-500';
  if (lower.includes('angry')) return 'bg-red-500';
  if (lower.includes('surprise')) return 'bg-yellow-500';
  if (lower.includes('fear')) return 'bg-purple-500';
  return 'bg-gray-500';
};

export const getContrastBadgeColor = (score: number): string => {
  if (score > 0.8) return 'bg-green-500/20 text-green-400 border-green-500/30';
  if (score > 0.5) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
  return 'bg-red-500/20 text-red-400 border-red-500/30';
};

export const getPriorityBadge = (suggestion: string): { 
  emoji: string; 
  label: string; 
  color: string;
  explanation: string;
} => {
  const lower = suggestion.toLowerCase();
  
  if (lower.includes('critical') || lower.includes('must') || lower.includes('important')) {
    return { 
      emoji: '🔴', 
      label: 'Critical', 
      color: 'bg-red-500/20 text-red-400 border-red-500/30',
      explanation: 'This issue significantly impacts click-through rate and should be addressed immediately for optimal performance.'
    };
  }
  
  if (lower.includes('should') || lower.includes('recommend') || lower.includes('consider')) {
    return { 
      emoji: '🟡', 
      label: 'Important', 
      color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      explanation: 'Implementing this suggestion will noticeably improve your thumbnail effectiveness and viewer engagement.'
    };
  }
  
  return { 
    emoji: '🟢', 
    label: 'Enhancement', 
    color: 'bg-green-500/20 text-green-400 border-green-500/30',
    explanation: 'This enhancement can provide incremental improvements to your thumbnail\'s overall appeal.'
  };
};

export const getScoreColor = (score: number): string => {
  if (score >= 80) return 'text-green-400';
  if (score >= 60) return 'text-yellow-400';
  return 'text-red-400';
};

export const getScoreGrade = (score: number): string => {
  if (score >= 80) return 'Excellent';
  if (score >= 60) return 'Good';
  if (score >= 40) return 'Average';
  return 'Needs Improvement';
};

export const extractYoutubeThumbnail = (url: string): string | null => {
  const videoIdMatch = url.match(
    /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/
  );
  if (videoIdMatch && videoIdMatch[1]) {
    return `https://img.youtube.com/vi/${videoIdMatch[1]}/maxresdefault.jpg`;
  }
  return null;
};

export const formatTimestamp = (timestamp: number): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInMins = Math.floor(diffInMs / 60000);
  
  if (diffInMins < 1) return 'Just now';
  if (diffInMins < 60) return `${diffInMins}m ago`;
  
  const diffInHours = Math.floor(diffInMins / 60);
  if (diffInHours < 24) return `${diffInHours}h ago`;
  
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) return `${diffInDays}d ago`;
  
  return date.toLocaleDateString();
};

export const calculateCTRRange = (score: number): {
  conservative: number;
  expected: number;
  optimistic: number;
} => {
  return {
    conservative: Number((score * 0.05).toFixed(1)),
    expected: Number((score * 0.08).toFixed(1)),
    optimistic: Number((score * 0.12).toFixed(1)),
  };
};

export const normalizeMetricValue = (value: number, max: number): number => {
  return Math.min(100, Math.round((value / max) * 100));
};