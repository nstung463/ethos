import { useState } from "react";

const MODELS = [
  { id: "openai/gpt-4o", label: "GPT-4o" },
  { id: "openai/gpt-4-turbo", label: "GPT-4 Turbo" },
  { id: "anthropic/claude-opus", label: "Claude Opus" },
  { id: "anthropic/claude-sonnet", label: "Claude Sonnet" },
  { id: "deepseek/deepseek-chat", label: "DeepSeek Chat" },
] as const;

const MODES = [
  { id: "build", label: "Build" },
  { id: "review", label: "Review" },
  { id: "explain", label: "Explain" },
] as const;

export default function ModelSettings() {
  const [defaultModel, setDefaultModel] = useState("openai/gpt-4o");
  const [defaultMode, setDefaultMode] = useState("build");

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--text-primary)] mb-6">Model Settings</h1>

        {/* Default Model Section */}
        <div className="space-y-4 mb-8">
          <label htmlFor="defaultModel" className="text-xs font-medium uppercase tracking-wider text-[var(--text-soft)] block">
            Default Model
          </label>
          <select
            id="defaultModel"
            value={defaultModel}
            onChange={(e) => setDefaultModel(e.target.value)}
            className="w-full rounded-lg bg-[var(--surface-soft)] border border-[var(--border-subtle)] px-3 py-2 text-[var(--text-primary)] outline-none transition hover:border-[var(--border-strong)] focus:border-[var(--accent)]"
            style={{ colorScheme: "inherit" }}
          >
            {MODELS.map((model) => (
              <option key={model.id} value={model.id} className="bg-[var(--panel-elevated)] text-[var(--text-primary)]">
                {model.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-[var(--text-soft)]">
            This model will be selected by default when starting new conversations.
          </p>
        </div>

        {/* Default Mode Section */}
        <div className="space-y-4">
          <label htmlFor="defaultMode" className="text-xs font-medium uppercase tracking-wider text-[var(--text-soft)] block">
            Default Mode
          </label>
          <select
            id="defaultMode"
            value={defaultMode}
            onChange={(e) => setDefaultMode(e.target.value)}
            className="w-full rounded-lg bg-[var(--surface-soft)] border border-[var(--border-subtle)] px-3 py-2 text-[var(--text-primary)] outline-none transition hover:border-[var(--border-strong)] focus:border-[var(--accent)]"
            style={{ colorScheme: "inherit" }}
          >
            {MODES.map((mode) => (
              <option key={mode.id} value={mode.id} className="bg-[var(--panel-elevated)] text-[var(--text-primary)]">
                {mode.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-[var(--text-soft)]">
            Choose how the assistant should behave by default.
          </p>
        </div>
      </div>
    </div>
  );
}
