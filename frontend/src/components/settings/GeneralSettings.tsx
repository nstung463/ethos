import { useState } from "react";
import { useTranslation } from "react-i18next";

export default function GeneralSettings() {
  const { t, i18n } = useTranslation();
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--text-primary)] mb-6">{t("settings.title", "General")}</h1>

        {/* Language Section */}
        <div className="space-y-4 mb-8">
          <label className="block">
            <span className="text-xs font-medium uppercase tracking-wider text-[var(--text-soft)] mb-2 block">
              {t("settings.language", "Language")}
            </span>
            <div className="mb-2 text-[12px] text-[var(--text-secondary)]">
              {t("settings.languageDesc", "Select your preferred language for the interface.")}
            </div>
            <select
              value={i18n.language || "en"}
              onChange={(e) => i18n.changeLanguage(e.target.value)}
              className="w-full rounded-lg bg-[var(--surface-soft)] border border-[var(--border-subtle)] px-3 py-2 text-[var(--text-primary)] outline-none transition hover:border-[var(--border-strong)] focus:border-[var(--accent)]"
              style={{ colorScheme: "inherit" }}
            >
              <option value="en" className="bg-[var(--panel-elevated)] text-[var(--text-primary)]">{t("common.english", "English")}</option>
              <option value="vi" className="bg-[var(--panel-elevated)] text-[var(--text-primary)]">{t("common.vietnamese", "Tiếng Việt")}</option>
            </select>
          </label>
        </div>

        {/* Notifications Section */}
        <div className="space-y-4">
          <label className="text-xs font-medium uppercase tracking-wider text-[var(--text-soft)] block">
            {t("settings.notificationsTitle", "Notifications")}
          </label>
          <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--surface-soft)] border border-[var(--border-subtle)]">
            <span className="text-sm text-[var(--text-secondary)]">{t("settings.enableNotifications", "Enable notifications")}</span>
            <button
              type="button"
              onClick={() => setNotificationsEnabled(!notificationsEnabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${notificationsEnabled
                  ? "bg-[var(--accent)]"
                  : "bg-[var(--border-subtle)]"
                }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-[var(--text-primary)] transition-transform ${notificationsEnabled ? "translate-x-6" : "translate-x-1"
                  }`}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
