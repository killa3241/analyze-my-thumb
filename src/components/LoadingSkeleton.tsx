// src/components/LoadingSkeleton.tsx

export const LoadingSkeleton = () => (
  <div className="w-full max-w-6xl mx-auto space-y-6">
    {/* Hero Score Skeleton */}
    <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-8 rounded-2xl h-56 animate-pulse">
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <div className="h-8 w-48 bg-gray-700 rounded"></div>
        <div className="h-24 w-32 bg-gray-700 rounded-lg"></div>
        <div className="h-6 w-32 bg-gray-700 rounded"></div>
      </div>
    </div>

    {/* Metrics Grid Skeleton */}
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {[1, 2, 3].map((i) => (
        <div 
          key={i}
          className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-6 rounded-2xl h-48 animate-pulse"
          style={{ animationDelay: `${i * 100}ms` }}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="h-6 w-24 bg-gray-700 rounded"></div>
            <div className="h-12 w-12 bg-gray-700 rounded-full"></div>
          </div>
          <div className="h-12 w-20 bg-gray-700 rounded mb-2"></div>
          <div className="h-4 w-32 bg-gray-700 rounded"></div>
        </div>
      ))}
    </div>

    {/* Colors Skeleton */}
    <div 
      className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-6 rounded-2xl h-48 animate-pulse"
      style={{ animationDelay: '400ms' }}
    >
      <div className="h-6 w-40 bg-gray-700 rounded mb-4"></div>
      <div className="flex gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex-1">
            <div className="h-24 bg-gray-700 rounded-lg mb-2"></div>
            <div className="h-4 w-16 bg-gray-700 rounded mx-auto"></div>
          </div>
        ))}
      </div>
    </div>

    {/* Objects Grid Skeleton */}
    <div 
      className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-6 rounded-2xl animate-pulse"
      style={{ animationDelay: '500ms' }}
    >
      <div className="h-6 w-48 bg-gray-700 rounded mb-6"></div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-gray-900/50 border border-gray-700 rounded-xl p-4 h-40">
            <div className="flex items-start justify-between mb-3">
              <div className="h-10 w-10 bg-gray-700 rounded"></div>
              <div className="h-12 w-12 bg-gray-700 rounded-full"></div>
            </div>
            <div className="h-5 w-20 bg-gray-700 rounded mb-3"></div>
            <div className="space-y-2">
              <div className="h-4 w-full bg-gray-700 rounded"></div>
              <div className="h-4 w-3/4 bg-gray-700 rounded"></div>
            </div>
          </div>
        ))}
      </div>
    </div>

    {/* Suggestions Skeleton */}
    <div 
      className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 p-6 rounded-2xl animate-pulse"
      style={{ animationDelay: '600ms' }}
    >
      <div className="h-6 w-56 bg-gray-700 rounded mb-6"></div>
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-900/50 border border-gray-700 rounded-xl p-4 h-24">
            <div className="flex gap-4">
              <div className="h-8 w-8 bg-gray-700 rounded-full flex-shrink-0"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 w-20 bg-gray-700 rounded"></div>
                <div className="h-4 w-full bg-gray-700 rounded"></div>
                <div className="h-4 w-5/6 bg-gray-700 rounded"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);