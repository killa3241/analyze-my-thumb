import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Upload, Link as LinkIcon, Loader2 } from "lucide-react";
import { toast } from "sonner";

interface ThumbnailInputProps {
  onAnalyze: (imageUrl: string) => void;
  isAnalyzing: boolean;
}

export function ThumbnailInput({ onAnalyze, isAnalyzing }: ThumbnailInputProps) {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const extractYoutubeThumbnail = (url: string): string | null => {
    const videoIdMatch = url.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/);
    if (videoIdMatch && videoIdMatch[1]) {
      return `https://img.youtube.com/vi/${videoIdMatch[1]}/maxresdefault.jpg`;
    }
    return null;
  };

  const handleYoutubeAnalyze = () => {
    const thumbnailUrl = extractYoutubeThumbnail(youtubeUrl);
    if (thumbnailUrl) {
      setPreviewUrl(thumbnailUrl);
      onAnalyze(thumbnailUrl);
    } else {
      toast.error("Invalid YouTube URL. Please enter a valid video URL.");
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith("image/")) {
        toast.error("Please upload an image file");
        return;
      }
      setUploadedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        const url = reader.result as string;
        setPreviewUrl(url);
        onAnalyze(url);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="bg-gradient-card p-8 rounded-2xl shadow-card border border-border">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-primary bg-clip-text text-transparent mb-3">
            Thumblytics
          </h1>
          <p className="text-muted-foreground text-lg">
            AI-Powered YouTube Thumbnail Analyzer
          </p>
        </div>

        <Tabs defaultValue="url" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="url" className="gap-2">
              <LinkIcon className="h-4 w-4" />
              YouTube URL
            </TabsTrigger>
            <TabsTrigger value="upload" className="gap-2">
              <Upload className="h-4 w-4" />
              Upload Image
            </TabsTrigger>
          </TabsList>

          <TabsContent value="url" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="youtube-url">YouTube Video URL</Label>
              <Input
                id="youtube-url"
                placeholder="https://youtube.com/watch?v=..."
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                className="bg-background/50"
              />
            </div>
            <Button
              onClick={handleYoutubeAnalyze}
              disabled={isAnalyzing || !youtubeUrl}
              className="w-full bg-gradient-primary hover:opacity-90 transition-opacity"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                "Analyze Thumbnail"
              )}
            </Button>
          </TabsContent>

          <TabsContent value="upload" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="file-upload">Upload Thumbnail Image</Label>
              <div className="relative">
                <Input
                  id="file-upload"
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  disabled={isAnalyzing}
                  className="bg-background/50"
                />
              </div>
            </div>
            {uploadedFile && (
              <p className="text-sm text-muted-foreground">
                Selected: {uploadedFile.name}
              </p>
            )}
          </TabsContent>
        </Tabs>

        {previewUrl && (
          <div className="mt-6">
            <Label className="mb-2 block">Thumbnail Preview</Label>
            <div className="relative rounded-lg overflow-hidden border border-border shadow-glow">
              <img
                src={previewUrl}
                alt="Thumbnail preview"
                className="w-full h-auto"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
