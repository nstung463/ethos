import { useState } from "react";

export default function SecuritySettings() {
  const [showConfirmClear, setShowConfirmClear] = useState(false);
  const [showConfirmReset, setShowConfirmReset] = useState(false);

  const handleClearData = () => {
    if (window.confirm("Are you sure you want to clear all data? This action cannot be undone.")) {
      // Clear all data
      localStorage.clear();
      setShowConfirmClear(false);
      alert("All data cleared.");
    }
  };

  const handleResetSettings = () => {
    if (window.confirm("Are you sure you want to reset all settings to defaults?")) {
      // Reset settings
      setShowConfirmReset(false);
      alert("Settings reset to defaults.");
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--text-primary)] mb-6">Security</h1>

        {/* Session Info */}
        <div className="mb-8 space-y-4">
          <label className="text-xs font-medium uppercase tracking-wider text-[var(--text-soft)] block">
            Session
          </label>
          <div className="p-4 rounded-lg bg-[var(--surface-soft)] border border-[var(--border-subtle)]">
            <p className="text-sm text-[var(--text-secondary)] mb-3">
              You are currently logged in with API access.
            </p>
            <button
              type="button"
              className="px-4 py-2 rounded-lg bg-[var(--accent)] text-white font-medium hover:opacity-90 transition"
            >
              Refresh Session
            </button>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="space-y-4">
          <label className="text-xs font-medium uppercase tracking-wider text-[var(--danger)] block">
            Danger Zone
          </label>

          {/* Clear Data */}
          <div className="p-4 rounded-lg bg-[var(--danger-bg)] border border-[var(--danger-border)]">
            <h3 className="text-sm font-medium text-[var(--text-primary)] mb-2">
              Clear All Data
            </h3>
            <p className="text-xs text-[var(--text-soft)] mb-4">
              Delete all conversations, settings, and cached data. This action cannot be undone.
            </p>
            <button
              type="button"
              onClick={() => setShowConfirmClear(!showConfirmClear)}
              className="px-3 py-2 text-sm font-medium text-[var(--danger)] border border-[var(--danger)]/30 rounded-lg hover:bg-[var(--danger)]/10 transition"
            >
              Clear Data
            </button>
            {showConfirmClear && (
              <div className="mt-3 p-3 rounded-lg bg-[var(--danger-bg)] border border-[var(--danger-border)] space-y-2">
                <p className="text-xs text-[var(--danger)]">
                  ⚠️ This will permanently delete all your data. Continue?
                </p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleClearData}
                    className="px-3 py-1.5 text-xs font-medium text-white bg-[var(--danger)] rounded-lg hover:opacity-90 transition"
                  >
                    Yes, Clear Everything
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowConfirmClear(false)}
                    className="px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] bg-[var(--surface-soft)] rounded-lg hover:bg-[var(--surface-hover)] transition"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Reset Settings */}
          <div className="p-4 rounded-lg bg-[var(--danger-bg)] border border-[var(--danger-border)]">
            <h3 className="text-sm font-medium text-[var(--text-primary)] mb-2">
              Reset Settings
            </h3>
            <p className="text-xs text-[var(--text-soft)] mb-4">
              Reset all preferences to their default values. Your data will not be affected.
            </p>
            <button
              type="button"
              onClick={() => setShowConfirmReset(!showConfirmReset)}
              className="px-3 py-2 text-sm font-medium text-[var(--danger)] border border-[var(--danger)]/30 rounded-lg hover:bg-[var(--danger)]/10 transition"
            >
              Reset Settings
            </button>
            {showConfirmReset && (
              <div className="mt-3 p-3 rounded-lg bg-[var(--danger-bg)] border border-[var(--danger-border)] space-y-2">
                <p className="text-xs text-[var(--danger)]">
                  ⚠️ This will reset all settings to defaults. Continue?
                </p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleResetSettings}
                    className="px-3 py-1.5 text-xs font-medium text-white bg-[var(--danger)] rounded-lg hover:opacity-90 transition"
                  >
                    Yes, Reset Settings
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowConfirmReset(false)}
                    className="px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] bg-[var(--surface-soft)] rounded-lg hover:bg-[var(--surface-hover)] transition"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
