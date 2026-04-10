import { useState } from "react";

export default function GeneralSettings() {
  const [language, setLanguage] = useState("en");
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--text-primary)] mb-6">General</h1>

        {/* Language Section */}
        <div className="space-y-4 mb-8">
          <label className="block">
            <span className="text-xs font-medium uppercase tracking-wider text-[var(--text-soft)] mb-2 block">
              Language
            </span>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full rounded-lg bg-[var(--surface-soft)] border border-[var(--border-subtle)] px-3 py-2 text-[var(--text-primary)] outline-none transition hover:border-[var(--border-strong)] focus:border-[var(--accent)]"
            >
              <option value="en">English</option>
              <option value="vi">Tiếng Việt</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="de">Deutsch</option>
              <option value="zh">中文</option>
            </select>
          </label>
        </div>

        {/* Notifications Section */}
        <div className="space-y-4">
          <label className="text-xs font-medium uppercase tracking-wider text-[var(--text-soft)] block">
            Notifications
          </label>
          <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--surface-soft)] border border-[var(--border-subtle)]">
            <span className="text-sm text-[var(--text-secondary)]">Enable notifications</span>
            <button
              type="button"
              onClick={() => setNotificationsEnabled(!notificationsEnabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                notificationsEnabled
                  ? "bg-[var(--accent)]"
                  : "bg-[var(--border-subtle)]"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-[var(--text-primary)] transition-transform ${
                  notificationsEnabled ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
