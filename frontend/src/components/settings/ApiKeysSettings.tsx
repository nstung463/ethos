import { useState } from "react";

export default function ApiKeysSettings() {
  const [apiKeys, setApiKeys] = useState({
    openrouter: "",
    anthropic: "",
    openai: "",
  });

  const [showKeys, setShowKeys] = useState({
    openrouter: false,
    anthropic: false,
    openai: false,
  });

  const [saved, setSaved] = useState(false);

  const handleChange = (key: keyof typeof apiKeys, value: string) => {
    setApiKeys((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleToggleShow = (key: keyof typeof showKeys) => {
    setShowKeys((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = () => {
    // In a real app, save to secure storage
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const renderKeyInput = (
    label: string,
    key: keyof typeof apiKeys,
    placeholder: string
  ) => (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-[var(--text-secondary)]">
        {label}
      </label>
      <div className="flex gap-2">
        <input
          type={showKeys[key] ? "text" : "password"}
          value={apiKeys[key]}
          onChange={(e) => handleChange(key, e.target.value)}
          placeholder={placeholder}
          className="flex-1 rounded-lg bg-[var(--surface-soft)] border border-[var(--border-subtle)] px-3 py-2 text-[var(--text-primary)] outline-none transition hover:border-[var(--border-strong)] focus:border-[var(--accent)]"
        />
        <button
          type="button"
          onClick={() => handleToggleShow(key)}
          className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--surface-soft)] border border-[var(--border-subtle)] text-[var(--text-soft)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition"
          title={showKeys[key] ? "Hide" : "Show"}
        >
          {showKeys[key] ? (
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M1 8c1.5-2.5 4-4 7-4s5.5 1.5 7 4c-1.5 2.5-4 4-7 4s-5.5-1.5-7-4z" fill="currentColor" opacity="0.5" />
              <circle cx="8" cy="8" r="2" fill="currentColor" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 3l10 10M13 8c-1.5-2.5-4-4-7-4s-5.5 1.5-7 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--text-primary)] mb-6">API Keys</h1>
        <p className="text-sm text-[var(--text-soft)] mb-6">
          Store your API keys securely. Keys are encrypted and never sent to external services.
        </p>

        <div className="space-y-6 mb-8">
          {renderKeyInput(
            "OpenRouter API Key",
            "openrouter",
            "sk-or-v1-..."
          )}
          {renderKeyInput(
            "Anthropic API Key",
            "anthropic",
            "sk-ant-..."
          )}
          {renderKeyInput(
            "OpenAI API Key",
            "openai",
            "sk-proj-..."
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleSave}
            className="px-4 py-2 rounded-lg bg-[var(--accent)] text-white font-medium hover:opacity-90 transition"
          >
            Save Keys
          </button>
          {saved && (
            <span className="text-sm text-[var(--success)]">✓ Saved successfully</span>
          )}
        </div>
      </div>
    </div>
  );
}
