import type { ModeConfig } from "../types";

export default function EmptyState({
  modeConfig,
  onSuggestion,
}: {
  modeConfig: ModeConfig;
  onSuggestion: (text: string) => void;
}) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 py-12 text-center">
      <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[var(--accent)] to-[var(--accent-2)] shadow-lg" style={{ boxShadow: "0 18px 40px var(--shadow-accent)" }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="var(--accent-contrast)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>

      <h2 className="mb-2 text-2xl font-semibold text-[var(--text-primary)]">How can I help you?</h2>
      <p className="mb-8 max-w-sm text-sm text-[var(--text-soft)]">
        {modeConfig.eyebrow} mode - {modeConfig.instruction.slice(0, 80)}...
      </p>

      <div className="grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-3">
        {modeConfig.suggestions.map((prompt) => (
          <button
            key={prompt}
            onClick={() => onSuggestion(prompt)}
            type="button"
            className="rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-soft)] px-4 py-3.5 text-left text-sm text-[var(--text-secondary)] transition-all hover:border-[var(--border-strong)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] cursor-pointer"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
