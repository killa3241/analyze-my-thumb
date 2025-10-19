// src/components/HistorySidebar.tsx

import { X, Trash2 } from 'lucide-react';
import { HistoryItem } from '@/hooks/useHistory';
import { getScoreColor, formatTimestamp } from '@/lib/utils';

interface HistorySidebarProps {
  isOpen: boolean;
  onClose: () => void;
  history: HistoryItem[];
  onRemoveItem: (id: string) => void;
  onClearAll: () => void;
  onSelectItem?: (item: HistoryItem) => void;
}

export const HistorySidebar = ({
  isOpen,
  onClose,
  history,
  onRemoveItem,
  onClearAll,
  onSelectItem,
}: HistorySidebarProps) => {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Sidebar */}
      <div className="fixed right-0 top-0 h-full w-full sm:w-96 bg-gray-900/95 backdrop-blur-xl border-l border-gray-800 z-50 overflow-y-auto animate-in slide-in-from-right duration-300">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-white">Recent Analyses</h3>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              aria-label="Close history"
            >
              <X className="h-5 w-5 text-gray-400" />
            </button>
          </div>

          {/* Clear All Button */}
          {history.length > 0 && (
            <button
              onClick={onClearAll}
              className="w-full mb-4 flex items-center justify-center gap-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              <Trash2 className="h-4 w-4" />
              Clear All History
            </button>
          )}

          {/* History Items */}
          <div className="space-y-3">
            {history.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📊</div>
                <p className="text-gray-500 text-sm">No analysis history yet</p>
                <p className="text-gray-600 text-xs mt-2">
                  Your recent thumbnails will appear here
                </p>
              </div>
            ) : (
              history.map((item) => (
                <div
                  key={item.id}
                  className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50 hover:border-purple-500/50 transition-all group"
                >
                  {/* Thumbnail Image */}
                  <div
                    className="relative rounded-lg overflow-hidden mb-3 cursor-pointer"
                    onClick={() => onSelectItem?.(item)}
                  >
                    <img
                      src={item.thumbnail}
                      alt="Thumbnail history"
                      className="w-full h-32 object-cover group-hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>

                  {/* Metadata */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-gray-400 truncate">
                        {item.fileName || item.youtubeUrl || 'Unknown source'}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatTimestamp(item.timestamp)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-lg font-bold ${getScoreColor(
                          item.score
                        )}`}
                      >
                        {item.score}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onRemoveItem(item.id);
                        }}
                        className="p-1 hover:bg-red-500/20 text-gray-500 hover:text-red-400 rounded transition-colors"
                        aria-label="Remove from history"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  {/* Score Bar */}
                  <div className="w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        item.score >= 80
                          ? 'bg-green-500'
                          : item.score >= 60
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${item.score}%` }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer Info */}
          {history.length > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-800">
              <p className="text-xs text-gray-500 text-center">
                Showing {history.length} of 10 recent analyses
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
};