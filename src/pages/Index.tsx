// src/pages/Index.tsx
import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Eye, BarChart3, Moon, Sun, History, Share2 } from 'lucide-react';
import { ThumbnailInput } from '@/components/ThumbnailInput';
import { AnalysisDashboard } from '@/components/AnalysisDashboard';
import { HistorySidebar } from '@/components/HistorySidebar';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { useAnalyzeThumbnail } from '@/hooks/useAnalyzeThumbnail';
import { useHistory } from '@/hooks/useHistory';

export function Index() {
  const location = useLocation()
  const [darkMode, setDarkMode] = useState(true);
  const [showHistory, setShowHistory] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [selectedObject, setSelectedObject] = useState<number | null>(null);
  
  // Toast state with fade control
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [isToastFadingOut, setIsToastFadingOut] = useState(false);

  const { history, addToHistory, removeFromHistory, clearHistory } = useHistory();
  const { analyzeThumbnail, result, isAnalyzing, error, progress } = useAnalyzeThumbnail();

  const handleAnalyze = async (source: { type: 'url' | 'file'; url?: string; file?: File }) => {
    setSelectedObject(null);
    
    try {
      const analysisResult = await analyzeThumbnail(
        source.type === 'url' ? source.url! : source.file!
      );
      
      if (analysisResult && previewUrl) {
        addToHistory({
          thumbnail: previewUrl,
          score: analysisResult.attractiveness_score,
          youtubeUrl: source.type === 'url' ? source.url : undefined,
          fileName: source.type === 'file' ? source.file!.name : undefined
        });
      }
    } catch (err) {
      console.error('Analysis failed:', err);
    }
  };
  
  // Toast animation with fade in/out
  useEffect(() => {
    let fadeOutTimer: NodeJS.Timeout | undefined;
    let hideTimer: NodeJS.Timeout | undefined;

    if (result && !isAnalyzing && !error) {
      // Reset fade state and show toast
      setIsToastFadingOut(false);
      setShowSuccessToast(true);
      
      // Start fade out after 1.5 seconds (2s total - 0.5s fade duration)
      fadeOutTimer = setTimeout(() => {
        setIsToastFadingOut(true);
      }, 1500);
      
      // Completely hide toast after 2 seconds
      hideTimer = setTimeout(() => {
        setShowSuccessToast(false);
        setIsToastFadingOut(false);
      }, 2000);
    } else if (isAnalyzing || error) {
      // Hide immediately when new analysis starts or error occurs
      setShowSuccessToast(false);
      setIsToastFadingOut(false);
    }

    return () => {
      if (fadeOutTimer) clearTimeout(fadeOutTimer);
      if (hideTimer) clearTimeout(hideTimer);
    };
  }, [result, isAnalyzing, error]);

  const handleHistoryItemClick = (item: typeof history[0]) => {
    setPreviewUrl(item.thumbnail);
    setShowHistory(false);
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'} transition-colors duration-300`}>
      {/* Animated Background Pattern */}
      <div className="fixed inset-0 opacity-10 pointer-events-none">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: 'radial-gradient(circle, #8B5CF6 1px, transparent 1px)',
            backgroundSize: '40px 40px'
          }}
        />
      </div>

      {/* Header */}
      <header className="relative border-b border-gray-800/50 backdrop-blur-xl bg-gray-900/80 top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="relative">
                <Eye className="h-8 w-8 text-purple-500" />
                <BarChart3 className="h-4 w-4 text-pink-500 absolute -bottom-1 -right-1" />
              </div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
                Thumblytics Pro
              </h1>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/" className={`text-sm font-medium pb-1 ${
                  location.pathname === '/' ? 'border-b-2 border-purple-500 text-white' : 'text-gray-400 hover:text-white'
                }`}
              >
                Analyze
              </Link>
              <Link
                to="/compare"
                className={`text-sm font-medium pb-1 ${
                  location.pathname === '/compare' ? 'border-b-2 border-purple-500 text-white' : 'text-gray-400 hover:text-white'
                }`}
              >
                Compare
              </Link>

              <button
                onClick={() => setShowHistory(!showHistory)}
                className="text-sm font-medium text-gray-400 hover:text-white transition-colors flex items-center gap-1"
              >
                <History className="h-4 w-4" />
                History
                {history.length > 0 && (
                  <span className="ml-1 bg-purple-500 text-white text-xs rounded-full px-2 py-0.5">
                    {history.length}
                  </span>
                )}
              </button>
              <button className="text-sm font-medium text-gray-400 hover:text-white transition-colors">
                Guide
              </button>
            </nav>

            {/* Action Buttons */}
            <div className="flex items-center gap-3">
              <button
                onClick={toggleDarkMode}
                className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
                aria-label="Toggle theme"
              >
                {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </button>
              <button
                onClick={() => {
                  if (navigator.share) {
                    navigator.share({
                      title: 'Thumblytics Pro',
                      text: 'Analyze your YouTube thumbnails with AI',
                      url: window.location.href
                    });
                  }
                }}
                className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
                aria-label="Share"
              >
                <Share2 className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* History Sidebar */}
      <HistorySidebar
        isOpen={showHistory}
        onClose={() => setShowHistory(false)}
        history={history}
        onRemoveItem={removeFromHistory}  
        onClearAll={clearHistory}
        onSelectItem={handleHistoryItemClick}  
      />

      {/* Main Content */}
      <main className="container mx-auto px-4 py-12">
        <div className="max-w-7xl mx-auto space-y-12">
          {/* Input Section */}
          <div className="max-w-2xl mx-auto">
            <ThumbnailInput
              onAnalyze={handleAnalyze}
              isAnalyzing={isAnalyzing}
              progress={progress}
              previewUrl={previewUrl}
              onPreviewChange={setPreviewUrl}
              selectedObject={selectedObject}
              detectedObjects={result?.detected_objects}
            />
          </div>

          {/* Loading State */}
          {isAnalyzing && <LoadingSkeleton />}

          {/* Error Display */}
          {error && !isAnalyzing && (
            <div className="max-w-2xl mx-auto">
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6 text-center">
                <p className="text-red-300 mb-4">{error}</p>
                <button
                  onClick={() => window.location.reload()}
                  className="bg-red-600 hover:bg-red-700 px-6 py-2 rounded-lg font-medium transition-colors"
                >
                  Try Again
                </button>
              </div>
            </div>
          )}

          {/* Results Dashboard */}
          {result && !isAnalyzing && previewUrl && (
            <AnalysisDashboard
              result={result}
              previewUrl={previewUrl}
              selectedObject={selectedObject}
              onObjectSelect={setSelectedObject}
            />
          )}

          {/* Empty State */}
          {!result && !isAnalyzing && !error && (
            <div className="max-w-2xl mx-auto text-center py-12">
              <div className="bg-gray-800/30 border border-gray-700/50 rounded-2xl p-12">
                <Eye className="h-16 w-16 mx-auto mb-4 text-purple-500/50" />
                <h3 className="text-2xl font-bold text-gray-400 mb-2">
                  Ready to Analyze
                </h3>
                <p className="text-gray-500">
                  Upload a thumbnail or paste a YouTube URL to get started
                </p>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-20 py-8">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-6 text-sm text-gray-400">
              <a href="#" className="hover:text-white transition-colors">
                About
              </a>
              <a href="#" className="hover:text-white transition-colors">
                API Docs
              </a>
              <a href="#" className="hover:text-white transition-colors">
                GitHub
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Contact
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Privacy Policy
              </a>
            </div>
            <p className="text-sm text-gray-500">
              © 2025 Thumblytics Pro. All rights reserved.
            </p>
          </div>
        </div>
      </footer>

      {/* Success Toast with Fade In/Out Animation */}
      {showSuccessToast && (
        <div 
          className={`fixed bottom-4 right-4 bg-green-500 text-white px-6 py-4 rounded-lg shadow-2xl flex items-center gap-3 z-50 transition-all duration-500 ${
            isToastFadingOut 
              ? 'opacity-0 translate-y-2' 
              : 'opacity-100 translate-y-0'
          }`}
          style={{
            animation: isToastFadingOut 
              ? 'none' 
              : 'fadeInSlideUp 0.5s ease-out'
          }}
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">✅</span>
            <p className="font-medium">Analysis Complete!</p>
          </div>
        </div>
      )}

      {/* CSS Animation (add to your global styles or inline style tag) */}
      <style>{`
        @keyframes fadeInSlideUp {
          from {
            opacity: 0;
            transform: translateY(0.5rem);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}