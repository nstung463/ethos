import type { ChatThread } from "../types";
import { getLatestPreview } from "../utils/threads";

function formatTime(dateString: string) {
  const d = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function ThreadItem({
  thread,
  isActive,
  onSelect,
  onDelete,
}: {
  thread: ChatThread;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
}) {
  const latest = thread.messages.at(-1);
  const isRunning = latest?.role === "assistant" && latest.status === "streaming";
  const hasError = thread.messages.some((m) => m.status === "error");
  const preview = getLatestPreview(thread);

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`group w-full rounded-[10px] px-3 py-2 text-left transition-colors ${
        isActive
          ? "bg-[var(--surface-hover)] text-[var(--text-primary)] hover:bg-[var(--surface-hover-strong)]"
          : "text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)]"
      }`}
    >
      <div className="mb-0.5 flex items-center justify-between gap-2">
        <span className="truncate text-[13px] font-medium leading-5">{thread.title}</span>
        <div className="flex shrink-0 items-center gap-1.5">
          {isRunning ? <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--success)]" /> : null}
          {hasError && !isRunning ? <span className="h-1.5 w-1.5 rounded-full bg-[var(--danger)]" /> : null}
          <span className={`text-[10px] group-hover:hidden ${isActive ? "text-[var(--text-muted)]" : "text-[var(--text-soft)]"}`}>
            {formatTime(thread.updatedAt)}
          </span>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className={`hidden px-1 text-[10px] transition-colors group-hover:flex cursor-pointer ${
              isActive ? "text-[var(--text-muted)] hover:text-[var(--danger)]" : "text-[var(--text-soft)] hover:text-[var(--danger)]"
            }`}
            title="Delete conversation"
          >
            Delete
          </button>
        </div>
      </div>
      <p className={`truncate text-[11px] leading-4 ${isActive ? "text-[var(--text-muted)]" : "text-[var(--text-soft)]"}`}>
        {preview.slice(0, 80)}
      </p>
    </button>
  );
}
