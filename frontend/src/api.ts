export interface MigrationRequest {
  module_name: string;
  source_version: string;
  target_version: string;
  filename: string;
  file_content: string;
  incremental: boolean;
}

export interface FileItem {
  filename: string;
  content: string;
}

export interface MultiFileMigrationRequest {
  module_name: string;
  source_version: string;
  target_version: string;
  files: FileItem[];
  incremental: boolean;
}

export interface MigrationIssue {
  line?: number;
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  suggestion?: string;
}

export interface MigrationResponse {
  module_name: string;
  source_version: string;
  target_version: string;
  original_code: string;
  migrated_code: string;
  diff: string;
  issues: MigrationIssue[];
  explanation: string;
  filename?: string;
}

export interface MultiFileMigrationResult {
  filename: string;
  response: MigrationResponse;
}

export interface MultiFileMigrationResponse {
  module_name: string;
  source_version: string;
  target_version: string;
  results: MultiFileMigrationResult[];
  total_issues: number;
  skipped_files: string[];
}

export interface ChatRequest {
  message: string;
  context?: string;
}

export interface ChatResponse {
  reply: string;
  tokens_used: number;
}

export interface ReportRequest {
  response: MigrationResponse;
  format: "json" | "text";
}

export interface ApplyFixRequest {
  code: string;
  issue_message: string;
  suggestion: string;
  line?: number;
}

export interface ApplyFixResponse {
  patched_code: string;
  applied: boolean;
  message?: string;
}

const API_BASE = "http://localhost:8000/api";

export const api = {
  async migrate(request: MigrationRequest): Promise<MigrationResponse> {
    const res = await fetch(`${API_BASE}/migrate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!res.ok) throw new Error("Migration failed: " + await res.text());
    return res.json();
  },

  async migrateMulti(request: MultiFileMigrationRequest): Promise<MultiFileMigrationResponse> {
    const res = await fetch(`${API_BASE}/migrate/multi`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!res.ok) throw new Error("Multi-file migration failed: " + await res.text());
    return res.json();
  },

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!res.ok) throw new Error("Chat failed: " + await res.text());
    return res.json();
  },

  async report(request: ReportRequest): Promise<string> {
    const res = await fetch(`${API_BASE}/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!res.ok) throw new Error("Failed to generate report: " + await res.text());
    const isText = request.format === "text";
    return isText ? res.text() : JSON.stringify(await res.json(), null, 2);
  },

  async applyFix(request: ApplyFixRequest): Promise<ApplyFixResponse> {
    const res = await fetch(`${API_BASE}/apply_fix`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!res.ok) throw new Error("Failed to apply fix: " + await res.text());
    return res.json();
  },

  async detectVersion(code: string, filename: string): Promise<{ version: string }> {
    const res = await fetch(`${API_BASE}/detect-version`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, filename }),
    });
    if (!res.ok) throw new Error("Failed to detect version");
    return res.json();
  },
};
