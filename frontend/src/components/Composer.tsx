import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { ArrowUp, Cloud, HardDrive, Paperclip, PenTool, Plus, Puzzle, Square } from "lucide-react";
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
              <Plus size={14} strokeWidth={1.75} />
            </button>

            {menuOpen ? (
              <div className="absolute bottom-full left-0 z-50 mb-2 w-56 rounded-xl border border-[var(--border-strong)] bg-[var(--panel-elevated)] py-1.5 shadow-xl" style={{ boxShadow: `0 20px 45px var(--shadow-panel)` }}>
                {[
                  {
                    label: "Google Drive",
                    icon: <Cloud size={16} strokeWidth={1.8} />,
                  },
                  {
                    label: "OneDrive",
                    icon: <HardDrive size={16} strokeWidth={1.8} />,
                  },
                  {
                    label: "Figma",
                    icon: <PenTool size={16} strokeWidth={1.8} />,
                  },
                  {
                    label: "Use Skills",
                    icon: <Puzzle size={16} strokeWidth={1.8} />,
                  },
                  {
                    label: "Add from local files",
                    icon: <Paperclip size={16} strokeWidth={1.8} />,
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
              <Square size={14} fill="currentColor" strokeWidth={0} />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!canSend}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--text-primary)] text-[var(--app-bg)] transition-all hover:opacity-90 cursor-pointer disabled:cursor-not-allowed disabled:opacity-20"
              title="Send message"
            >
              <ArrowUp size={14} strokeWidth={1.9} />
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
