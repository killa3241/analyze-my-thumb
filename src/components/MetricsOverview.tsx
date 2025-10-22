// src/components/MetricsOverview.tsx - Fixed OCR Display

import { Sun, Zap, Type, Palette } from 'lucide-react';
import { CircularProgress } from './CircularProgress';
import { normalizeMetricValue } from '@/lib/utils';

interface MetricsOverviewProps {
  averageBrightness: number;
  contrastLevel: number;
  wordCount: number;
  textContent: string;
  dominantColors: string[];
}

export const MetricsOverview = ({
  averageBrightness,
  contrastLevel,
  wordCount,
  textContent,
  dominantColors,
}: MetricsOverviewProps) => {
  const brightnessPercentage = normalizeMetricValue(averageBrightness, 255);
  
  // ✅ FIXED: Robust OCR display logic
  const normalizedText = textContent?.trim() || 'None';
  const isOcrFailed = 
    normalizedText === 'None' || 
    normalizedText === 'OCR Failed' ||
    normalizedText.includes('Failed') ||
    normalizedText.length === 0;
  
  const displayContent = isOcrFailed 
    ? 'No text detected' 
    : normalizedText.replace(/\r?\n/g, ' ');
  
  // ✅ FIXED: Use 0 if OCR failed
  const actualWordCount = isOcrFailed ? 0 : wordCount;

  return (
    <div className="space-y-6">
      {/* Main Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Brightness */}
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-6 rounded-2xl shadow-xl hover:shadow-2xl transition-all hover:scale-105 hover:border-yellow-500/30">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-500/10 rounded-lg">
                <Sun className="h-5 w-5 text-yellow-400" />
              </div>
              <h3 className="font-semibold text-white">Brightness</h3>
            </div>
            <CircularProgress percentage={brightnessPercentage} size={50} />
          </div>
          <p className="text-3xl font-bold text-yellow-400 mb-1">
            {Math.round(averageBrightness)}/255
          </p>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-yellow-600 to-yellow-400 transition-all duration-1000"
                style={{ width: `${brightnessPercentage}%` }}
              />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Optimal: 128-180 • {brightnessPercentage >= 50 && brightnessPercentage <= 70 ? '✓ Good' : '⚠ Adjust'}
          </p>
        </div>

        {/* Contrast */}
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-6 rounded-2xl shadow-xl hover:shadow-2xl transition-all hover:scale-105 hover:border-purple-500/30">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Zap className="h-5 w-5 text-purple-400" />
              </div>
              <h3 className="font-semibold text-white">Contrast</h3>
            </div>
            <CircularProgress percentage={contrastLevel} size={50} />
          </div>
          <p className="text-3xl font-bold text-purple-400 mb-1">
            {Math.round(contrastLevel)}%
          </p>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-600 to-pink-500 transition-all duration-1000"
                style={{ width: `${contrastLevel}%` }}
              />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Optimal: 60-80% • {contrastLevel >= 60 && contrastLevel <= 80 ? '✓ Perfect' : '⚠ Adjust'}
          </p>
        </div>

        {/* Text Count (Words) - FIXED */}
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-6 rounded-2xl shadow-xl hover:shadow-2xl transition-all hover:scale-105 hover:border-green-500/30">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <Type className="h-5 w-5 text-green-400" />
              </div>
              <h3 className="font-semibold text-white">Words</h3>
            </div>
            <div className="text-4xl font-bold text-green-400">
              {actualWordCount}
            </div>
          </div>

          {/* Content Preview */}
          <p 
            className={`text-sm truncate mb-3 h-5 ${
              isOcrFailed ? 'text-gray-500 italic' : 'text-gray-300'
            }`}
            title={displayContent}
          >
            {displayContent}
          </p>

          {/* Progress Bar */}
          <div className="flex items-center gap-2 mb-2">
            <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-green-600 to-green-400 transition-all duration-1000"
                style={{ width: `${Math.min(100, (actualWordCount / 7) * 100)}%` }}
              />
            </div>
          </div>

          {/* Optimal Range Indicator */}
          <p className="text-xs text-gray-400">
            Optimal: 3-7 words • {
              actualWordCount === 0 
                ? '— No text' 
                : actualWordCount >= 3 && actualWordCount <= 7 
                  ? '✓ Perfect' 
                  : actualWordCount < 3 
                    ? '⚠ Too few' 
                    : '⚠ Too many'
            }
          </p>
        </div>
      </div>

      {/* Dominant Colors - Full Width Section */}
      <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-6 rounded-2xl shadow-xl">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-pink-500/10 rounded-lg">
            <Palette className="h-5 w-5 text-pink-400" />
          </div>
          <h3 className="text-xl font-semibold text-white">Dominant Colors</h3>
          <span className="text-sm text-gray-500">({dominantColors.length} detected)</span>
        </div>
        <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-6 gap-4">
          {dominantColors.map((color, idx) => (
            <div
              key={idx}
              className="group cursor-pointer transform transition-all hover:scale-110"
            >
              <div
                className="h-24 rounded-xl shadow-lg group-hover:shadow-2xl transition-shadow border-2 border-gray-700 group-hover:border-white"
                style={{ backgroundColor: color }}
              />
              <p className="text-center mt-2 text-xs font-mono text-gray-400 group-hover:text-white transition-colors">
                {color}
              </p>
            </div>
          ))}
        </div>
        {dominantColors.length === 0 && (
          <div className="text-center py-8">
            <Palette className="h-12 w-12 mx-auto text-gray-600 mb-3" />
            <p className="text-gray-500 text-sm">No dominant colors detected</p>
          </div>
        )}
      </div>
    </div>
  );
};