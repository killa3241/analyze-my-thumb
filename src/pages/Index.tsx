import { useState } from "react";
import { ThumbnailInput } from "@/components/ThumbnailInput";
import { AnalysisDashboard } from "@/components/AnalysisDashboard";

// Mock analysis function to simulate the backend
const mockAnalysis = async (imageUrl: string) => {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 2000));

  // Generate mock results
  return {
    attractivenessScore: Math.floor(Math.random() * 30) + 70, // 70-100
    brightness: Math.random() * 0.4 + 0.5, // 0.5-0.9
    contrast: Math.random() * 0.4 + 0.5, // 0.5-0.9
    detectedObjects: [
      { class: "person", confidence: 0.95, contrast: 0.78 },
      { class: "text", confidence: 0.89, contrast: 0.92 },
      { class: "background", confidence: 0.87, contrast: 0.45 },
    ],
    faceCount: Math.random() > 0.3 ? 1 : 0,
    dominantEmotion: ["happy", "surprised", "neutral"][Math.floor(Math.random() * 3)],
    suggestions: [
      "The thumbnail has excellent contrast with the detected text elements, making them highly readable against the background.",
      "Consider increasing the brightness slightly in the lower third of the image to better highlight secondary elements.",
      "The facial expression detected shows positive emotion which typically performs well with viewer engagement.",
      "The current color scheme creates strong visual hierarchy - maintain this approach for consistency.",
      "Text elements are well-positioned in high-contrast areas, maximizing click-through potential.",
    ],
  };
};

const Index = () => {
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleAnalyze = async (imageUrl: string) => {
    setIsAnalyzing(true);
    setAnalysisResult(null);

    try {
      const result = await mockAnalysis(imageUrl);
      setAnalysisResult(result);
    } catch (error) {
      console.error("Analysis failed:", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background py-12 px-4">
      <div className="container mx-auto max-w-7xl space-y-12">
        <ThumbnailInput onAnalyze={handleAnalyze} isAnalyzing={isAnalyzing} />
        
        {analysisResult && <AnalysisDashboard result={analysisResult} />}
      </div>
    </div>
  );
};

export default Index;
