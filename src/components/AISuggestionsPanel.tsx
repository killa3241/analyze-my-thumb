// src/components/AISuggestionsPanel.tsx

import { useState } from 'react';
import { Lightbulb, ChevronRight, Sparkles } from 'lucide-react';
import { getPriorityBadge } from '@/lib/utils';

interface AISuggestionsPanelProps {
  suggestions: string[];
}

export const AISuggestionsPanel = ({ suggestions }: AISuggestionsPanelProps) => {
  const [expandedSuggestion, setExpandedSuggestion] = useState<number | null>(null);

  const toggleExpand = (index: number) => {
    setExpandedSuggestion(expandedSuggestion === index ? null : index);
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-6 rounded-2xl shadow-xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-yellow-500/10 rounded-lg">
          <Lightbulb className="h-5 w-5 text-yellow-400" />
        </div>
        <h3 className="text-xl font-semibold text-white">AI-Generated Suggestions</h3>
        <span className="text-sm text-gray-500">({suggestions.length} tips)</span>
      </div>

      {suggestions.length === 0 ? (
        <div className="text-center py-12">
          <Sparkles className="h-16 w-16 mx-auto text-gray-600 mb-4" />
          <p className="text-gray-400 font-medium mb-2">No suggestions available</p>
          <p className="text-sm text-gray-600">
            Your thumbnail is already optimized!
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {suggestions.map((suggestion, idx) => {
            const priority = getPriorityBadge(suggestion);
            const isExpanded = expandedSuggestion === idx;

            return (
              <div
                key={idx}
                className="bg-gray-900/50 border border-gray-700 rounded-xl overflow-hidden hover:border-purple-500/50 transition-all"
              >
                {/* Main Content */}
                <div
                  onClick={() => toggleExpand(idx)}
                  className="flex items-start gap-4 p-4 cursor-pointer hover:bg-gray-800/30 transition-colors"
                >
                  {/* Priority Emoji */}
                  <div className="flex-shrink-0 text-2xl mt-1">
                    {priority.emoji}
                  </div>

                  {/* Suggestion Text */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className={`text-xs px-2 py-1 rounded-full border font-medium ${priority.color}`}
                      >
                        {priority.label}
                      </span>
                      {idx === 0 && (
                        <span className="text-xs px-2 py-1 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30">
                          Top Priority
                        </span>
                      )}
                    </div>
                    <p className="text-gray-300 leading-relaxed text-sm">
                      {suggestion}
                    </p>
                  </div>

                  {/* Expand Arrow */}
                  <ChevronRight
                    className={`h-5 w-5 text-gray-500 flex-shrink-0 transition-transform duration-200 ${
                      isExpanded ? 'rotate-90' : ''
                    }`}
                  />
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-gray-700/50 animate-in fade-in slide-in-from-top-2 duration-200">
                    <div className="mt-4 bg-purple-900/20 border border-purple-500/30 rounded-lg p-4">
                      <p className="text-sm font-semibold text-purple-400 mb-2 flex items-center gap-2">
                        <Lightbulb className="h-4 w-4" />
                        Why this matters:
                      </p>
                      <p className="text-sm text-gray-400 leading-relaxed">
                        {priority.explanation}
                      </p>

                      {/* Action Button */}
                      <button className="mt-4 w-full sm:w-auto text-sm bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2">
                        <Sparkles className="h-4 w-4" />
                        Quick Fix Preview
                      </button>
                    </div>

                    {/* Implementation Tips */}
                    <div className="mt-3 p-3 bg-gray-800/50 rounded-lg">
                      <p className="text-xs font-semibold text-gray-400 mb-2">
                        💡 Implementation Tips:
                      </p>
                      <ul className="text-xs text-gray-500 space-y-1">
                        {priority.label === 'Critical' && (
                          <>
                            <li>• Address this issue immediately</li>
                            <li>• Test multiple variations</li>
                            <li>• Monitor CTR changes after implementation</li>
                          </>
                        )}
                        {priority.label === 'Important' && (
                          <>
                            <li>• Implement within the next revision</li>
                            <li>• A/B test against current version</li>
                            <li>• Consider audience preferences</li>
                          </>
                        )}
                        {priority.label === 'Enhancement' && (
                          <>
                            <li>• Optional but recommended</li>
                            <li>• Apply to future thumbnails</li>
                            <li>• Experiment with different approaches</li>
                          </>
                        )}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Summary Footer */}
      {suggestions.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-700/50">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">
              {suggestions.filter(s => getPriorityBadge(s).label === 'Critical').length} Critical •{' '}
              {suggestions.filter(s => getPriorityBadge(s).label === 'Important').length} Important •{' '}
              {suggestions.filter(s => getPriorityBadge(s).label === 'Enhancement').length} Enhancements
            </span>
            <button className="text-purple-400 hover:text-purple-300 transition-colors font-medium">
              Export All →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};