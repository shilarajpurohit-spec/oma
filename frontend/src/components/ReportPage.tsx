import { useState } from "react";
import { Download, FileJson, FileText, Loader2, CheckCircle2 } from "lucide-react";
import { MigrationResponse, api } from "../api";

interface ReportPageProps {
  result: MigrationResponse;
}

export function ReportPage({ result }: ReportPageProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [downloadedFormat, setDownloadedFormat] = useState<"json" | "text" | null>(null);

  const handleDownload = async (format: "json" | "text") => {
    setIsGenerating(true);
    setDownloadedFormat(null);
    try {
      const content = await api.report({ response: result, format });
      
      const blob = new Blob([content], { 
        type: format === "json" ? "application/json" : "text/plain" 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${result.module_name}_migration_report.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setDownloadedFormat(format);
    } catch (err) {
      console.error(err);
      alert("Failed to generate the report. See console for details.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden shadow-xl">
      <div className="flex items-center justify-between px-4 py-3 bg-neutral-800 border-b border-neutral-700">
        <h2 className="text-lg font-semibold text-neutral-100 flex items-center gap-2">
          Export Report
        </h2>
      </div>

      <div className="flex-1 p-8 flex flex-col items-center justify-center space-y-8 overflow-y-auto">
        <div className="text-center max-w-sm">
           <Download className="w-12 h-12 text-blue-400 mx-auto mb-4 opacity-80" />
           <h3 className="text-2xl font-bold text-neutral-200 mb-2">Migration Summary</h3>
           <p className="text-neutral-400 leading-relaxed">
             Download a comprehensive summary of your migration output, containing the AST analysis, identified severity issues, and your code transformations.
           </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-lg">
           <button
             onClick={() => handleDownload("json")}
             disabled={isGenerating}
             className="group relative flex flex-col items-center gap-3 p-6 bg-neutral-800 hover:bg-neutral-800/80 border border-neutral-600 hover:border-blue-500 rounded-xl transition-all outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
           >
              <FileJson className="w-8 h-8 text-blue-400 group-hover:scale-110 transition-transform" />
              <span className="font-semibold text-neutral-200">Export as JSON</span>
              <span className="text-xs text-neutral-500 font-mono tracking-wide">Machine Readable</span>
           </button>

           <button
             onClick={() => handleDownload("text")}
             disabled={isGenerating}
             className="group relative flex flex-col items-center gap-3 p-6 bg-neutral-800 hover:bg-neutral-800/80 border border-neutral-600 hover:border-emerald-500 rounded-xl transition-all outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
           >
              <FileText className="w-8 h-8 text-emerald-400 group-hover:scale-110 transition-transform" />
              <span className="font-semibold text-neutral-200">Export as Text</span>
              <span className="text-xs text-neutral-500 font-mono tracking-wide">Human Readable</span>
           </button>
        </div>

        {isGenerating && (
          <div className="flex items-center gap-2 text-blue-400 animate-pulse">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span className="font-medium">Generating Report...</span>
          </div>
        )}

        {downloadedFormat && !isGenerating && (
          <div className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-4 py-2 rounded-lg">
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-medium">Successfully generated {downloadedFormat.toUpperCase()} report!</span>
          </div>
        )}
      </div>
    </div>
  );
}
