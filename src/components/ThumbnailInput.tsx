// src/components/ThumbnailInput.tsx
import { useState } from 'react';
import { Upload, Link as LinkIcon, Loader2, AlertCircle, X } from 'lucide-react';

interface ThumbnailInputProps {
  onAnalyze: (source: { type: 'url' | 'file'; url?: string; file?: File }) => void;
  isAnalyzing: boolean;
  progress: number;
  previewUrl: string | null;
  onPreviewChange: (url: string | null) => void;
  selectedObject: number | null;
  detectedObjects?: Array<{ bbox: number[] }>;
}

export const ThumbnailInput = ({
  onAnalyze,
  isAnalyzing,
  progress,
  previewUrl,
  onPreviewChange,
  selectedObject,
  detectedObjects = []
}: ThumbnailInputProps) => {
  const [activeTab, setActiveTab] = useState<'url' | 'upload'>('url');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleYoutubeAnalyze = () => {
    setError(null);
    const videoIdMatch = youtubeUrl.match(
      /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/
    );
    
    if (videoIdMatch && videoIdMatch[1]) {
      const thumbnailUrl = `https://img.youtube.com/vi/${videoIdMatch[1]}/maxresdefault.jpg`;
      onPreviewChange(thumbnailUrl);
      onAnalyze({ type: 'url', url: youtubeUrl });
    } else {
      setError('Invalid YouTube URL. Please enter a valid video URL.');
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const file = e.target.files?.[0];
    
    if (file) {
      if (!file.type.startsWith('image/')) {
        setError('Please upload an image file (PNG, JPG, etc.)');
        return;
      }
      
      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }
      
      setUploadedFile(file);
      const url = URL.createObjectURL(file);
      onPreviewChange(url);
      onAnalyze({ type: 'file', file });
      e.target.value = '';
    }
  };

  const handleClearPreview = () => {
    onPreviewChange(null);
    setUploadedFile(null);
    setYoutubeUrl('');
    setError(null);
  };

  const exampleVideos = [
    { id: 'dQw4w9WgXcQ', label: 'Music Video' },
    { id: 'jNQXAC9IVRw', label: 'Me at the zoo' }
  ];

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-8 rounded-2xl shadow-2xl">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-4xl font-bold bg-gradient-to-r from-purple-500 via-pink-500 to-purple-500 bg-clip-text text-transparent mb-3 animate-pulse">
          AI-Powered Thumbnail Analysis
        </h2>
        <p className="text-gray-400 text-lg">
          Get instant insights to boost your click-through rate
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 bg-gray-900/50 p-1 rounded-lg">
        <button
          onClick={() => setActiveTab('url')}
          disabled={isAnalyzing}
          className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-medium transition-all ${
            activeTab === 'url'
              ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <LinkIcon className="h-4 w-4" />
          YouTube URL
        </button>
        <button
          onClick={() => setActiveTab('upload')}
          disabled={isAnalyzing}
          className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-medium transition-all ${
            activeTab === 'upload'
              ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Upload className="h-4 w-4" />
          Upload Image
        </button>
      </div>

      {/* URL Input */}
      {activeTab === 'url' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-300">
              YouTube Video URL
            </label>
            <input
              type="text"
              placeholder="https://youtube.com/watch?v=..."
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              disabled={isAnalyzing}
              className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>
          
          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-gray-500">Examples:</span>
            {exampleVideos.map(video => (
              <button
                key={video.id}
                onClick={() => setYoutubeUrl(`https://youtube.com/watch?v=${video.id}`)}
                disabled={isAnalyzing}
                className="text-xs bg-gray-800 hover:bg-gray-700 px-3 py-1 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {video.label}
              </button>
            ))}
          </div>
          
          <button
            onClick={handleYoutubeAnalyze}
            disabled={isAnalyzing || !youtubeUrl}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-4 rounded-lg transition-all transform hover:scale-105 active:scale-95 shadow-lg"
          >
            {isAnalyzing ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin" />
                Analyzing... {progress}%
              </span>
            ) : (
              'Analyze Thumbnail'
            )}
          </button>
        </div>
      )}

      {/* File Upload */}
      {activeTab === 'upload' && (
        <div className="space-y-4">
          <label className="block">
            <div className="border-2 border-dashed border-gray-700 hover:border-purple-500 rounded-lg p-8 text-center cursor-pointer transition-all group">
              <Upload className="h-12 w-12 mx-auto mb-4 text-gray-500 group-hover:text-purple-500 transition-colors" />
              <p className="text-gray-400 group-hover:text-white transition-colors">
                Click to upload or drag and drop
              </p>
              <p className="text-sm text-gray-600 mt-2">PNG, JPG up to 10MB</p>
            </div>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              disabled={isAnalyzing}
              className="hidden"
            />
          </label>
          
          {uploadedFile && (
            <div className="flex items-center justify-between bg-gray-900/50 rounded-lg px-4 py-3">
              <p className="text-sm text-gray-400 truncate flex-1">
                Selected: {uploadedFile.name}
              </p>
              <button
                onClick={handleClearPreview}
                disabled={isAnalyzing}
                className="ml-2 text-red-400 hover:text-red-300 disabled:opacity-50"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Preview */}
      {previewUrl && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-300">Preview</label>
            {!isAnalyzing && (
              <button
                onClick={handleClearPreview}
                className="text-xs text-gray-400 hover:text-white transition-colors"
              >
                Clear
              </button>
            )}
          </div>
          <div className="relative rounded-lg overflow-hidden border border-gray-700 shadow-2xl group">
            <img
              src={previewUrl}
              alt="Thumbnail preview"
              className="w-full h-auto transition-transform duration-300 group-hover:scale-105"
            />
            {/* Object Detection Overlay */}
            {selectedObject !== null && detectedObjects[selectedObject] && (
              <div
                className="absolute border-4 border-purple-500 pointer-events-none animate-pulse"
                style={{
                  left: `${detectedObjects[selectedObject].bbox[0] / 12.8}%`,
                  top: `${detectedObjects[selectedObject].bbox[1] / 7.2}%`,
                  width: `${(detectedObjects[selectedObject].bbox[2] - detectedObjects[selectedObject].bbox[0]) / 12.8}%`,
                  height: `${(detectedObjects[selectedObject].bbox[3] - detectedObjects[selectedObject].bbox[1]) / 7.2}%`,
                }}
              />
            )}
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 bg-red-500/20 border border-red-500/50 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-red-300">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-400 hover:text-red-300"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
};