import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import type { ComposerMode, ModeConfig } from "../types";
import { MODES } from "../constants";

export default function Composer({
  draft,
  mode,
  modeConfig,
  isStreaming,
  activeModel,
  status,
  error,
  onChange,
  onSubmit,
  onStop,
  onModeChange,
  onSuggestion,
}: {
  draft: string;
  mode: ComposerMode;
  modeConfig: ModeConfig;
  isStreaming: boolean;
  activeModel: string;
  status: string;
  error: string;
  onChange: (value: string) => void;
  onSubmit: (e?: FormEvent) => void;
  onStop: () => void;
  onModeChange: (mode: ComposerMode) => void;
  onSuggestion: (text: string) => void;
}) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const node = textareaRef.current;
    if (!node) return;
    node.style.height = "0px";
    node.style.height = `${Math.min(node.scrollHeight, 200)}px`;
  }, [draft]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [menuOpen]);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  }

  const canSend = !!draft.trim() && !!activeModel && !isStreaming;

  return (
    <div className="border-t border-[var(--border-subtle)] bg-[var(--panel-bg-soft)]">
      <div className="flex items-center gap-1 px-4 pt-3 pb-0">
        {MODES.map((m) => (
          <button
            key={m.id}
            type="button"
            onClick={() => onModeChange(m.id)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all cursor-pointer ${
              m.id === mode
                ? "bg-[var(--surface-hover-strong)] text-[var(--text-primary)]"
                : "text-[var(--text-faint)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-muted)]"
            }`}
          >
            {m.label}
          </button>
        ))}

        <div className="flex-1" />

        <span
          className={`rounded-full px-2 py-1 text-xs ${
            error
              ? "text-[var(--danger)]"
              : isStreaming
              ? "text-[var(--success)]"
              : "text-[var(--text-faint)]"
          }`}
          style={error ? { background: "var(--danger-bg)" } : isStreaming ? { background: "var(--success-bg)" } : undefined}
        >
          {error || status}
        </span>
      </div>

      <form onSubmit={onSubmit} className="px-3 py-2 sm:px-4 sm:py-3">
        <div className="flex items-end gap-2 rounded-2xl border border-[var(--border-subtle)] bg-[var(--panel-raised)] px-3 py-2 transition-colors focus-within:border-[var(--border-strong)] sm:gap-3 sm:px-4 sm:py-3">
          <div className="relative shrink-0" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen((o) => !o)}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-soft)] text-[var(--text-faint)] transition-all hover:border-[var(--border-strong)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-secondary)] cursor-pointer"
              title="Add attachment or action"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 2v10M2 7h10" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
              </svg>
            </button>

            {menuOpen ? (
              <div className="absolute bottom-full left-0 z-50 mb-2 w-56 rounded-xl border border-[var(--border-strong)] bg-[var(--panel-elevated)] py-1.5 shadow-xl" style={{ boxShadow: `0 20px 45px var(--shadow-panel)` }}>
                {[
                  {
                    label: "Google Drive",
                    icon: (
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M5.33 2L2 6.67v6.66h4L10.33 8l-2.67-6z" fill="#4285F4" />
                        <path d="M10.67 8L8 14.33h6V8h-3.33z" fill="#EA4335" />
                        <path d="M10.67 2L8 8l2.67 6 3.33-6v-6z" fill="#FBBC04" />
                      </svg>
                    ),
                  },
                  {
                    label: "OneDrive",
                    icon: (
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M2 8C2 5.24 4.24 3 7 3c1.5 0 2.89.63 3.87 1.63C12.85 4.42 14 6.07 14 8c0 2.76-2.24 5-5 5H6c-2.21 0-4-1.79-4-4z" fill="#0078D4" />
                      </svg>
                    ),
                  },
                  {
                    label: "Figma",
                    icon: (
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <circle cx="4" cy="4" r="2.5" fill="#F24E1E" />
                        <circle cx="12" cy="4" r="2.5" fill="#A259FF" />
                        <circle cx="12" cy="12" r="2.5" fill="#1ABCFE" />
                        <circle cx="4" cy="12" r="2.5" fill="#0ACF83" />
                        <circle cx="8" cy="8" r="2.5" fill="#FF61F6" />
                      </svg>
                    ),
                  },
                  {
                    label: "Use Skills",
                    icon: (
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M3 6C2.44772 6 2 6.44772 2 7V9C2 9.55228 2.44772 10 3 10H4V6H3ZM6 2C5.44772 2 5 2.44772 5 3V13C5 13.5523 5.44772 14 6 14H8V2H6ZM10 5C9.44772 5 9 5.44772 9 6V13C9 13.5523 9.44772 14 10 14H12V5H10ZM13 8C13 7.44772 13.4477 7 14 7V11C14 11.5523 13.4477 12 13 12H12V8H13Z" fill="currentColor" />
                      </svg>
                    ),
                  },
                  {
                    label: "Add from local files",
                    icon: (
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M4 2C3.44772 2 3 2.44772 3 3V10C3 11.1046 3.89543 12 5 12H6V14C6 14.5523 6.44772 15 7 15H9C9.55228 15 10 14.5523 10 14V12H11C12.1046 12 13 11.1046 13 10V3C13 2.44772 12.5523 2 12 2H4Z" fill="currentColor" />
                        <path d="M6 4C6.55228 4 7 4.44772 7 5C7 5.55228 6.55228 6 6 6C5.44772 6 5 5.55228 5 5C5 4.44772 5.44772 4 6 4Z" fill="currentColor" />
                      </svg>
                    ),
                  },
                ].map((item) => (
                  <button
                    key={item.label}
                    type="button"
                    onClick={() => {
                      console.log(`${item.label} clicked`);
                      setMenuOpen(false);
                    }}
                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] cursor-pointer"
                  >
                    {item.icon}
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
            ) : null}
          </div>

          <textarea
            ref={textareaRef}
            value={draft}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={modeConfig.placeholder}
            rows={1}
            className="min-h-6 max-h-48 flex-1 resize-none bg-transparent leading-6 text-[var(--text-primary)] outline-none placeholder:text-[var(--text-fainter)]"
            style={{ fontSize: "var(--message-text-size)" }}
          />

          {isStreaming ? (
            <button
              type="button"
              onClick={onStop}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border text-[var(--danger)] transition-all cursor-pointer"
              style={{ background: "color-mix(in oklab, var(--danger) 12%, transparent)", borderColor: "color-mix(in oklab, var(--danger) 30%, transparent)" }}
              title="Stop generation"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                <rect x="3" y="3" width="8" height="8" rx="1.5" />
              </svg>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!canSend}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--text-primary)] text-[var(--app-bg)] transition-all hover:opacity-90 cursor-pointer disabled:cursor-not-allowed disabled:opacity-20"
              title="Send message"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 11V3M3 7l4-4 4 4" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          )}
        </div>

        <div className="mt-1.5 flex items-center justify-between px-0.5 sm:mt-2 sm:px-1">
          <div className="flex min-w-0 flex-1 gap-1.5 overflow-x-auto sm:gap-2">
            {modeConfig.suggestions.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => onSuggestion(s)}
                className="whitespace-nowrap text-[10px] text-[var(--text-faint)] transition-colors hover:text-[var(--text-muted)] cursor-pointer sm:text-xs"
              >
                {s.slice(0, 35)}...
              </button>
            ))}
          </div>
          <span className="ml-1 shrink-0 text-[10px] text-[var(--text-fainter)] sm:text-xs">{activeModel || "No model"}</span>
        </div>
      </form>
    </div>
  );
}
