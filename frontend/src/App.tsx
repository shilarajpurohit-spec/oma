import { useState } from "react";
import { CodeEditor } from "./components/CodeEditor";
import { MigrationResults } from "./components/MigrationResults";
import { ChatInterface } from "./components/ChatInterface";
import { ReportPage } from "./components/ReportPage";
import { FileUpload, UploadedFile } from "./components/FileUpload";
import {
  api,
  MigrationResponse,
  MultiFileMigrationResponse,
  MultiFileMigrationResult,
} from "./api";
import {
  Code2, Settings, ArrowRight, Activity, MessageSquare,
  AlertTriangle, Download, Layers, ChevronLeft, ChevronRight, Upload,
} from "lucide-react";

type ActiveTab = "results" | "chat" | "report";
type MigrateMode = "single" | "multi";

function App() {
  // ── Editor state ──────────────────────────────────────────────
  const [code, setCode] = useState<string>("# Paste your Odoo v15-18 module code here\n");
  const [fileName, setFileName] = useState("models.py");
  const [moduleName, setModuleName] = useState("my_custom_module");
  const [sourceVersion, setSourceVersion] = useState("15.0");
  const [targetVersion, setTargetVersion] = useState("19.0");
  const [isIncremental, setIsIncremental] = useState(false);

  // ── Upload state ──────────────────────────────────────────────
  const [showUpload, setShowUpload] = useState(false);
  const [migrateMode, setMigrateMode] = useState<MigrateMode>("single");

  // ── Migration state ───────────────────────────────────────────
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<MigrationResponse | null>(null);
  const [multiResult, setMultiResult] = useState<MultiFileMigrationResponse | null>(null);
  const [activeFileIdx, setActiveFileIdx] = useState(0);
  const [activeTab, setActiveTab] = useState<ActiveTab>("results");
  const [error, setError] = useState<string | null>(null);

  // ── File upload callbacks ─────────────────────────────────────
  const handleSingleFile = (file: UploadedFile) => {
    setCode(file.content);
    setFileName(file.filename);
    setMigrateMode("single");
    setShowUpload(false);
  };

  const handleMultiFiles = (files: UploadedFile[]) => {
    // Prime the editor with the first file
    setCode(files[0].content);
    setFileName(files[0].filename);
    setMigrateMode("multi");
    setShowUpload(false);
    // Store files for multi migrate
    (window as any).__oma_multi_files = files;
    detectVersionIfPossible(files[0].content, files[0].filename);
  };

  const handleCodeChange = (newCode: string | undefined) => {
    const codeStr = newCode || "";
    setCode(codeStr);
    if (codeStr.length > 50 && migrateMode === "single") {
      // Basic debounce would be better here, but we'll run on large changes
      detectVersionIfPossible(codeStr, fileName);
    }
  };

  const detectVersionIfPossible = async (fileCode: string, name: string) => {
    try {
      const res = await api.detectVersion(fileCode, name);
      if (res.version && res.version !== sourceVersion) {
        setSourceVersion(res.version);
      }
    } catch (e) {
      // ignore
    }
  };

  // ── Single-file migrate ───────────────────────────────────────
  const handleMigrate = async () => {
    setIsLoading(true);
    setError(null);
    setMultiResult(null);
    try {
      const res = await api.migrate({
        module_name: moduleName,
        source_version: sourceVersion,
        target_version: targetVersion,
        filename: fileName,
        file_content: code,
        incremental: isIncremental,
      });
      setResult(res);
      setMigrateMode("single");
      setActiveTab("results");
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setIsLoading(false);
    }
  };

  // ── Multi-file migrate ────────────────────────────────────────
  const handleMigrateMulti = async () => {
    const files: UploadedFile[] = (window as any).__oma_multi_files ?? [];
    if (!files.length) { handleMigrate(); return; }

    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.migrateMulti({
        module_name: moduleName,
        source_version: sourceVersion,
        target_version: targetVersion,
        files: files.map(f => ({ filename: f.filename, content: f.content })),
        incremental: isIncremental,
      });
      setMultiResult(res);
      setActiveFileIdx(0);
      setMigrateMode("multi");
      setActiveTab("results");
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setIsLoading(false);
    }
  };

  // ── Code patch callback (from Apply Fix) ──────────────────────
  const handleCodePatched = (newCode: string, filename: string) => {
    // Update single result
    if (result && (!filename || filename === fileName)) {
      setResult({ ...result, migrated_code: newCode });
    }
    // Update multi result
    if (multiResult) {
      const updated = multiResult.results.map(r =>
        r.filename === filename
          ? { ...r, response: { ...r.response, migrated_code: newCode } }
          : r
      );
      setMultiResult({ ...multiResult, results: updated });
    }
  };

  // ── Active multi-file result ──────────────────────────────────
  const activeMultiFile: MultiFileMigrationResult | null =
    multiResult?.results[activeFileIdx] ?? null;

  const displayResult: MigrationResponse | null =
    migrateMode === "multi" ? (activeMultiFile?.response ?? null) : result;

  const isMulti = migrateMode === "multi" && !!multiResult;

  return (
    <div className="flex flex-col h-screen bg-black text-neutral-100 font-sans overflow-hidden">
      {/* Navbar */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-neutral-800 bg-neutral-900/50 backdrop-blur-md z-10 shrink-0">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-tr from-blue-500 to-indigo-500 p-1.5 rounded-lg">
            <Code2 className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400 tracking-tight">
            OMA Agent
          </h1>
          <span className="text-sm font-medium text-neutral-500 ml-2 hidden sm:inline-block border-l border-neutral-700 pl-4 py-1">
            Odoo Migration AI Agent
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-neutral-500">
          {isMulti && multiResult && (
            <span className="px-2 py-1 bg-indigo-500/10 border border-indigo-500/20 rounded-full text-indigo-400 font-medium">
              {multiResult.results.length} files · {multiResult.total_issues} issues
            </span>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex flex-1 overflow-hidden">
        {/* Left Pane - Editor & Config */}
        <section className="flex flex-col w-1/2 min-w-[40%] border-r border-neutral-800 bg-neutral-900 shadow-xl z-0">
          {/* Config Bar */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800 shrink-0 gap-3">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <input
                type="text"
                id="module-name-input"
                value={moduleName}
                onChange={e => setModuleName(e.target.value)}
                placeholder="Module Name"
                className="bg-neutral-800 border border-neutral-700 rounded px-2 py-1.5 text-sm flex-1 min-w-0 placeholder:text-neutral-600 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-all"
              />
              <span className="text-neutral-600">/</span>
              <input
                type="text"
                id="file-name-input"
                value={fileName}
                onChange={e => setFileName(e.target.value)}
                placeholder="filename.py"
                className="bg-neutral-800 border border-neutral-700 rounded px-2 py-1.5 text-sm flex-1 min-w-0 placeholder:text-neutral-600 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-all"
              />
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <label className="text-sm text-neutral-400 flex items-center gap-1">
                <Settings className="w-4 h-4 opacity-70" />
              </label>
              <select
                id="source-version-select"
                value={sourceVersion}
                onChange={e => setSourceVersion(e.target.value)}
                className="bg-neutral-800 border border-neutral-700 rounded px-2 py-1.5 text-sm text-neutral-200 outline-none focus:ring-1 focus:ring-blue-500 transition-shadow appearance-none min-w-[70px]"
              >
                <option value="15.0">v15.0</option>
                <option value="16.0">v16.0</option>
                <option value="17.0">v17.0</option>
                <option value="18.0">v18.0</option>
                <option value="19.0">v19.0</option>
              </select>
              <span className="text-neutral-500">→</span>
              <select
                id="target-version-select"
                value={targetVersion}
                onChange={e => setTargetVersion(e.target.value)}
                className="bg-neutral-800 border border-neutral-700 rounded px-2 py-1.5 text-sm text-neutral-200 outline-none focus:ring-1 focus:ring-blue-500 transition-shadow appearance-none min-w-[70px]"
              >
                {["16.0", "17.0", "18.0", "19.0"]
                  .filter(v => parseFloat(v) > parseFloat(sourceVersion))
                  .map(v => (
                    <option key={v} value={v}>v{v}</option>
                  ))}
              </select>
              <label className="flex items-center gap-1.5 text-xs text-neutral-400 ml-1 cursor-pointer" title="Step-by-step migration through intermediate versions">
                <input 
                  type="checkbox" 
                  checked={isIncremental}
                  onChange={e => setIsIncremental(e.target.checked)}
                  className="rounded border-neutral-700 bg-neutral-800 text-blue-500 focus:ring-blue-500 focus:ring-offset-neutral-900"
                />
                <span className="hidden xl:inline">Incremental</span>
              </label>
              {/* Upload toggle */}
              <button
                id="toggle-upload-btn"
                onClick={() => setShowUpload(v => !v)}
                title="Upload files"
                className={`p-1.5 rounded-md border transition-all ${showUpload
                  ? "border-blue-500/50 bg-blue-500/10 text-blue-400"
                  : "border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-200"
                  }`}
              >
                <Upload className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* File Upload Drawer */}
          {showUpload && (
            <div className="px-4 pt-3 pb-2 border-b border-neutral-800 bg-neutral-900/50 shrink-0">
              <FileUpload
                onSingleFile={handleSingleFile}
                onFilesLoaded={handleMultiFiles}
              />
            </div>
          )}

          {/* Multi-file tab pills */}
          {isMulti && multiResult.results.length > 0 && (
            <div className="flex items-center gap-1 px-4 py-2 border-b border-neutral-800 overflow-x-auto bg-neutral-900/80 shrink-0">
              <Layers className="w-3.5 h-3.5 text-neutral-500 mr-1 shrink-0" />
              {multiResult.results.map((r, i) => (
                <button
                  key={i}
                  id={`file-tab-${i}`}
                  onClick={() => {
                    setActiveFileIdx(i);
                    setCode(r.response.migrated_code);
                    setFileName(r.filename);
                  }}
                  className={`px-2 py-1 rounded text-xs font-mono whitespace-nowrap transition-colors ${i === activeFileIdx
                    ? "bg-indigo-600/30 text-indigo-300 border border-indigo-500/30"
                    : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800"
                    }`}
                >
                  {r.filename}
                  {r.response.issues.length > 0 && (
                    <span className="ml-1.5 text-orange-400">{r.response.issues.length}</span>
                  )}
                </button>
              ))}
            </div>
          )}

          {/* Editor */}
          <div className="flex-1 min-h-0 relative">
            <CodeEditor value={code} onChange={handleCodeChange} />

            {/* Migrate Button */}
            <div className="absolute bottom-6 right-6 z-20 flex items-center gap-2">
              {migrateMode === "multi" && (window as any).__oma_multi_files?.length > 0 && (
                <button
                  id="migrate-multi-btn"
                  onClick={handleMigrateMulti}
                  disabled={isLoading}
                  className="group flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-medium px-4 py-2.5 rounded-full shadow-lg hover:shadow-purple-500/25 transition-all outline-none disabled:opacity-70 disabled:cursor-not-allowed text-sm"
                >
                  {isLoading ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /><span>Migrating…</span></> : <><Layers className="w-4 h-4" /><span>Migrate All</span></>}
                </button>
              )}
              <button
                id="migrate-btn"
                onClick={handleMigrate}
                disabled={isLoading}
                className="group flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium px-5 py-2.5 rounded-full shadow-lg hover:shadow-indigo-500/25 transition-all outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-neutral-900 disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <><div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /><span>Migrating…</span></>
                ) : (
                  <><span>Migrate Code</span><ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" /></>
                )}
              </button>
            </div>
          </div>
        </section>

        {/* Right Pane - Results & Chat */}
        <section className="flex flex-col flex-1 bg-black overflow-hidden relative">
          {/* Tab Bar */}
          <div className="flex items-center gap-1 p-2 bg-neutral-900 border-b border-neutral-800 shrink-0">
            <button
              id="tab-results"
              onClick={() => setActiveTab("results")}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === "results" ? "bg-neutral-800 text-white shadow-sm" : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/50"}`}
            >
              <Activity className="w-4 h-4" />
              Migration Results {displayResult && <span className="ml-1 w-2 h-2 rounded-full bg-blue-500 animate-pulse inline-block" />}
            </button>
            <button
              id="tab-chat"
              onClick={() => setActiveTab("chat")}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === "chat" ? "bg-neutral-800 text-white shadow-sm" : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/50"}`}
            >
              <MessageSquare className="w-4 h-4" />
              Expert Assistant
            </button>
            <button
              id="tab-report"
              onClick={() => setActiveTab("report")}
              disabled={!displayResult}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === "report" ? "bg-neutral-800 text-white shadow-sm" : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/50"} disabled:opacity-40 disabled:cursor-not-allowed`}
            >
              <Download className="w-4 h-4" />
              Export Report
            </button>

            {/* Multi-file navigation */}
            {isMulti && multiResult.results.length > 1 && (
              <div className="ml-auto flex items-center gap-1">
                <button
                  id="prev-file-btn"
                  onClick={() => setActiveFileIdx(i => Math.max(0, i - 1))}
                  disabled={activeFileIdx === 0}
                  className="p-1 text-neutral-400 hover:text-neutral-200 disabled:opacity-30 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-xs text-neutral-500">
                  {activeFileIdx + 1} / {multiResult.results.length}
                </span>
                <button
                  id="next-file-btn"
                  onClick={() => setActiveFileIdx(i => Math.min(multiResult.results.length - 1, i + 1))}
                  disabled={activeFileIdx === multiResult.results.length - 1}
                  className="p-1 text-neutral-400 hover:text-neutral-200 disabled:opacity-30 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          <div className="flex-1 overflow-hidden p-4 relative">
            {/* Error Banner */}
            {error && (
              <div className="absolute top-4 left-4 right-4 z-50 bg-red-500/10 border border-red-500/30 text-red-500 px-4 py-3 rounded-lg flex items-start gap-3 backdrop-blur-md">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <p className="text-sm font-medium">{error}</p>
                <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-300">×</button>
              </div>
            )}

            {activeTab === "results" ? (
              displayResult ? (
                <MigrationResults
                  result={displayResult}
                  fileName={isMulti ? (activeMultiFile?.filename ?? "") : fileName}
                  onCodePatched={handleCodePatched}
                />
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-neutral-600 space-y-4">
                  <div className="w-16 h-16 rounded-2xl bg-neutral-900 border border-neutral-800 flex items-center justify-center">
                    <Code2 className="w-8 h-8 opacity-50" />
                  </div>
                  <p className="text-sm font-medium tracking-wide">Paste code or upload files, then press Migrate.</p>
                </div>
              )
            ) : activeTab === "report" && displayResult ? (
              <ReportPage result={displayResult} />
            ) : (
              <ChatInterface context={{ moduleName, fileName, sourceVersion, code, result: displayResult }} />
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
