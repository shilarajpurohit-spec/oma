import Editor from "@monaco-editor/react";

interface CodeEditorProps {
  value: string;
  onChange: (value: string | undefined) => void;
  language?: string;
  readOnly?: boolean;
}

export function CodeEditor({ value, onChange, language = "python", readOnly = false }: CodeEditorProps) {
  return (
    <div className="h-full w-full rounded-md overflow-hidden border border-neutral-700 shadow-sm relative group bg-[#1e1e1e]">
      <div className="absolute top-0 right-0 z-10 px-3 py-1 text-xs font-semibold text-neutral-400 bg-neutral-800 rounded-bl-md border-b border-l border-neutral-700 shadow opacity-0 group-hover:opacity-100 transition-opacity">
        {language.toUpperCase()}
      </div>
      <Editor
        height="100%"
        defaultLanguage={language}
        theme="vs-dark"
        value={value}
        onChange={onChange}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
          lineHeight: 24,
          padding: { top: 16, bottom: 16 },
          readOnly,
          scrollBeyondLastLine: false,
          smoothScrolling: true,
          cursorBlinking: "smooth",
          cursorSmoothCaretAnimation: "on",
          formatOnPaste: false,
        }}
      />
    </div>
  );
}
