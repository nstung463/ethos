import { useState, useEffect } from "react";
import type { SettingsSection } from "../types";
import SettingsSubSidebar from "./SettingsSubSidebar";
import GeneralSettings from "./settings/GeneralSettings";
import AppearanceSettings from "./settings/AppearanceSettings";
import ApiKeysSettings from "./settings/ApiKeysSettings";
import ModelSettings from "./settings/ModelSettings";
import SecuritySettings from "./settings/SecuritySettings";

export default function SettingsPage({
  onClose,
  theme,
  onThemeChange,
}: {
  onClose: () => void;
  theme: "dark" | "light";
  onThemeChange: () => void;
}) {
  const [section, setSection] = useState<SettingsSection>("general");
  const [visible, setVisible] = useState(false);

  // Trigger animation on mount
  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

  const handleClose = () => {
    setVisible(false);
    setTimeout(onClose, 200); // Wait for animation to complete
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      handleClose();
    }
  };

  const renderSection = () => {
    switch (section) {
      case "general":
        return <GeneralSettings />;
      case "appearance":
        return <AppearanceSettings theme={theme} onThemeChange={onThemeChange} />;
      case "api-keys":
        return <ApiKeysSettings />;
      case "model-settings":
        return <ModelSettings />;
      case "security":
        return <SecuritySettings />;
      default:
        return <GeneralSettings />;
    }
  };

  return (
    // Layer 1: Backdrop with blur
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-sm transition-opacity duration-200 ${
        visible ? "opacity-100 bg-black/60" : "opacity-0 pointer-events-none bg-black/0"
      }`}
      onClick={handleBackdropClick}
    >
      {/* Layer 2: Modal Container */}
      <div
        className={`relative flex flex-col bg-[var(--panel-elevated)] rounded-2xl shadow-2xl border border-[var(--border-subtle)] w-full max-w-[880px] h-[520px] overflow-hidden transition-all duration-200 ${
          visible ? "opacity-100 scale-100" : "opacity-0 scale-95"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between shrink-0 px-6 py-4 border-b border-[var(--border-subtle)]">
          <h2 className="text-base font-semibold text-[var(--text-primary)]">Settings</h2>
          <button
            type="button"
            onClick={handleClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--text-soft)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] transition"
            title="Close settings"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M2 2l12 12M14 2L2 14"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>

        {/* Layer 3: Modal Body (Nested Layout) - Fixed height */}
        <div className="flex flex-1 min-h-0 overflow-hidden">
          {/* Sidebar */}
          <SettingsSubSidebar section={section} onSectionChange={setSection} />

          {/* Content Area - Scrollable */}
          <div className="flex-1 overflow-y-auto bg-[var(--panel-bg-soft)]">
            <div className="px-8 py-6">
              <div className="max-w-[500px]">{renderSection()}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
