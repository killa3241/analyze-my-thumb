// src/components/ui/ComparisonDashboard.tsx
import React from 'react';
import { Loader2 } from 'lucide-react';
import { AnalysisResult } from '../types/comparison';

interface ComparisonDashboardProps {
  resultA: AnalysisResult | null;
  resultB: AnalysisResult | null;
  previewUrlA: string | null;
  previewUrlB: string | null;
  isAnalyzingA: boolean;
  isAnalyzingB: boolean;
}

export const ComparisonDashboard: React.FC<ComparisonDashboardProps> = ({
  resultA,
  resultB,
  previewUrlA,
  previewUrlB,
  isAnalyzingA,
  isAnalyzingB
}) => {
  return (
    <div className="grid md:grid-cols-2 gap-6">
      {/* Dashboard A */}
      <DashboardPanel
        side="A"
        result={resultA}
        previewUrl={previewUrlA}
        isAnalyzing={isAnalyzingA}
        color="purple"
      />

      {/* VS Divider on Desktop */}
      <div className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
        <div className="bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold text-2xl px-6 py-3 rounded-full shadow-2xl">
          VS
        </div>
      </div>

      {/* Dashboard B */}
      <DashboardPanel
        side="B"
        result={resultB}
        previewUrl={previewUrlB}
        isAnalyzing={isAnalyzingB}
        color="blue"
      />
    </div>
  );
};

interface DashboardPanelProps {
  side: 'A' | 'B';
  result: AnalysisResult | null;
  previewUrl: string | null;
  isAnalyzing: boolean;
  color: 'purple' | 'blue';
}

const DashboardPanel: React.FC<DashboardPanelProps> = ({
  side,
  result,
  previewUrl,
  isAnalyzing,
  color
}) => {
  const colorClasses = {
    purple: {
      gradient: 'from-purple-500 to-pink-500',
      border: 'border-purple-500',
      text: 'text-purple-400',
      bg: 'bg-purple-500/10'
    },
    blue: {
      gradient: 'from-blue-500 to-cyan-500',
      border: 'border-blue-500',
      text: 'text-blue-400',
      bg: 'bg-blue-500/10'
    }
  };

  const colors = colorClasses[color];

  if (isAnalyzing) {
    return (
      <div className={`border-2 ${colors.border} rounded-xl p-8 ${colors.bg} backdrop-blur-sm`}>
        <div className="flex flex-col items-center justify-center space-y-4 py-12">
          <Loader2 className={`w-16 h-16 animate-spin ${colors.text}`} />
          <p className="text-lg text-gray-400">Analyzing Thumbnail {side}...</p>
          <div className="w-48 h-2 bg-gray-700 rounded-full overflow-hidden">
            <div className={`h-full bg-gradient-to-r ${colors.gradient} animate-pulse`} style={{ width: '60%' }} />
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className={`border-2 border-dashed ${colors.border} rounded-xl p-8 ${colors.bg} backdrop-blur-sm opacity-50`}>
        <div className="flex flex-col items-center justify-center space-y-4 py-12">
          <div className={`text-6xl ${colors.text}`}>?</div>
          <p className="text-lg text-gray-500">Awaiting Thumbnail {side} Analysis</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`border-2 ${colors.border} rounded-xl overflow-hidden bg-gray-900/50 backdrop-blur-sm transition-all duration-300 hover:shadow-xl`}>
      {/* Header */}
      <div className={`bg-gradient-to-r ${colors.gradient} p-4`}>
        <h3 className="text-xl font-bold text-white">Thumbnail {side}</h3>
      </div>

      {/* Thumbnail Preview */}
      {previewUrl && (
        <div className="p-4 bg-gray-800/50">
          <img
            src={previewUrl}
            alt={`Thumbnail ${side}`}
            className="w-full rounded-lg border border-gray-700"
          />
        </div>
      )}

      {/* Metrics Grid */}
      <div className="p-6 space-y-4">
        {/* Attractiveness Score */}
        <MetricCard
          label="Attractiveness Score"
          value={result.attractiveness_score}
          max={100}
          color={color}
        />

        {/* Contrast Level */}
        <MetricCard
          label="Contrast Level"
          value={result.contrast_level}
          max={100}
          color={color}
        />

        {/* Brightness */}
        <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
          <span className="text-gray-300 font-medium">Brightness</span>
          <span className={`font-bold ${colors.text}`}>
            {Math.round(result.average_brightness)}/255
          </span>
        </div>

        {/* Word Count */}
        <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
          <span className="text-gray-300 font-medium">Word Count</span>
          <span className={`font-bold ${colors.text}`}>
            {result.word_count} words
          </span>
        </div>

        {/* Face Count */}
        <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
          <span className="text-gray-300 font-medium">Faces Detected</span>
          <span className={`font-bold ${colors.text}`}>
            {result.face_count}
          </span>
        </div>

        {/* Emotion */}
        {result.detected_emotion && (
          <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
            <span className="text-gray-300 font-medium">Emotion</span>
            <span className={`font-bold ${colors.text} capitalize`}>
              {result.detected_emotion}
            </span>
          </div>
        )}

        {/* Text Content */}
        {result.text_content && (
          <div className="p-3 bg-gray-800/50 rounded-lg">
            <p className="text-gray-300 font-medium mb-2">Text Content</p>
            <p className="text-sm text-gray-400 italic">"{result.text_content}"</p>
          </div>
        )}
      </div>
    </div>
  );
};

interface MetricCardProps {
  label: string;
  value: number;
  max: number;
  color: 'purple' | 'blue';
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, max, color }) => {
  const percentage = (value / max) * 100;
  const gradients = {
    purple: 'from-purple-500 to-pink-500',
    blue: 'from-blue-500 to-cyan-500'
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-gray-300 font-medium">{label}</span>
        <span className="text-white font-bold">{Math.round(value)}/{max}</span>
      </div>
      <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${gradients[color]} transition-all duration-1000 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};