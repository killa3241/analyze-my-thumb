// src/components/AnalysisDashboard.tsx
import { useState } from 'react';
import { Target, Download, Share2, TrendingUp, FileText, Image as ImageIcon, Loader2 } from 'lucide-react';
import { AnalysisResult } from '@/types/analysis';
import { MetricsOverview } from './MetricsOverview';
import { ObjectDetectionGrid } from './ObjectDetectionGrid';
import { FaceAnalysisCard } from './FaceAnalysisCard';
import { AISuggestionsPanel } from './AISuggestionsPanel';
import { getScoreColor, getScoreGrade } from '@/lib/utils';
import { exportAsJSON, exportAsImage, exportAsPDF } from '@/lib/exportUtils';

interface AnalysisDashboardProps {
  result: AnalysisResult;
  previewUrl: string | null;
  onObjectSelect: (index: number | null) => void;
  selectedObject: number | null;
}

export const AnalysisDashboard = ({
  result,
  previewUrl,
  onObjectSelect,
  selectedObject
}: AnalysisDashboardProps) => {
  const [exportFormat, setExportFormat] = useState<'json' | 'pdf' | 'image' | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: 'Thumblytics Analysis',
        text: `My thumbnail scored ${result.attractiveness_score}!`,
        url: window.location.href
      }).catch(err => console.log('Share failed:', err));
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(
        `Check out my Thumblytics score: ${result.attractiveness_score}/100! ${window.location.href}`
      ).then(() => {
        alert('Link copied to clipboard!');
      });
    }
  };

  const handleExport = async (format: 'json' | 'pdf' | 'image') => {
    setExportFormat(format);
    setExportError(null);

    try {
      switch (format) {
        case 'json':
          exportAsJSON(result, previewUrl);
          break;
        case 'pdf':
          await exportAsPDF('analysis-dashboard-content', result, previewUrl);
          break;
        case 'image':
          await exportAsImage('analysis-dashboard-content', result, previewUrl);
          break;
      }
      
      // Success feedback
      setTimeout(() => setExportFormat(null), 2000);
    } catch (error) {
      console.error('Export failed:', error);
      setExportError(`Failed to export as ${format.toUpperCase()}. Please try again.`);
      setExportFormat(null);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-700">
      {/* Wrapper div with ID for export */}
      <div id="analysis-dashboard-content" className="space-y-6">
        {/* Hero Score Section */}
        <div className="bg-gradient-to-br from-purple-900/50 to-pink-900/50 backdrop-blur-sm border border-purple-500/30 p-8 rounded-2xl shadow-2xl text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Target className="h-6 w-6 text-purple-400" />
            <h2 className="text-2xl font-bold">Attractiveness Score</h2>
          </div>
          
          <div className={`text-8xl font-bold ${getScoreColor(result.attractiveness_score)} mb-2 animate-pulse`}>
            {result.attractiveness_score}
          </div>
          
          <p className="text-2xl text-gray-300 mb-4">
            {getScoreGrade(result.attractiveness_score)}
          </p>
          
          <div className="flex items-center justify-center gap-4 mt-6 flex-wrap">
            <button
              onClick={() => handleExport('pdf')}
              disabled={exportFormat !== null}
              className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {exportFormat === 'pdf' ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4" />
                  Download Report
                </>
              )}
            </button>
            <button
              onClick={handleShare}
              className="flex items-center gap-2 bg-pink-600 hover:bg-pink-700 px-6 py-3 rounded-lg font-medium transition-colors"
            >
              <Share2 className="h-4 w-4" />
              Share Results
            </button>
          </div>
        </div>

        {/* Preview Image Section (for export) */}
        {previewUrl && (
          <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-700/30 p-6 rounded-2xl">
            <h3 className="text-xl font-semibold mb-4 text-center">Analyzed Thumbnail</h3>
            <div className="flex justify-center">
              <img 
                src={previewUrl} 
                alt="Analyzed thumbnail" 
                className="max-w-full h-auto rounded-lg shadow-xl"
                crossOrigin="anonymous"
              />
            </div>
          </div>
        )}

        {/* Metrics Overview */}
        <MetricsOverview
          averageBrightness={result.average_brightness}
          contrastLevel={result.contrast_level}
          wordCount={result.word_count}
          textContent={result.text_content}
          dominantColors={result.dominant_colors}
        />

        {/* Object Detection */}
        <ObjectDetectionGrid
          objects={result.detected_objects}
          selectedObject={selectedObject}
          onObjectSelect={onObjectSelect}
        />

        {/* Face Analysis */}
        {result.face_count > 0 && (
          <FaceAnalysisCard
            faceCount={result.face_count}
            detectedEmotion={result.detected_emotion}
          />
        )}

        {/* AI Suggestions */}
        <AISuggestionsPanel suggestions={result.ai_suggestions} />

        {/* CTR Prediction */}
        <div className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 backdrop-blur-sm border border-blue-500/30 p-6 rounded-2xl shadow-xl">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-5 w-5 text-blue-400" />
            <h3 className="text-xl font-semibold">Predicted CTR Range</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <p className="text-sm text-gray-400 mb-2">Conservative</p>
              <p className="text-4xl font-bold text-red-400">
                {(result.attractiveness_score * 0.05).toFixed(1)}%
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-400 mb-2">Expected</p>
              <p className="text-5xl font-bold text-yellow-400">
                {(result.attractiveness_score * 0.08).toFixed(1)}%
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-400 mb-2">Optimistic</p>
              <p className="text-4xl font-bold text-green-400">
                {(result.attractiveness_score * 0.12).toFixed(1)}%
              </p>
            </div>
          </div>
          
          <div className="mt-6 bg-gray-900/50 rounded-lg p-4">
            <p className="text-sm text-gray-400">
              📊 Based on your score of{' '}
              <span className="text-purple-400 font-bold">{result.attractiveness_score}</span>, 
              this thumbnail is predicted to achieve a CTR between{' '}
              <span className="text-yellow-400 font-bold">
                {(result.attractiveness_score * 0.05).toFixed(1)}%
              </span>
              {' '}and{' '}
              <span className="text-green-400 font-bold">
                {(result.attractiveness_score * 0.12).toFixed(1)}%
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* Export Error Message */}
      {exportError && (
        <div className="bg-red-900/30 border border-red-500/50 text-red-200 px-6 py-4 rounded-lg">
          {exportError}
        </div>
      )}

      {/* Export Options */}
      <div className="flex flex-wrap gap-4 justify-center">
        <button
          onClick={() => handleExport('json')}
          disabled={exportFormat !== null}
          className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 px-6 py-3 rounded-lg font-medium transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {exportFormat === 'json' ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Exporting...
            </>
          ) : (
            <>
              <FileText className="h-4 w-4" />
              Export as JSON
            </>
          )}
        </button>
        <button
          onClick={() => handleExport('pdf')}
          disabled={exportFormat !== null}
          className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 px-6 py-3 rounded-lg font-medium transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {exportFormat === 'pdf' ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Download className="h-4 w-4" />
              Download PDF Report
            </>
          )}
        </button>
        <button
          onClick={() => handleExport('image')}
          disabled={exportFormat !== null}
          className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 px-6 py-3 rounded-lg font-medium transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {exportFormat === 'image' ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Capturing...
            </>
          ) : (
            <>
              <ImageIcon className="h-4 w-4" />
              Download Annotated
            </>
          )}
        </button>
      </div>
    </div>
  );
};