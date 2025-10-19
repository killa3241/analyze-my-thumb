// src/components/FaceAnalysisCard.tsx

import { Users, Smile } from 'lucide-react';
import { getEmotionEmoji, getEmotionColor } from '@/lib/utils';

interface FaceAnalysisCardProps {
  faceCount: number;
  detectedEmotion: string | null;
}

export const FaceAnalysisCard = ({
  faceCount,
  detectedEmotion,
}: FaceAnalysisCardProps) => {
  if (faceCount === 0) {
    return null;
  }

  const emotionColorClass = getEmotionColor(detectedEmotion);

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-6 rounded-2xl shadow-xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-green-500/10 rounded-lg">
          <Users className="h-5 w-5 text-green-400" />
        </div>
        <h3 className="text-xl font-semibold text-white">Face Analysis</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Emotion Card */}
        <div className="bg-gradient-to-br from-green-900/30 to-blue-900/30 border border-green-500/30 rounded-xl p-6 hover:scale-105 transition-transform">
          <div className="flex items-center gap-4 mb-4">
            <div className="text-6xl animate-bounce-slow">
              {getEmotionEmoji(detectedEmotion)}
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-1">Detected Emotion</p>
              <p className="text-2xl font-bold text-white capitalize">
                {detectedEmotion || 'Neutral'}
              </p>
            </div>
          </div>

          <div
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${emotionColorClass} text-white font-medium`}
          >
            <Smile className="h-4 w-4" />
            <span className="text-sm">Primary Expression</span>
          </div>

          {/* Emotion Insight */}
          <div className="mt-4 pt-4 border-t border-gray-700/50">
            <p className="text-xs text-gray-400">
              {detectedEmotion?.toLowerCase().includes('happy')
                ? '✓ Positive emotions increase engagement'
                : detectedEmotion?.toLowerCase().includes('surprise')
                ? '⚡ Surprise expressions grab attention'
                : '💡 Consider more expressive facial emotions'}
            </p>
          </div>
        </div>

        {/* Face Count Card */}
        <div className="bg-gray-900/50 border border-gray-700 rounded-xl p-6 hover:scale-105 transition-transform">
          <p className="text-sm text-gray-400 mb-2">Face Count</p>
          <p className="text-6xl font-bold text-green-400 mb-4">{faceCount}</p>

          {/* Progress Bar */}
          <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden mb-3">
            <div
              className="h-full bg-gradient-to-r from-green-600 to-green-400 transition-all duration-1000"
              style={{ width: `${Math.min(100, (faceCount / 3) * 100)}%` }}
            />
          </div>

          {/* Insight Text */}
          <p className="text-sm text-gray-400">
            {faceCount === 1
              ? '✓ Single face detected - excellent for personal connection'
              : faceCount === 2
              ? '✓ Two faces - great for comparison or collaboration content'
              : '✓ Multiple faces - good for group or social content'}
          </p>

          {/* Best Practice */}
          <div className="mt-4 pt-4 border-t border-gray-700/50">
            <p className="text-xs text-green-400 font-medium mb-1">
              📊 Best Practice
            </p>
            <p className="text-xs text-gray-500">
              1-2 faces typically perform best for thumbnails
            </p>
          </div>
        </div>
      </div>

      {/* Additional Stats */}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="bg-gray-900/30 border border-gray-700/50 rounded-lg p-3">
          <p className="text-xs text-gray-500 mb-1">Eye Contact</p>
          <p className="text-sm font-bold text-white">
            {faceCount > 0 ? 'Detected ✓' : 'Not Detected'}
          </p>
        </div>
        <div className="bg-gray-900/30 border border-gray-700/50 rounded-lg p-3">
          <p className="text-xs text-gray-500 mb-1">Expression Clarity</p>
          <p className="text-sm font-bold text-white">
            {detectedEmotion ? 'Clear ✓' : 'Unclear'}
          </p>
        </div>
      </div>
    </div>
  );
};