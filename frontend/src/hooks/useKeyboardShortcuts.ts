import { useEffect } from "react";
import type { AppView, SettingsSection } from "../types";

interface KeyboardShortcutOptions {
  appView: AppView;
  isStreaming: boolean;
  onNewChat: () => void;
  onOpenSettings: (section?: SettingsSection) => void;
  onToggleSidebar: () => void;
  onStop: () => void;
  onCloseSettings: () => void;
}

/** Returns true when the event originates from a focusable text input,
 *  so we don't steal keypresses during text editing. */
function isTyping(event: KeyboardEvent): boolean {
  const target = event.target as HTMLElement;
  const tag = target.tagName.toLowerCase();
  return (
    tag === "input" ||
    tag === "textarea" ||
    tag === "select" ||
    target.isContentEditable
  );
}

export function useKeyboardShortcuts({
  appView,
  isStreaming,
  onNewChat,
  onOpenSettings,
  onToggleSidebar,
  onStop,
  onCloseSettings,
}: KeyboardShortcutOptions) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const isMod = event.metaKey || event.ctrlKey;

      // ── Escape ─────────────────────────────────────────────────────────────
      // Esc: close settings modal first; if not open, stop streaming
      if (event.key === "Escape") {
        if (appView === "settings") {
          event.preventDefault();
          onCloseSettings();
          return;
        }
        if (isStreaming) {
          event.preventDefault();
          onStop();
          return;
        }
        return;
      }

      // Everything below requires Mod key and must not be inside a text input
      if (!isMod) return;

      // ── Cmd/Ctrl + K — New chat ────────────────────────────────────────────
      if (event.key === "k" && !event.shiftKey && !isTyping(event)) {
        event.preventDefault();
        onNewChat();
        return;
      }

      // ── Cmd/Ctrl + , — Settings ────────────────────────────────────────────
      if (event.key === ",") {
        event.preventDefault();
        if (appView === "settings") {
          onCloseSettings();
        } else {
          onOpenSettings();
        }
        return;
      }

      // ── Cmd/Ctrl + Shift + L — Toggle sidebar ─────────────────────────────
      if (event.key === "L" && event.shiftKey) {
        event.preventDefault();
        onToggleSidebar();
        return;
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [appView, isStreaming, onNewChat, onOpenSettings, onToggleSidebar, onStop, onCloseSettings]);
}
