import { ChevronDown, Ellipsis, FolderOpen, Moon, Share2, SunMedium, UsersRound } from "lucide-react";
import type { ChatThread, ProviderProfile } from "../types";
import { getModeConfig } from "../constants";

export default function Header({
  thread,
  profiles,
  activeProfileId,
  onProfileChange,
  backendMode,
  localRootDir,
  onBackendModeChange,
  onImportLocalProject,
  theme,
  onToggleTheme,
  showConversationActions,
}: {
  thread: ChatThread | null;
  profiles: ProviderProfile[];
  activeProfileId: string;
  onProfileChange: (profileId: string) => void;
  backendMode: "sandbox" | "local";
  localRootDir: string;
  onBackendModeChange: (mode: "sandbox" | "local") => void;
  onImportLocalProject: () => void;
  theme: "dark" | "light";
  onToggleTheme: () => void;
  showConversationActions: boolean;
}) {
  const mode = thread?.mode ?? "build";
  const modeConfig = getModeConfig(mode);

  return (
    <div className="flex shrink-0 items-center justify-between gap-2 border-b border-[var(--border-subtle)] bg-[var(--app-bg)] px-3 py-2.5 sm:px-4 sm:py-3">
      <div className="flex min-w-0 items-center gap-2 sm:gap-3">
        <h1 className="truncate text-[clamp(0.85rem,1.8vw,1rem)] font-medium text-[var(--text-primary)]">
          {thread?.title || "New conversation"}
        </h1>
        <span className="shrink-0 whitespace-nowrap rounded-full border border-[var(--border-subtle)] bg-[var(--surface-badge)] px-1.5 py-0.5 text-[9px] text-[var(--text-soft)] sm:px-2 sm:text-xs">
          {modeConfig.label}
        </span>
      </div>

      <div className="flex shrink-0 items-center gap-1 sm:gap-2">
        {showConversationActions ? (
          <>
            <button
              type="button"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-soft)] text-[var(--text-soft)] transition-all hover:border-[var(--border-strong)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] cursor-pointer"
              title="Share conversation"
              aria-label="Share conversation"
            >
              <Share2 size={15} strokeWidth={1.8} />
            </button>
            <button
              type="button"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-soft)] text-[var(--text-soft)] transition-all hover:border-[var(--border-strong)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] cursor-pointer"
              title="Conversation members"
              aria-label="Conversation members"
            >
              <UsersRound size={15} strokeWidth={1.8} />
            </button>
            <button
              type="button"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-soft)] text-[var(--text-soft)] transition-all hover:border-[var(--border-strong)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] cursor-pointer"
              title="More options"
              aria-label="More options"
            >
              <Ellipsis size={15} strokeWidth={1.8} />
            </button>
          </>
        ) : null}

        <button
          type="button"
          onClick={onToggleTheme}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-soft)] text-[var(--text-soft)] transition-all hover:border-[var(--border-strong)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] cursor-pointer"
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? (
            <SunMedium size={15} strokeWidth={1.8} />
          ) : (
            <Moon size={15} strokeWidth={1.8} />
          )}
        </button>

        {profiles.length > 0 ? (
          <div className="relative min-w-[100px] sm:min-w-[140px]">
            <select
              value={activeProfileId}
              onChange={(e) => onProfileChange(e.target.value)}
              className="w-full appearance-none rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-soft)] py-1 pl-2.5 pr-6 text-[10px] text-[var(--text-secondary)] outline-none transition-all hover:border-[var(--border-strong)] hover:text-[var(--text-primary)] cursor-pointer sm:py-1.5 sm:pl-3 sm:text-xs"
              style={{ colorScheme: "inherit" }}
            >
              {profiles.map((p) => (
                <option key={p.id} value={p.id} className="bg-[var(--panel-elevated)] text-[var(--text-primary)]">
                  {p.name || p.model}
                </option>
              ))}
            </select>
            <ChevronDown size={10} strokeWidth={1.8} className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-faint)]" />
          </div>
        ) : (
          <span className="text-xs text-[var(--text-faint)]">No profiles</span>
        )}

        <div className="flex items-center rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-soft)] p-0.5" title="Execution backend">
          <button
            type="button"
            onClick={() => onBackendModeChange("sandbox")}
            className={`rounded-md px-2.5 py-1 text-[10px] transition-all sm:text-xs cursor-pointer ${
              backendMode === "sandbox"
                ? "bg-[var(--surface-hover)] font-medium text-[var(--text-primary)]"
                : "text-[var(--text-faint)] hover:text-[var(--text-secondary)]"
            }`}
          >
            Sandbox
          </button>
          <button
            type="button"
            onClick={() => onBackendModeChange("local")}
            className={`rounded-md px-2.5 py-1 text-[10px] transition-all sm:text-xs cursor-pointer ${
              backendMode === "local"
                ? "bg-[var(--surface-hover)] font-medium text-[var(--text-primary)]"
                : "text-[var(--text-faint)] hover:text-[var(--text-secondary)]"
            }`}
          >
            Local
          </button>
        </div>

        {backendMode === "local" ? (
          <button
            type="button"
            onClick={onImportLocalProject}
            className="inline-flex max-w-[160px] items-center gap-1.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-soft)] px-2.5 py-1 text-[10px] text-[var(--text-secondary)] transition-all hover:border-[var(--border-strong)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] cursor-pointer sm:max-w-[220px] sm:py-1.5 sm:text-xs"
            title={localRootDir ? `Change folder: ${localRootDir}` : "Select project folder"}
            aria-label="Select project folder"
          >
            <FolderOpen size={12} strokeWidth={1.9} className="shrink-0" />
            <span className="truncate">{localRootDir || "Select folder"}</span>
          </button>
        ) : null}
      </div>
    </div>
  );
}
