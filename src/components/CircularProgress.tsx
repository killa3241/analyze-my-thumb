// src/components/CircularProgress.tsx

interface CircularProgressProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  showLabel?: boolean;
}

export const CircularProgress = ({ 
  percentage, 
  size = 60, 
  strokeWidth = 4,
  showLabel = true 
}: CircularProgressProps) => {
  const radius = 18;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;
  
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        {/* Background circle */}
        <circle 
          cx={size / 2} 
          cy={size / 2} 
          r={radius} 
          stroke="rgba(139, 92, 246, 0.2)" 
          strokeWidth={strokeWidth} 
          fill="none" 
        />
        
        {/* Progress circle */}
        <circle 
          cx={size / 2} 
          cy={size / 2} 
          r={radius} 
          stroke="url(#gradient)" 
          strokeWidth={strokeWidth} 
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
        
        {/* Gradient definition */}
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#8B5CF6" />
            <stop offset="100%" stopColor="#EC4899" />
          </linearGradient>
        </defs>
      </svg>
      
      {/* Percentage label */}
      {showLabel && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold text-white">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
    </div>
  );
};