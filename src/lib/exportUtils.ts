// src/lib/exportUtils.ts
import { AnalysisResult } from '@/types/analysis';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

/**
 * Export analysis results as JSON
 */
export const exportAsJSON = (result: AnalysisResult, previewUrl: string | null) => {
  const exportData = {
    exportDate: new Date().toISOString(),
    version: '1.0',
    thumbnailData: previewUrl,
    analysis: {
      attractivenessScore: result.attractiveness_score,
      grade: getScoreGrade(result.attractiveness_score),
      metrics: {
        averageBrightness: result.average_brightness,
        contrastLevel: result.contrast_level,
        wordCount: result.word_count,
        textContent: result.text_content,
        dominantColors: result.dominant_colors,
      },
      detectedObjects: result.detected_objects.map((obj, idx) => ({
        index: idx,
        label: obj.label,
        confidence: obj.confidence,
        boundingBox: obj.bbox_normalized,
      })),
      faceAnalysis: {
        faceCount: result.face_count,
        detectedEmotion: result.detected_emotion,
      },
      predictions: {
        ctr: {
          conservative: (result.attractiveness_score * 0.05).toFixed(2),
          expected: (result.attractiveness_score * 0.08).toFixed(2),
          optimistic: (result.attractiveness_score * 0.12).toFixed(2),
        },
      },
      aiSuggestions: result.ai_suggestions,
    },
  };

  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `thumblytics-analysis-${Date.now()}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Export dashboard as annotated image
 */
export const exportAsImage = async (
  elementId: string,
  result: AnalysisResult,
  previewUrl: string | null
) => {
  try {
    const element = document.getElementById(elementId);
    if (!element) throw new Error('Dashboard element not found');

    // Capture the entire dashboard
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
      backgroundColor: '#0f172a',
      logging: false,
    });

    // If there's a preview image with detected objects, create annotated version
    if (previewUrl && result.detected_objects.length > 0) {
      const annotatedCanvas = await createAnnotatedImage(
        previewUrl,
        result.detected_objects
      );
      
      // Combine dashboard and annotated image
      const finalCanvas = document.createElement('canvas');
      const ctx = finalCanvas.getContext('2d');
      
      if (ctx) {
        finalCanvas.width = Math.max(canvas.width, annotatedCanvas.width);
        finalCanvas.height = canvas.height + annotatedCanvas.height + 40;
        
        // Fill background
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, finalCanvas.width, finalCanvas.height);
        
        // Draw dashboard
        ctx.drawImage(canvas, 0, 0);
        
        // Draw annotated image below
        ctx.drawImage(annotatedCanvas, 0, canvas.height + 40);
        
        // Download combined image
        finalCanvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `thumblytics-complete-${Date.now()}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
          }
        });
      }
    } else {
      // Just download the dashboard
      canvas.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `thumblytics-dashboard-${Date.now()}.png`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        }
      });
    }
  } catch (error) {
    console.error('Error exporting as image:', error);
    throw error;
  }
};

/**
 * Create annotated image with bounding boxes
 */
const createAnnotatedImage = (
  imageUrl: string,
  objects: Array<{ label: string; confidence: number; bbox_normalized: number[] }>
): Promise<HTMLCanvasElement> => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        reject(new Error('Could not get canvas context'));
        return;
      }
      
      // Draw image
      ctx.drawImage(img, 0, 0);
      
      // Draw bounding boxes and labels
      objects.forEach((obj, idx) => {
        const [x, y, width, height] = obj.bbox_normalized;
        
        // Draw box
        ctx.strokeStyle = `hsl(${(idx * 137.5) % 360}, 70%, 60%)`;
        ctx.lineWidth = 3;
        ctx.strokeRect(x, y, width, height);
        
        // Draw label background
        const label = `${obj.label} (${(obj.confidence * 100).toFixed(1)}%)`;
        ctx.font = 'bold 16px Arial';
        const textWidth = ctx.measureText(label).width;
        
        ctx.fillStyle = `hsl(${(idx * 137.5) % 360}, 70%, 60%)`;
        ctx.fillRect(x, y - 25, textWidth + 10, 25);
        
        // Draw label text
        ctx.fillStyle = '#ffffff';
        ctx.fillText(label, x + 5, y - 7);
      });
      
      resolve(canvas);
    };
    
    img.onerror = () => reject(new Error('Failed to load image'));
    img.src = imageUrl;
  });
};

/**
 * Export as PDF report
 */
export const exportAsPDF = async (
  elementId: string,
  result: AnalysisResult,
  previewUrl: string | null
) => {
  try {
    const element = document.getElementById(elementId);
    if (!element) throw new Error('Dashboard element not found');

    // Create PDF
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    let yPosition = 20;

    // Title
    pdf.setFontSize(24);
    pdf.setTextColor(147, 51, 234); // Purple
    pdf.text('Thumblytics Analysis Report', pageWidth / 2, yPosition, {
      align: 'center',
    });
    yPosition += 15;

    // Date
    pdf.setFontSize(10);
    pdf.setTextColor(150, 150, 150);
    pdf.text(
      `Generated: ${new Date().toLocaleString()}`,
      pageWidth / 2,
      yPosition,
      { align: 'center' }
    );
    yPosition += 15;

    // Attractiveness Score (Large)
    pdf.setFontSize(48);
    const scoreColor = getScoreColorRGB(result.attractiveness_score);
    pdf.setTextColor(scoreColor.r, scoreColor.g, scoreColor.b);
    pdf.text(
      result.attractiveness_score.toString(),
      pageWidth / 2,
      yPosition,
      { align: 'center' }
    );
    yPosition += 10;

    pdf.setFontSize(16);
    pdf.setTextColor(200, 200, 200);
    pdf.text(
      getScoreGrade(result.attractiveness_score),
      pageWidth / 2,
      yPosition,
      { align: 'center' }
    );
    yPosition += 20;

    // Preview Image (if available)
    if (previewUrl) {
      try {
        const imgData = await loadImageAsDataURL(previewUrl);
        const imgWidth = 100;
        const imgHeight = 60;
        pdf.addImage(
          imgData,
          'PNG',
          (pageWidth - imgWidth) / 2,
          yPosition,
          imgWidth,
          imgHeight
        );
        yPosition += imgHeight + 10;
      } catch (e) {
        console.error('Could not add preview image:', e);
      }
    }

    // Check if we need a new page
    if (yPosition > pageHeight - 60) {
      pdf.addPage();
      yPosition = 20;
    }

    // Metrics Section
    pdf.setFontSize(16);
    pdf.setTextColor(147, 51, 234);
    pdf.text('Key Metrics', 20, yPosition);
    yPosition += 10;

    pdf.setFontSize(11);
    pdf.setTextColor(100, 100, 100);
    const metrics = [
      `Average Brightness: ${result.average_brightness.toFixed(1)}`,
      `Contrast Level: ${result.contrast_level.toFixed(2)}`,
      `Word Count: ${result.word_count}`,
      `Text Content: ${result.text_content || 'None detected'}`,
    ];

    metrics.forEach((metric) => {
      pdf.text(metric, 25, yPosition);
      yPosition += 7;
    });
    yPosition += 10;

    // Dominant Colors
    if (result.dominant_colors.length > 0) {
      pdf.setFontSize(14);
      pdf.setTextColor(147, 51, 234);
      pdf.text('Dominant Colors', 20, yPosition);
      yPosition += 8;

      result.dominant_colors.forEach((color) => {
        const rgb = hexToRgb(color);
        if (rgb) {
          pdf.setFillColor(rgb.r, rgb.g, rgb.b);
          pdf.rect(25, yPosition - 3, 5, 5, 'F');
          pdf.setFontSize(10);
          pdf.setTextColor(100, 100, 100);
          pdf.text(
            `${color.toUpperCase()} - RGB(${rgb.r}, ${rgb.g}, ${rgb.b})`,
            35,
            yPosition
          );
          yPosition += 7;
        }
      });
      yPosition += 10;
    }

    // Check for new page
    if (yPosition > pageHeight - 80) {
      pdf.addPage();
      yPosition = 20;
    }

    // Detected Objects
    if (result.detected_objects.length > 0) {
      pdf.setFontSize(14);
      pdf.setTextColor(147, 51, 234);
      pdf.text('Detected Objects', 20, yPosition);
      yPosition += 8;

      result.detected_objects.forEach((obj) => {
        pdf.setFontSize(10);
        pdf.setTextColor(100, 100, 100);
        pdf.text(
          `• ${obj.label} (${(obj.confidence * 100).toFixed(1)}% confidence)`,
          25,
          yPosition
        );
        yPosition += 6;
      });
      yPosition += 10;
    }

    // Face Analysis
    if (result.face_count > 0) {
      pdf.setFontSize(14);
      pdf.setTextColor(147, 51, 234);
      pdf.text('Face Analysis', 20, yPosition);
      yPosition += 8;

      pdf.setFontSize(10);
      pdf.setTextColor(100, 100, 100);
      pdf.text(`Faces Detected: ${result.face_count}`, 25, yPosition);
      yPosition += 6;
      if (result.detected_emotion) {
        pdf.text(`Dominant Emotion: ${result.detected_emotion}`, 25, yPosition);
        yPosition += 6;
      }
      yPosition += 10;
    }

    // Check for new page
    if (yPosition > pageHeight - 60) {
      pdf.addPage();
      yPosition = 20;
    }

    // CTR Predictions
    pdf.setFontSize(14);
    pdf.setTextColor(59, 130, 246); // Blue
    pdf.text('Predicted CTR Range', 20, yPosition);
    yPosition += 10;

    const ctrData = [
      {
        label: 'Conservative',
        value: (result.attractiveness_score * 0.05).toFixed(1),
      },
      {
        label: 'Expected',
        value: (result.attractiveness_score * 0.08).toFixed(1),
      },
      {
        label: 'Optimistic',
        value: (result.attractiveness_score * 0.12).toFixed(1),
      },
    ];

    ctrData.forEach((ctr) => {
      pdf.setFontSize(11);
      pdf.setTextColor(100, 100, 100);
      pdf.text(`${ctr.label}: ${ctr.value}%`, 25, yPosition);
      yPosition += 7;
    });
    yPosition += 10;

    // AI Suggestions
    if (result.ai_suggestions.length > 0) {
      // Check for new page
      if (yPosition > pageHeight - 80) {
        pdf.addPage();
        yPosition = 20;
      }

      pdf.setFontSize(14);
      pdf.setTextColor(147, 51, 234);
      pdf.text('AI Suggestions', 20, yPosition);
      yPosition += 8;

      pdf.setFontSize(10);
      pdf.setTextColor(100, 100, 100);
      result.ai_suggestions.forEach((suggestion) => {
        const lines = pdf.splitTextToSize(`• ${suggestion}`, pageWidth - 40);
        lines.forEach((line: string) => {
          if (yPosition > pageHeight - 20) {
            pdf.addPage();
            yPosition = 20;
          }
          pdf.text(line, 25, yPosition);
          yPosition += 6;
        });
        yPosition += 3;
      });
    }

    // Save PDF
    pdf.save(`thumblytics-report-${Date.now()}.pdf`);
  } catch (error) {
    console.error('Error exporting as PDF:', error);
    throw error;
  }
};

// Helper functions
const getScoreGrade = (score: number): string => {
  if (score >= 90) return '🔥 Exceptional';
  if (score >= 80) return '⭐ Excellent';
  if (score >= 70) return '✨ Great';
  if (score >= 60) return '👍 Good';
  if (score >= 50) return '👌 Average';
  return '💡 Needs Improvement';
};

const getScoreColorRGB = (score: number): { r: number; g: number; b: number } => {
  if (score >= 80) return { r: 34, g: 197, b: 94 }; // Green
  if (score >= 60) return { r: 234, g: 179, b: 8 }; // Yellow
  return { r: 239, g: 68, b: 68 }; // Red
};

const loadImageAsDataURL = (url: string): Promise<string> => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(img, 0, 0);
        resolve(canvas.toDataURL('image/png'));
      } else {
        reject(new Error('Could not get canvas context'));
      }
    };
    img.onerror = () => reject(new Error('Failed to load image'));
    img.src = url;
  });
};

const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
  // Remove # if present
  hex = hex.replace(/^#/, '');
  
  // Parse hex to RGB
  if (hex.length === 3) {
    hex = hex.split('').map(char => char + char).join('');
  }
  
  if (hex.length !== 6) {
    return null;
  }
  
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  
  return { r, g, b };
};