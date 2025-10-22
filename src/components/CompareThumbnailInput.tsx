// src/components/CompareThumbnailInput.tsx
import React, { useState, useRef, ChangeEvent } from 'react';
import { Upload, Link as LinkIcon, Loader2 } from 'lucide-react';

interface CompareThumbnailInputProps {
  side: 'A' | 'B';
  onAnalyze: (input: { type: 'url' | 'file'; url?: string; file?: File }) => void;
  isAnalyzing: boolean;
  previewUrl: string | null;
  onPreviewChange: (url: string | null) => void;
  error: string | null;
}

export const CompareThumbnailInput: React.FC<CompareThumbnailInputProps> = ({
  side,
  onAnalyze,
  isAnalyzing,
  previewUrl,
  onPreviewChange,
  error
}) => {
  const [inputMethod, setInputMethod] = useState<'upload' | 'url'>('upload');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sideColors = {
    A: {
      gradient: 'from-purple-500 to-pink-500',
      border: 'border-purple-500',
      text: 'text-purple-400',
      glow: 'shadow-purple-500/50',
      bg: 'bg-purple-500/10'
    },
    B: {
      gradient: 'from-blue-500 to-cyan-500',
      border: 'border-blue-500',
      text: 'text-blue-400',
      glow: 'shadow-blue-500/50',
      bg: 'bg-blue-500/10'
    }
  };

  const colors = sideColors[side];

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        onPreviewChange(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAnalyze = () => {
    if (inputMethod === 'upload' && fileInputRef.current?.files?.[0]) {
      onAnalyze({ type: 'file', file: fileInputRef.current.files[0] });
    } else if (inputMethod === 'url' && youtubeUrl) {
      onAnalyze({ type: 'url', url: youtubeUrl });
      
      // Extract thumbnail from YouTube URL
      const videoId = extractYouTubeVideoId(youtubeUrl);
      if (videoId) {
        onPreviewChange(`https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`);
      }
    }
  };

  const extractYouTubeVideoId = (url: string): string | null => {
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
      /^([a-zA-Z0-9_-]{11})$/
    ];
    
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) return match[1];
    }
    return null;
  };

  const canAnalyze = previewUrl && !isAnalyzing;

  return (
    <div className={`border-2 ${colors.border} rounded-xl p-4 ${colors.bg} backdrop-blur-sm transition-all duration-300 hover:shadow-lg ${colors.glow}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className={`text-lg font-bold ${colors.text}`}>
          Thumbnail {side}
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setInputMethod('upload')}
            className={`px-3 py-1 rounded-lg text-sm transition-all ${
              inputMethod === 'upload'
                ? `bg-gradient-to-r ${colors.gradient} text-white`
                : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            <Upload className="inline w-4 h-4 mr-1" />
            Upload
          </button>
          <button
            onClick={() => setInputMethod('url')}
            className={`px-3 py-1 rounded-lg text-sm transition-all ${
              inputMethod === 'url'
                ? `bg-gradient-to-r ${colors.gradient} text-white`
                : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            <LinkIcon className="inline w-4 h-4 mr-1" />
            URL
          </button>
        </div>
      </div>

      {/* Input Area */}
      {inputMethod === 'upload' ? (
        <div className="mb-4">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
            id={`file-input-${side}`}
          />
          <label
            htmlFor={`file-input-${side}`}
            className={`block w-full p-8 border-2 border-dashed ${colors.border} rounded-lg cursor-pointer hover:bg-gray-800/50 transition-all text-center`}
          >
            <Upload className={`w-8 h-8 mx-auto mb-2 ${colors.text}`} />
            <p className="text-sm text-gray-400">
              Click to upload thumbnail {side}
            </p>
          </label>
        </div>
      ) : (
        <div className="mb-4">
          <input
            type="text"
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
            placeholder="Paste YouTube URL or Video ID"
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-all"
          />
        </div>
      )}

      {/* Preview */}
      {previewUrl && (
        <div className="mb-4 relative">
          <img
            src={previewUrl}
            alt={`Thumbnail ${side} preview`}
            className="w-full rounded-lg border-2 border-gray-700"
          />
          {isAnalyzing && (
            <div className="absolute inset-0 bg-black/70 rounded-lg flex items-center justify-center">
              <Loader2 className={`w-8 h-8 animate-spin ${colors.text}`} />
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Analyze Button */}
      <button
        onClick={handleAnalyze}
        disabled={!canAnalyze}
        className={`w-full py-3 rounded-lg font-semibold transition-all ${
          canAnalyze
            ? `bg-gradient-to-r ${colors.gradient} text-white hover:scale-105 shadow-lg ${colors.glow}`
            : 'bg-gray-800 text-gray-600 cursor-not-allowed'
        }`}
      >
        {isAnalyzing ? (
          <>
            <Loader2 className="inline w-5 h-5 mr-2 animate-spin" />
            Analyzing...
          </>
        ) : (
          `Analyze Thumbnail ${side}`
        )}
      </button>
    </div>
  );
};