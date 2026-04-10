import { useState } from "react";

export default function CodeBlock({ language, value }: { language?: string; value: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="code-block my-1 overflow-hidden rounded-lg border border-[var(--border-subtle)] sm:my-2">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] bg-[var(--panel-elevated)] px-2.5 py-1.5 sm:px-4 sm:py-2">
        <span className="font-mono text-[10px] uppercase tracking-wide text-[var(--text-soft)] sm:text-xs">
          {language || "code"}
        </span>
        <button
          onClick={() => void handleCopy()}
          type="button"
          className="rounded px-2 py-0.5 text-[10px] text-[var(--text-soft)] transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] cursor-pointer sm:text-xs"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto bg-[var(--panel-code)] p-2.5 font-mono text-[11px] leading-relaxed whitespace-pre text-[var(--text-primary)] sm:p-4 sm:text-sm">
        {value}
      </pre>
    </div>
  );
}
