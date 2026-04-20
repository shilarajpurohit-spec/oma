import { useState } from "react";
import { DiffEditor } from "@monaco-editor/react";
import { MigrationResponse, MigrationIssue, api } from "../api";
import { AlertCircle, AlertTriangle, AlertOctagon, CheckCircle2, Wrench, Loader2, ChevronDown, ChevronUp } from "lucide-react";

interface MigrationResultsProps {
  result: MigrationResponse;
  fileName: string;
  onCodePatched?: (newCode: string, filename: string) => void;
}

export function MigrationResults({ result, fileName, onCodePatched }: MigrationResultsProps) {
  const [explanation, setExplanation] = useState<"collapsed" | "expanded">("collapsed");

  return (
    <div className="flex flex-col h-full bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-neutral-800 border-b border-neutral-700">
        <h2 className="text-lg font-semibold text-neutral-100 flex items-center gap-2">
          Migration Output
          <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            {result.target_version}
          </span>
        </h2>
        <div className="text-sm text-neutral-400 font-mono">
          {result.module_name}/{fileName || result.filename || "file.py"}
        </div>
      </div>

      {/* Diff Editor */}
      <div className="h-[340px] border-b border-neutral-800 shrink-0">
        <DiffEditor
          height="100%"
          original={result.original_code}
          modified={result.migrated_code}
          language="python"
          theme="vs-dark"
          options={{
            readOnly: true,
            renderSideBySide: true,
            minimap: { enabled: false },
            fontSize: 13,
            fontFamily: "'JetBrains Mono', Consolas, monospace",
            ignoreTrimWhitespace: false,
            scrollBeyondLastLine: false,
          }}
        />
      </div>

      {/* Explanation (collapsible) */}
      {result.explanation && (
        <div className="shrink-0 border-b border-neutral-800">
          <button
            id="toggle-explanation"
            onClick={() => setExplanation(e => e === "collapsed" ? "expanded" : "collapsed")}
            className="w-full flex items-center justify-between px-4 py-2 text-sm font-medium text-neutral-300 hover:bg-neutral-800/50 transition-colors"
          >
            <span className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
              AI Explanation
            </span>
            {explanation === "collapsed"
              ? <ChevronDown className="w-4 h-4 text-neutral-500" />
              : <ChevronUp className="w-4 h-4 text-neutral-500" />
            }
          </button>
          {explanation === "expanded" && (
            <div
              className="px-4 pb-4 text-sm text-neutral-300 leading-relaxed prose prose-invert max-w-none prose-sm"
              style={{ whiteSpace: "pre-wrap" }}
            >
              {result.explanation}
            </div>
          )}
        </div>
      )}

      {/* Issues List */}
      <div className="flex-1 overflow-y-auto p-4 bg-neutral-900">
        <h3 className="text-md font-medium text-neutral-200 mb-4 flex items-center gap-2">
          Detected Issues
          <span className="px-2 py-0.5 text-xs rounded-full bg-neutral-800 text-neutral-400">
            {result.issues.length}
          </span>
        </h3>

        {result.issues.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-neutral-500 border border-neutral-800 border-dashed rounded-lg">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mb-2" />
            <p>No issues detected! Code looks ready for Odoo {result.target_version}.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {result.issues.map((issue, idx) => (
              <IssueCard
                key={idx}
                issue={issue}
                currentCode={result.migrated_code}
                filename={fileName || result.filename || "file.py"}
                onPatched={onCodePatched}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface IssueCardProps {
  issue: MigrationIssue;
  currentCode: string;
  filename: string;
  onPatched?: (newCode: string, filename: string) => void;
}

function IssueCard({ issue, currentCode, filename, onPatched }: IssueCardProps) {
  const [isApplying, setIsApplying] = useState(false);
  const [fixStatus, setFixStatus] = useState<"idle" | "success" | "error">("idle");
  const [fixMessage, setFixMessage] = useState("");

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case "critical": return "border-red-500/30 bg-red-500/10 text-red-400";
      case "high": return "border-orange-500/30 bg-orange-500/10 text-orange-400";
      case "medium": return "border-yellow-500/30 bg-yellow-500/10 text-yellow-500";
      case "low": return "border-blue-500/30 bg-blue-500/10 text-blue-400";
      default: return "border-neutral-500/30 bg-neutral-500/10 text-neutral-400";
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "critical": return <AlertOctagon className="w-5 h-5" />;
      case "high": return <AlertTriangle className="w-5 h-5" />;
      default: return <AlertCircle className="w-5 h-5" />;
    }
  };

  const handleApplyFix = async () => {
    if (!issue.suggestion) return;
    setIsApplying(true);
    setFixStatus("idle");
    setFixMessage("");
    try {
      const res = await api.applyFix({
        code: currentCode,
        issue_message: issue.message,
        suggestion: issue.suggestion,
        line: issue.line,
      });
      if (res.applied) {
        setFixStatus("success");
        setFixMessage("Fix applied — code updated in editor.");
        onPatched?.(res.patched_code, filename);
      } else {
        setFixStatus("error");
        setFixMessage(res.message || "Fix could not be applied automatically.");
      }
    } catch (err: any) {
      setFixStatus("error");
      setFixMessage(err.message || "Unexpected error applying fix.");
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className={`p-4 rounded-lg border ${getSeverityStyle(issue.severity)} flex flex-col gap-2 transition-colors`}>
      <div className="flex items-start gap-3">
        <div className="mt-0.5">{getSeverityIcon(issue.severity)}</div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <span className="font-semibold uppercase text-xs tracking-wider opacity-80">
              {issue.severity} Issue
            </span>
            {issue.line && (
              <span className="font-mono text-xs opacity-70">Line {issue.line}</span>
            )}
          </div>
          <p className="text-sm opacity-90 leading-relaxed">{issue.message}</p>

          {issue.suggestion && (
            <div className="mt-3 p-3 bg-black/40 rounded border border-black/20">
              <span className="text-xs font-semibold uppercase tracking-wider mb-1 block opacity-60">Hint</span>
              <p className="text-sm opacity-80 font-mono text-xs leading-relaxed">{issue.suggestion}</p>
            </div>
          )}

          {/* Apply Fix Button */}
          {issue.suggestion && fixStatus !== "success" && (
            <button
              id={`apply-fix-btn-line-${issue.line ?? "na"}`}
              onClick={handleApplyFix}
              disabled={isApplying}
              className="mt-3 flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isApplying
                ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Applying…</>
                : <><Wrench className="w-3.5 h-3.5" /> Apply Fix</>
              }
            </button>
          )}

          {/* Fix Feedback */}
          {fixStatus !== "idle" && (
            <p className={`mt-2 text-xs font-medium ${fixStatus === "success" ? "text-emerald-400" : "text-red-400"}`}>
              {fixMessage}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
