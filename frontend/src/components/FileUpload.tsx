import { useCallback, useRef, useState } from "react";
import { UploadCloud, FileCode2, X, FolderOpen, AlertCircle } from "lucide-react";

export interface UploadedFile {
  filename: string;
  content: string;
  size: number;
}

interface FileUploadProps {
  onFilesLoaded: (files: UploadedFile[]) => void;
  onSingleFile: (file: UploadedFile) => void;
}

const ACCEPTED_EXTS = [".py", ".xml", ".js", ".ts", ".csv", ".json"];
const MAX_FILE_SIZE_MB = 2;

function getExt(name: string): string {
  return name.slice(name.lastIndexOf(".")).toLowerCase();
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileUpload({ onFilesLoaded, onSingleFile }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const processFiles = useCallback(async (rawFiles: FileList | File[]) => {
    setError(null);
    const arr = Array.from(rawFiles);
    const valid: UploadedFile[] = [];
    const errs: string[] = [];

    for (const f of arr) {
      const ext = getExt(f.name);
      if (!ACCEPTED_EXTS.includes(ext)) {
        errs.push(`${f.name}: unsupported type`);
        continue;
      }
      if (f.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
        errs.push(`${f.name}: exceeds ${MAX_FILE_SIZE_MB}MB limit`);
        continue;
      }
      const content = await f.text();
      valid.push({ filename: f.name, content, size: f.size });
    }

    if (errs.length) setError(errs.join(" · "));
    if (!valid.length) return;

    setFiles(valid);
    if (valid.length === 1) {
      onSingleFile(valid[0]);
    } else {
      onFilesLoaded(valid);
    }
  }, [onFilesLoaded, onSingleFile]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    processFiles(e.dataTransfer.files);
  }, [processFiles]);

  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const onDragLeave = () => setIsDragging(false);

  const removeFile = (idx: number) => {
    const updated = files.filter((_, i) => i !== idx);
    setFiles(updated);
    if (updated.length === 0) return;
    if (updated.length === 1) onSingleFile(updated[0]);
    else onFilesLoaded(updated);
  };

  const fileIcon = (name: string) => {
    const ext = getExt(name);
    const colors: Record<string, string> = {
      ".py": "text-blue-400", ".xml": "text-orange-400",
      ".js": "text-yellow-400", ".ts": "text-sky-400",
      ".csv": "text-green-400", ".json": "text-purple-400",
    };
    return <FileCode2 className={`w-4 h-4 ${colors[ext] ?? "text-neutral-400"}`} />;
  };

  return (
    <div className="flex flex-col gap-2">
      {/* Drop Zone */}
      <div
        id="file-upload-zone"
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => inputRef.current?.click()}
        className={`
          relative flex flex-col items-center justify-center gap-2 cursor-pointer
          border-2 border-dashed rounded-lg p-5 transition-all duration-200
          ${isDragging
            ? "border-blue-500 bg-blue-500/10 scale-[1.01]"
            : "border-neutral-700 bg-neutral-800/40 hover:border-neutral-500 hover:bg-neutral-800/70"
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          id="file-upload-input"
          multiple
          accept={ACCEPTED_EXTS.join(",")}
          className="hidden"
          onChange={e => e.target.files && processFiles(e.target.files)}
        />
        <UploadCloud className={`w-8 h-8 transition-colors ${isDragging ? "text-blue-400" : "text-neutral-500"}`} />
        <div className="text-center">
          <p className="text-sm font-medium text-neutral-300">
            Drop files or{" "}
            <span className="text-blue-400 hover:text-blue-300 underline underline-offset-2">browse</span>
          </p>
          <p className="text-xs text-neutral-500 mt-0.5">
            {ACCEPTED_EXTS.join(", ")} · max {MAX_FILE_SIZE_MB}MB each
          </p>
        </div>
        <button
          type="button"
          onClick={e => { e.stopPropagation(); inputRef.current?.click(); }}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-neutral-700 hover:bg-neutral-600 text-neutral-200 text-xs font-medium rounded-md transition-colors mt-1"
        >
          <FolderOpen className="w-3.5 h-3.5" />
          Choose Files
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-md px-3 py-2">
          <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loaded File List */}
      {files.length > 0 && (
        <ul className="space-y-1 max-h-40 overflow-y-auto pr-1">
          {files.map((f, i) => (
            <li
              key={i}
              className="flex items-center gap-2 bg-neutral-800 border border-neutral-700 rounded-md px-3 py-1.5 text-xs group"
            >
              {fileIcon(f.filename)}
              <span className="flex-1 truncate font-mono text-neutral-300">{f.filename}</span>
              <span className="text-neutral-500 shrink-0">{formatSize(f.size)}</span>
              <button
                id={`remove-file-${i}`}
                onClick={() => removeFile(i)}
                className="opacity-0 group-hover:opacity-100 text-neutral-500 hover:text-red-400 transition-opacity ml-1"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
