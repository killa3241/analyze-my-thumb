// src/pages/Compare.tsx
import React from 'react';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useCompareThumbnails } from '../hooks/useCompareThumbnails';
import { CompareThumbnailInput } from '../components/CompareThumbnailInput';
import { WinnerDeclaration } from '../components/WinnerDeclaration';
import { ComparisonDashboard } from '../components/ComparisonDashboard';
import { ComparisonMetrics } from '../components/ComparisonMetrics';

export const Compare: React.FC = () => {
  const navigate = useNavigate();
  const {
    thumbnailA,
    thumbnailB,
    comparisonResult,
    analyzeThumbnailA,
    analyzeThumbnailB,
    setPreviewUrlA,
    setPreviewUrlB,
    resetComparison
  } = useCompareThumbnails();

  const bothAnalyzed = thumbnailA.result && thumbnailB.result;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-blue-900/20">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back</span>
              </button>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent">
                  Compare Thumbnails
                </h1>
                <p className="text-sm text-gray-400 mt-1">
                  Analyze two thumbnails side-by-side and see which performs better
                </p>
              </div>
            </div>
            {bothAnalyzed && (
              <button
                onClick={resetComparison}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg hover:scale-105 transition-all shadow-lg"
              >
                <RefreshCw className="w-4 h-4" />
                Compare New
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Input Panels */}
        <div className="grid md:grid-cols-2 gap-6">
          <CompareThumbnailInput
            side="A"
            onAnalyze={analyzeThumbnailA}
            isAnalyzing={thumbnailA.isAnalyzing}
            previewUrl={thumbnailA.previewUrl}
            onPreviewChange={setPreviewUrlA}
            error={thumbnailA.error}
          />
          <CompareThumbnailInput
            side="B"
            onAnalyze={analyzeThumbnailB}
            isAnalyzing={thumbnailB.isAnalyzing}
            previewUrl={thumbnailB.previewUrl}
            onPreviewChange={setPreviewUrlB}
            error={thumbnailB.error}
          />
        </div>

        {/* Winner Declaration - Only shows when both are analyzed */}
        {comparisonResult && (
          <div className="animate-fade-in">
            <WinnerDeclaration comparison={comparisonResult} />
          </div>
        )}

        {/* Comparison Dashboard - Shows loading states independently */}
        <div className="relative">
          <ComparisonDashboard
            resultA={thumbnailA.result}
            resultB={thumbnailB.result}
            previewUrlA={thumbnailA.previewUrl}
            previewUrlB={thumbnailB.previewUrl}
            isAnalyzingA={thumbnailA.isAnalyzing}
            isAnalyzingB={thumbnailB.isAnalyzing}
          />
        </div>

        {/* Detailed Metrics - Only shows when both are analyzed */}
        {bothAnalyzed && (
          <div className="animate-fade-in">
            <ComparisonMetrics
              resultA={thumbnailA.result}
              resultB={thumbnailB.result}
            />
          </div>
        )}

        {/* Instructions - Shows when nothing is analyzed yet */}
        {!thumbnailA.result && !thumbnailB.result && !thumbnailA.isAnalyzing && !thumbnailB.isAnalyzing && (
          <div className="bg-gray-800/30 rounded-xl p-8 border border-gray-700 backdrop-blur-sm">
            <h2 className="text-2xl font-bold text-white mb-4">How to Use</h2>
            <div className="grid md:grid-cols-3 gap-6 text-gray-300">
              <div className="space-y-2">
                <div className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  01
                </div>
                <h3 className="text-lg font-semibold text-white">Upload Thumbnails</h3>
                <p className="text-sm text-gray-400">
                  Upload or paste YouTube URLs for both thumbnails you want to compare
                </p>
              </div>
              <div className="space-y-2">
                <div className="text-4xl font-bold bg-gradient-to-r from-pink-400 to-blue-400 bg-clip-text text-transparent">
                  02
                </div>
                <h3 className="text-lg font-semibold text-white">Analyze Both</h3>
                <p className="text-sm text-gray-400">
                  Click analyze for each thumbnail. They'll be processed independently
                </p>
              </div>
              <div className="space-y-2">
                <div className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                  03
                </div>
                <h3 className="text-lg font-semibold text-white">See Winner</h3>
                <p className="text-sm text-gray-400">
                  View the winner declaration and detailed metric comparisons
                </p>
              </div>
            </div>

            <div className="mt-8 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <h4 className="text-blue-400 font-semibold mb-2">💡 Tip</h4>
              <p className="text-sm text-gray-300">
                The winner is determined by a weighted scoring system that considers attractiveness (40%), 
                contrast (20%), brightness optimization (15%), word count (15%), and face presence (10%).
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-gray-800 bg-gray-900/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-gray-500 text-sm">
            Compare mode helps you make data-driven decisions for your thumbnail designs
          </p>
        </div>
      </footer>
    </div>
  );
};