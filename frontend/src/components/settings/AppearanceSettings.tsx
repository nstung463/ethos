import { useState, useEffect } from "react";

type ThemeMode = "dark" | "light" | "system";

export default function AppearanceSettings({
  theme,
  onThemeChange,
}: {
  theme: "dark" | "light";
  onThemeChange: () => void;
}) {
  const [fontSize, setFontSize] = useState(14);
  const [themeMode, setThemeMode] = useState<ThemeMode>("dark");

  useEffect(() => {
    const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const systemTheme = isDark ? "dark" : "light";

    if (theme === systemTheme) {
      setThemeMode("system");
    } else {
      setThemeMode(theme);
    }
  }, [theme]);

  const handleThemeSelect = (mode: ThemeMode) => {
    setThemeMode(mode);

    if (mode === "system") {
      const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      const systemTheme = isDark ? "dark" : "light";
      if (theme !== systemTheme) {
        onThemeChange();
      }
    } else if (mode !== theme) {
      onThemeChange();
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--text-primary)] mb-6">Appearance</h1>

        <div className="space-y-4 mb-8">
          <label className="text-xs font-medium uppercase tracking-wider text-[var(--text-soft)] block">
            Theme
          </label>
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => handleThemeSelect("light")}
              className={`flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition ${
                themeMode === "light"
                  ? "border-[var(--accent)] bg-[var(--surface-hover)]"
                  : "border-[var(--border-subtle)] bg-[var(--surface-soft)] hover:bg-[var(--surface-hover)]"
              }`}
            >
              <div className="w-20 h-12 rounded-lg bg-gradient-to-b from-white to-gray-100 border border-gray-300" />
              <span className="text-xs font-medium text-[var(--text-secondary)]">Light</span>
            </button>

            <button
              type="button"
              onClick={() => handleThemeSelect("dark")}
              className={`flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition ${
                themeMode === "dark"
                  ? "border-[var(--accent)] bg-[var(--surface-hover)]"
                  : "border-[var(--border-subtle)] bg-[var(--surface-soft)] hover:bg-[var(--surface-hover)]"
              }`}
            >
              <div className="w-20 h-12 rounded-lg bg-gradient-to-b from-gray-900 to-black border border-gray-700" />
              <span className="text-xs font-medium text-[var(--text-secondary)]">Dark</span>
            </button>

            <button
              type="button"
              onClick={() => handleThemeSelect("system")}
              className={`flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition ${
                themeMode === "system"
                  ? "border-[var(--accent)] bg-[var(--surface-hover)]"
                  : "border-[var(--border-subtle)] bg-[var(--surface-soft)] hover:bg-[var(--surface-hover)]"
              }`}
            >
              <div className="w-20 h-12 rounded-lg bg-gradient-to-r from-gray-100 to-gray-900 border border-gray-400" />
              <span className="text-xs font-medium text-[var(--text-secondary)]">System</span>
            </button>
          </div>
          <p className="text-xs text-[var(--text-soft)]">
            {themeMode === "system" && "Uses your system's theme preference."}
          </p>
        </div>

        <div className="space-y-4">
          <label htmlFor="fontSize" className="text-xs font-medium uppercase tracking-wider text-[var(--text-soft)] block">
            Font Size
          </label>
          <div className="space-y-3">
            <input
              id="fontSize"
              type="range"
              min="12"
              max="18"
              value={fontSize}
              onChange={(e) => setFontSize(parseInt(e.target.value))}
              className="w-full h-2 bg-[var(--surface-soft)] rounded-lg appearance-none cursor-pointer accent-[var(--accent)]"
            />
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-soft)]">12px</span>
              <span className="text-sm font-medium text-[var(--text-primary)]">{fontSize}px</span>
              <span className="text-xs text-[var(--text-soft)]">18px</span>
            </div>
            <div
              className="p-3 rounded-lg bg-[var(--surface-soft)] border border-[var(--border-subtle)] text-center transition"
              style={{ fontSize: `${fontSize}px` }}
            >
              Sample text at {fontSize}px
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
