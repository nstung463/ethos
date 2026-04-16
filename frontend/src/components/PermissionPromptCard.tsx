import { AlertTriangle, LockKeyhole, ShieldAlert, ShieldCheck } from "lucide-react";
import { useState } from "react";
import type { PermissionMode, PermissionRequest, ThreadPermissionsBundle } from "../types";

export default function PermissionPromptCard({
  prompt,
  threadPermissions,
  onApproveOnce,
  onApproveForChat,
  onBypassForChat,
  onPromoteThreadPermissions,
  onOpenSecuritySettings,
}: {
  prompt: PermissionRequest;
  threadPermissions: ThreadPermissionsBundle | null;
  onApproveOnce: () => Promise<void>;
  onApproveForChat: (mode: PermissionMode) => Promise<void>;
  onBypassForChat: () => Promise<void>;
  onPromoteThreadPermissions: () => Promise<void>;
  onOpenSecuritySettings: () => void;
}) {
  const [status, setStatus] = useState("");
  const [busyAction, setBusyAction] = useState<"" | "approve_once" | "approve_chat" | "bypass_chat" | "promote">("");

  async function runAction(
    action: "" | "approve_once" | "approve_chat" | "bypass_chat" | "promote",
    fn: () => Promise<void>,
  ) {
    try {
      setBusyAction(action);
      setStatus("");
      await fn();
      if (action === "promote") {
        setStatus("Saved as your default permission profile.");
      } else {
        setStatus("Approval applied. Retrying the blocked action...");
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Permission update failed.");
    } finally {
      setBusyAction("");
    }
  }

  const effectiveMode = threadPermissions?.effective.mode ?? null;
  const icon =
    prompt.behavior === "ask" ? (
      <ShieldAlert size={18} strokeWidth={1.9} />
    ) : (
      <LockKeyhole size={18} strokeWidth={1.9} />
    );

  return (
    <div className="mt-3 rounded-2xl border border-[var(--border-strong)] bg-[var(--panel-elevated)] p-4 shadow-[0_16px_40px_var(--shadow-panel)]">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[color:color-mix(in_oklab,var(--accent)_18%,var(--panel-raised))] text-[var(--accent)]">
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-[var(--text-primary)]">
              {prompt.behavior === "ask" ? "This chat needs permission" : "This chat is blocked by permissions"}
            </p>
            {effectiveMode ? (
              <span className="rounded-full border border-[var(--border-subtle)] bg-[var(--surface-soft)] px-2 py-0.5 text-[10px] uppercase tracking-[0.16em] text-[var(--text-soft)]">
                {effectiveMode.replace("_", " ")}
              </span>
            ) : null}
          </div>
          <p className="mt-1 text-sm leading-6 text-[var(--text-secondary)]">{prompt.reason}</p>
          <p className="mt-2 text-xs leading-5 text-[var(--text-soft)]">
            Approvals here are temporary for this thread. Use settings only if you want to change your defaults.
          </p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => runAction("approve_once", onApproveOnce)}
          disabled={busyAction !== ""}
          className="rounded-xl border border-[var(--border-subtle)] px-3 py-2 text-sm font-medium text-[var(--text-primary)] transition hover:border-[var(--border-strong)] hover:bg-[var(--surface-hover)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busyAction === "approve_once" ? "Retrying..." : "Approve once"}
        </button>
        <button
          type="button"
          onClick={() =>
            runAction(
              "approve_chat",
              () => onApproveForChat(prompt.suggested_thread_mode ?? "bypass_permissions"),
            )
          }
          disabled={busyAction !== ""}
          className="rounded-xl border border-[var(--accent)]/40 bg-[color:color-mix(in_oklab,var(--accent)_10%,transparent)] px-3 py-2 text-sm font-medium text-[var(--text-primary)] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busyAction === "approve_chat" ? "Retrying..." : "Approve for this chat"}
        </button>
        <button
          type="button"
          onClick={() => runAction("bypass_chat", onBypassForChat)}
          disabled={busyAction !== ""}
          className="rounded-xl border border-[var(--border-subtle)] px-3 py-2 text-sm font-medium text-[var(--text-secondary)] transition hover:border-[var(--border-strong)] hover:bg-[var(--surface-hover)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busyAction === "bypass_chat" ? "Retrying..." : "Bypass for this chat"}
        </button>
        <button
          type="button"
          onClick={() => runAction("promote", onPromoteThreadPermissions)}
          disabled={busyAction !== ""}
          className="rounded-xl border border-[var(--border-subtle)] px-3 py-2 text-sm font-medium text-[var(--text-secondary)] transition hover:border-[var(--border-strong)] hover:bg-[var(--surface-hover)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busyAction === "promote" ? "Saving..." : "Save current thread defaults"}
        </button>
        <button
          type="button"
          onClick={onOpenSecuritySettings}
          className="rounded-xl px-3 py-2 text-sm font-medium text-[var(--accent)] transition hover:bg-[color:color-mix(in_oklab,var(--accent)_10%,transparent)]"
        >
          Open Security Settings
        </button>
      </div>

      {status ? (
        <div className="mt-3 flex items-center gap-2 rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-soft)] px-3 py-2 text-xs text-[var(--text-secondary)]">
          {status.includes("failed") ? <AlertTriangle size={14} strokeWidth={1.8} /> : <ShieldCheck size={14} strokeWidth={1.8} />}
          <span>{status}</span>
        </div>
      ) : null}
    </div>
  );
}
