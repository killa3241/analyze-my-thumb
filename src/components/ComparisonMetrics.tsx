// src/components/ui/ComparisonMetrics.tsx
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts';
import { AnalysisResult } from '../types/comparison';

interface ComparisonMetricsProps {
  resultA: AnalysisResult;
  resultB: AnalysisResult;
}

export const ComparisonMetrics: React.FC<ComparisonMetricsProps> = ({ resultA, resultB }) => {
  // Prepare data for radar chart
  const radarData = [
    {
      metric: 'Attractiveness',
      A: resultA.attractiveness_score,
      B: resultB.attractiveness_score,
      fullMark: 100
    },
    {
      metric: 'Contrast',
      A: resultA.contrast_level,
      B: resultB.contrast_level,
      fullMark: 100
    },
    {
      metric: 'Brightness',
      A: Math.max(0, 100 - Math.abs(resultA.average_brightness - 154) / 1.54),
      B: Math.max(0, 100 - Math.abs(resultB.average_brightness - 154) / 1.54),
      fullMark: 100
    },
    {
      metric: 'Word Count',
      A: resultA.word_count >= 3 && resultA.word_count <= 7 ? 100 : Math.max(0, 100 - Math.abs(5 - resultA.word_count) * 20),
      B: resultB.word_count >= 3 && resultB.word_count <= 7 ? 100 : Math.max(0, 100 - Math.abs(5 - resultB.word_count) * 20),
      fullMark: 100
    },
    {
      metric: 'Face Impact',
      A: resultA.face_count > 0 ? (resultA.detected_emotion && resultA.detected_emotion !== 'neutral' ? 100 : 50) : 0,
      B: resultB.face_count > 0 ? (resultB.detected_emotion && resultB.detected_emotion !== 'neutral' ? 100 : 50) : 0,
      fullMark: 100
    }
  ];

  // Prepare data for bar chart
  const barData = [
    {
      name: 'Attractiveness',
      A: resultA.attractiveness_score,
      B: resultB.attractiveness_score
    },
    {
      name: 'Contrast',
      A: resultA.contrast_level,
      B: resultB.contrast_level
    },
    {
      name: 'Brightness',
      A: resultA.average_brightness,
      B: resultB.average_brightness
    },
    {
      name: 'Word Count',
      A: resultA.word_count,
      B: resultB.word_count
    },
    {
      name: 'Face Count',
      A: resultA.face_count,
      B: resultB.face_count
    }
  ];

  // Compare objects detected
  const objectsA = resultA.detected_objects?.slice(0, 5) || [];
  const objectsB = resultB.detected_objects?.slice(0, 5) || [];

  return (
    <div className="space-y-8">
      <h2 className="text-3xl font-bold text-white mb-6">Detailed Comparison</h2>

      {/* Radar Chart - Overall Metrics */}
      <div className="bg-gray-800/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700">
        <h3 className="text-xl font-semibold text-white mb-4">Overall Performance</h3>
        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#374151" />
            <PolarAngleAxis dataKey="metric" stroke="#9CA3AF" />
            <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#9CA3AF" />
            <Radar
              name="Thumbnail A"
              dataKey="A"
              stroke="#A855F7"
              fill="#A855F7"
              fillOpacity={0.5}
            />
            <Radar
              name="Thumbnail B"
              dataKey="B"
              stroke="#3B82F6"
              fill="#3B82F6"
              fillOpacity={0.5}
            />
            <Legend />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px'
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Bar Chart - Direct Comparison */}
      <div className="bg-gray-800/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700">
        <h3 className="text-xl font-semibold text-white mb-4">Metric Comparison</h3>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Bar dataKey="A" fill="#A855F7" name="Thumbnail A" />
            <Bar dataKey="B" fill="#3B82F6" name="Thumbnail B" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Progress Bars - Head to Head */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Text Content Comparison */}
        <div className="bg-gray-800/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Text Content</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-purple-400 font-medium">Thumbnail A</span>
                <span className="text-gray-400">{resultA.word_count} words</span>
              </div>
              <div className="text-sm text-gray-300 bg-gray-900/50 p-3 rounded-lg h-20 overflow-y-auto">
                {resultA.text_content || 'No text detected'}
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-blue-400 font-medium">Thumbnail B</span>
                <span className="text-gray-400">{resultB.word_count} words</span>
              </div>
              <div className="text-sm text-gray-300 bg-gray-900/50 p-3 rounded-lg h-20 overflow-y-auto">
                {resultB.text_content || 'No text detected'}
              </div>
            </div>
          </div>
        </div>

        {/* Emotion & Face Detection */}
        <div className="bg-gray-800/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Faces & Emotion</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-purple-500/10 rounded-lg border border-purple-500/30">
              <div>
                <p className="text-purple-400 font-medium">Thumbnail A</p>
                <p className="text-sm text-gray-400">
                  {resultA.face_count} {resultA.face_count === 1 ? 'face' : 'faces'}
                </p>
              </div>
              <div className="text-right">
                <p className="text-white font-semibold capitalize">
                  {resultA.detected_emotion || 'N/A'}
                </p>
                <p className="text-xs text-gray-500">Emotion</p>
              </div>
            </div>
            <div className="flex items-center justify-between p-4 bg-blue-500/10 rounded-lg border border-blue-500/30">
              <div>
                <p className="text-blue-400 font-medium">Thumbnail B</p>
                <p className="text-sm text-gray-400">
                  {resultB.face_count} {resultB.face_count === 1 ? 'face' : 'faces'}
                </p>
              </div>
              <div className="text-right">
                <p className="text-white font-semibold capitalize">
                  {resultB.detected_emotion || 'N/A'}
                </p>
                <p className="text-xs text-gray-500">Emotion</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Objects Detected */}
      <div className="bg-gray-800/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700">
        <h3 className="text-xl font-semibold text-white mb-4">Detected Objects</h3>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-purple-400 font-medium mb-3">Thumbnail A</h4>
            {objectsA.length > 0 ? (
              <div className="space-y-2">
                {objectsA.map((obj, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-gray-900/50 rounded">
                    <span className="text-gray-300">{obj.label}</span>
                    <span className="text-purple-400 text-sm">
                      {Math.round(obj.confidence * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 italic">No objects detected</p>
            )}
          </div>
          <div>
            <h4 className="text-blue-400 font-medium mb-3">Thumbnail B</h4>
            {objectsB.length > 0 ? (
              <div className="space-y-2">
                {objectsB.map((obj, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-gray-900/50 rounded">
                    <span className="text-gray-300">{obj.label}</span>
                    <span className="text-blue-400 text-sm">
                      {Math.round(obj.confidence * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 italic">No objects detected</p>
            )}
          </div>
        </div>
      </div>

      {/* Dominant Colors */}
      {(resultA.dominant_colors || resultB.dominant_colors) && (
        <div className="bg-gray-800/50 rounded-xl p-6 backdrop-blur-sm border border-gray-700">
          <h3 className="text-xl font-semibold text-white mb-4">Dominant Colors</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-purple-400 font-medium mb-3">Thumbnail A</h4>
              <div className="flex gap-2">
                {resultA.dominant_colors?.slice(0, 5).map((color, idx) => (
                  <div
                    key={idx}
                    className="w-12 h-12 rounded-lg border-2 border-gray-700"
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-blue-400 font-medium mb-3">Thumbnail B</h4>
              <div className="flex gap-2">
                {resultB.dominant_colors?.slice(0, 5).map((color, idx) => (
                  <div
                    key={idx}
                    className="w-12 h-12 rounded-lg border-2 border-gray-700"
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};