// src/components/ui/WinnerDeclaration.tsx
import React, { useState } from 'react';
import { Trophy, ChevronDown, ChevronUp } from 'lucide-react';
import { ComparisonResult } from '../types/comparison';

interface WinnerDeclarationProps {
  comparison: ComparisonResult;
}

export const WinnerDeclaration: React.FC<WinnerDeclarationProps> = ({ comparison }) => {
  const [showBreakdown, setShowBreakdown] = useState(false);

  const { winner, scoreA, scoreB, scoreDifference, metricBreakdown, recommendations } = comparison;

  const winnerColors = {
    A: {
      gradient: 'from-purple-500 via-pink-500 to-purple-600',
      text: 'text-purple-400',
      border: 'border-purple-500',
      bg: 'bg-purple-500/20'
    },
    B: {
      gradient: 'from-blue-500 via-cyan-500 to-blue-600',
      text: 'text-blue-400',
      border: 'border-blue-500',
      bg: 'bg-blue-500/20'
    },
    TIE: {
      gradient: 'from-yellow-400 via-orange-500 to-yellow-600',
      text: 'text-yellow-400',
      border: 'border-yellow-500',
      bg: 'bg-yellow-500/20'
    }
  };

  const colors = winnerColors[winner];

  return (
    <div className="animate-scale-in">
      {/* Main Winner Card */}
      <div className={`relative overflow-hidden rounded-2xl border-2 ${colors.border} bg-gradient-to-br from-gray-900/95 to-gray-800/95 backdrop-blur-xl shadow-2xl`}>
        {/* Animated Background Gradient */}
        <div className={`absolute inset-0 bg-gradient-to-r ${colors.gradient} opacity-10 animate-pulse`} />
        
        <div className="relative p-8">
          {/* Trophy Icon with Animation */}
          <div className="flex justify-center mb-4">
            <div className="relative">
              <Trophy className={`w-24 h-24 ${colors.text} animate-bounce-slow`} />
              <div className={`absolute inset-0 bg-gradient-to-r ${colors.gradient} opacity-20 blur-xl animate-pulse`} />
            </div>
          </div>

          {/* Winner Text */}
          <h2 className="text-4xl font-bold text-center mb-2">
            {winner === 'TIE' ? (
              <span className={`bg-gradient-to-r ${colors.gradient} bg-clip-text text-transparent`}>
                It's a Tie!
              </span>
            ) : (
              <>
                <span className={`bg-gradient-to-r ${colors.gradient} bg-clip-text text-transparent`}>
                  Thumbnail {winner}
                </span>
                <span className="text-gray-400"> Wins!</span>
              </>
            )}
          </h2>

          {/* Score Display */}
          <div className="flex items-center justify-center gap-8 mb-6">
            <div className="text-center">
              <div className={`text-3xl font-bold ${winner === 'A' ? colors.text : 'text-gray-500'}`}>
                {scoreA}
              </div>
              <div className="text-sm text-gray-400">Thumbnail A</div>
            </div>

            <div className="text-4xl font-bold text-gray-600">VS</div>

            <div className="text-center">
              <div className={`text-3xl font-bold ${winner === 'B' ? colors.text : 'text-gray-500'}`}>
                {scoreB}
              </div>
              <div className="text-sm text-gray-400">Thumbnail B</div>
            </div>
          </div>

          {/* Score Difference */}
          {winner !== 'TIE' && (
            <div className="text-center mb-6">
              <p className="text-gray-400">
                Score Difference: <span className={`font-bold ${colors.text}`}>{scoreDifference} points</span>
              </p>
            </div>
          )}

          {/* Toggle Breakdown Button */}
          <button
            onClick={() => setShowBreakdown(!showBreakdown)}
            className={`w-full py-3 px-4 rounded-lg bg-gradient-to-r ${colors.gradient} text-white font-semibold flex items-center justify-center gap-2 hover:scale-105 transition-all shadow-lg`}
          >
            {showBreakdown ? (
              <>
                Hide Breakdown <ChevronUp className="w-5 h-5" />
              </>
            ) : (
              <>
                View Breakdown <ChevronDown className="w-5 h-5" />
              </>
            )}
          </button>
        </div>

        {/* Expandable Breakdown Section */}
        {showBreakdown && (
          <div className="border-t border-gray-700 p-8 bg-gray-900/50 animate-slide-down">
            <h3 className="text-xl font-bold text-white mb-4">Metric Breakdown</h3>
            
            <div className="space-y-4 mb-6">
              {/* Attractiveness */}
              <MetricRow
                label="Attractiveness"
                valueA={metricBreakdown.attractiveness.A}
                valueB={metricBreakdown.attractiveness.B}
                winner={metricBreakdown.attractiveness.winner}
                unit="/100"
              />

              {/* Contrast */}
              <MetricRow
                label="Contrast"
                valueA={metricBreakdown.contrast.A}
                valueB={metricBreakdown.contrast.B}
                winner={metricBreakdown.contrast.winner}
                unit="/100"
              />

              {/* Brightness */}
              <MetricRow
                label="Brightness Score"
                valueA={metricBreakdown.brightness.A}
                valueB={metricBreakdown.brightness.B}
                winner={metricBreakdown.brightness.winner}
                unit="/100"
              />

              {/* Word Count */}
              <MetricRow
                label="Word Count Score"
                valueA={metricBreakdown.wordCount.A}
                valueB={metricBreakdown.wordCount.B}
                winner={metricBreakdown.wordCount.winner}
                unit="/100"
              />

              {/* Face Presence */}
              <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                <span className="text-gray-300 font-medium">Face Presence</span>
                <div className="flex items-center gap-4">
                  <span className={`${metricBreakdown.facePresence.winner === 'A' ? 'text-green-400' : 'text-gray-500'}`}>
                    {metricBreakdown.facePresence.A ? '✓' : '✗'} A
                  </span>
                  <span className="text-gray-600">vs</span>
                  <span className={`${metricBreakdown.facePresence.winner === 'B' ? 'text-green-400' : 'text-gray-500'}`}>
                    {metricBreakdown.facePresence.B ? '✓' : '✗'} B
                  </span>
                </div>
              </div>
            </div>

            {/* Recommendations */}
            {recommendations.length > 0 && (
              <div className="mt-6">
                <h4 className="text-lg font-semibold text-white mb-3">Recommendations</h4>
                <ul className="space-y-2">
                  {recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-gray-300">
                      <span className="text-yellow-400 mt-1">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Helper component for metric rows
const MetricRow: React.FC<{
  label: string;
  valueA: number;
  valueB: number;
  winner: 'A' | 'B' | 'TIE';
  unit: string;
}> = ({ label, valueA, valueB, winner, unit }) => {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
      <span className="text-gray-300 font-medium">{label}</span>
      <div className="flex items-center gap-4">
        <span className={`${winner === 'A' ? 'text-green-400 font-bold' : 'text-gray-500'}`}>
          {Math.round(valueA * 10) / 10}{unit}
        </span>
        <span className="text-gray-600">vs</span>
        <span className={`${winner === 'B' ? 'text-green-400 font-bold' : 'text-gray-500'}`}>
          {Math.round(valueB * 10) / 10}{unit}
        </span>
      </div>
    </div>
  );
};