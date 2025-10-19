// src/components/ObjectDetectionGrid.tsx
import { Zap, Target, Image as ImageIcon } from 'lucide-react';
import { ObjectAnalysis } from '@/types/analysis';
import { CircularProgress } from './CircularProgress';
import { getObjectIcon, getContrastBadgeColor } from '@/lib/utils';

interface ObjectDetectionGridProps {
  objects: ObjectAnalysis[];
  onObjectSelect?: (index: number | null) => void;
  selectedObject?: number | null;
}

export const ObjectDetectionGrid = ({
  objects,
  onObjectSelect,
  selectedObject,
}: ObjectDetectionGridProps) => {
  const handleObjectClick = (index: number) => {
    if (onObjectSelect) {
      onObjectSelect(selectedObject === index ? null : index);
    }
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-6 rounded-2xl shadow-xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-yellow-500/10 rounded-lg">
          <Zap className="h-5 w-5 text-yellow-400" />
        </div>
        <h3 className="text-xl font-semibold text-white">Detected Objects</h3>
        <span className="text-sm text-gray-500">({objects.length} found)</span>
      </div>

      {objects.length === 0 ? (
        <div className="text-center py-12">
          <ImageIcon className="h-16 w-16 mx-auto text-gray-600 mb-4" />
          <p className="text-gray-400 font-medium mb-2">No objects detected</p>
          <p className="text-sm text-gray-600">
            Try a thumbnail with more distinct visual elements
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {objects.map((obj, idx) => (
              <div
                key={idx}
                onClick={() => handleObjectClick(idx)}
                className={`bg-gray-900/50 border rounded-xl p-4 cursor-pointer transition-all hover:scale-105 ${
                  selectedObject === idx
                    ? 'border-purple-500 shadow-lg shadow-purple-500/20 ring-2 ring-purple-500/50'
                    : 'border-gray-700 hover:border-purple-500/50'
                }`}
              >
                {/* Icon and Progress */}
                <div className="flex items-start justify-between mb-3">
                  <div className="text-5xl animate-bounce-slow">
                    {getObjectIcon(obj.label)}
                  </div>
                  <CircularProgress
                    percentage={obj.confidence * 100}
                    size={55}
                  />
                </div>

                {/* Label */}
                <h4 className="font-bold text-lg capitalize mb-3 text-white">
                  {obj.label}
                </h4>

                {/* Metrics */}
                <div className="space-y-2">
                  {/* Confidence */}
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">Confidence</span>
                    <span className="text-sm font-bold text-purple-400">
                      {Math.round(obj.confidence * 100)}%
                    </span>
                  </div>

                  {/* Confidence Bar */}
                  <div className="w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-purple-600 to-pink-500 transition-all duration-1000"
                      style={{ width: `${obj.confidence * 100}%` }}
                    />
                  </div>

                  {/* Contrast */}
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-sm text-gray-400">Contrast</span>
                    <span
                      className={`text-xs px-2 py-1 rounded-full border font-medium ${getContrastBadgeColor(
                        obj.contrast_score_vs_bg
                      )}`}
                    >
                      {Math.round(obj.contrast_score_vs_bg * 100)}%
                    </span>
                  </div>
                </div>

                {/* Selected Indicator */}
                {selectedObject === idx && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <p className="text-xs text-purple-400 flex items-center gap-1 animate-pulse">
                      <Target className="h-3 w-3" />
                      Location highlighted on thumbnail
                    </p>
                  </div>
                )}

                {/* ✅ FIX: Position Info with null check */}
                {obj.bbox && obj.bbox.length >= 2 && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>Position:</span>
                      <span className="font-mono">
                        {Math.round(obj.bbox[0])}, {Math.round(obj.bbox[1])}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Helper Text */}
          <div className="mt-6 p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
            <p className="text-sm text-purple-300 flex items-center gap-2">
              <Target className="h-4 w-4 flex-shrink-0" />
              <span>
                Click on any object card to highlight its location on the thumbnail image
              </span>
            </p>
          </div>
        </>
      )}
    </div>
  );
};