import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Lightbulb, Eye, Zap, Target } from "lucide-react";

interface AnalysisResult {
  attractivenessScore: number;
  brightness: number;
  contrast: number;
  detectedObjects: Array<{
    class: string;
    confidence: number;
    contrast: number;
  }>;
  faceCount: number;
  dominantEmotion: string;
  suggestions: string[];
}

interface AnalysisDashboardProps {
  result: AnalysisResult;
}

export function AnalysisDashboard({ result }: AnalysisDashboardProps) {
  const metricsData = [
    { name: "Brightness", value: Math.round(result.brightness * 100), color: "hsl(var(--accent))" },
    { name: "Contrast", value: Math.round(result.contrast * 100), color: "hsl(var(--secondary))" },
  ];

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-accent";
    if (score >= 60) return "text-secondary";
    return "text-destructive";
  };

  const getScoreGrade = (score: number) => {
    if (score >= 80) return "Excellent";
    if (score >= 60) return "Good";
    if (score >= 40) return "Average";
    return "Needs Improvement";
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6 animate-in fade-in duration-700">
      {/* Hero Score */}
      <Card className="bg-gradient-card p-8 border-border shadow-card">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 mb-4">
            <Target className="h-6 w-6 text-primary" />
            <h2 className="text-2xl font-bold">Attractiveness Score</h2>
          </div>
          <div className={`text-7xl font-bold ${getScoreColor(result.attractivenessScore)} mb-2`}>
            {result.attractivenessScore}
          </div>
          <p className="text-xl text-muted-foreground">{getScoreGrade(result.attractivenessScore)}</p>
        </div>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Visual Metrics Chart */}
        <Card className="bg-gradient-card p-6 border-border shadow-card">
          <div className="flex items-center gap-2 mb-6">
            <Eye className="h-5 w-5 text-accent" />
            <h3 className="text-xl font-semibold">Visual Metrics</h3>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={metricsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" />
              <YAxis stroke="hsl(var(--muted-foreground))" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "0.5rem",
                }}
              />
              <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                {metricsData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Object Detection */}
        <Card className="bg-gradient-card p-6 border-border shadow-card">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="h-5 w-5 text-secondary" />
            <h3 className="text-xl font-semibold">Detected Objects</h3>
          </div>
          <div className="space-y-3 max-h-48 overflow-y-auto">
            {result.detectedObjects.map((obj, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <Badge variant="outline" className="capitalize">
                    {obj.class}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {Math.round(obj.confidence * 100)}% confident
                  </span>
                </div>
                <span className="text-sm font-medium">
                  Contrast: {Math.round(obj.contrast * 100)}%
                </span>
              </div>
            ))}
            {result.faceCount > 0 && (
              <div className="flex items-center justify-between p-3 bg-accent/10 rounded-lg border border-accent/20">
                <div className="flex items-center gap-3">
                  <Badge className="bg-accent/20 text-accent">Face Detected</Badge>
                  <span className="text-sm text-muted-foreground capitalize">
                    {result.dominantEmotion} expression
                  </span>
                </div>
                <span className="text-sm font-medium">{result.faceCount} face(s)</span>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* AI Suggestions */}
      <Card className="bg-gradient-card p-6 border-border shadow-card">
        <div className="flex items-center gap-2 mb-4">
          <Lightbulb className="h-5 w-5 text-primary" />
          <h3 className="text-xl font-semibold">AI-Generated Suggestions</h3>
        </div>
        <div className="space-y-3">
          {result.suggestions.map((suggestion, idx) => (
            <div
              key={idx}
              className="flex gap-3 p-4 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-gradient-primary flex items-center justify-center text-sm font-bold">
                {idx + 1}
              </div>
              <p className="text-foreground leading-relaxed">{suggestion}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
