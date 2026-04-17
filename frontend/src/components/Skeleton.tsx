import type { CSSProperties } from "react";

/** A single shimmer skeleton block */
export function Skeleton({
  className = "",
  style,
}: {
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <div
      className={`skeleton-shimmer rounded-md bg-[var(--surface-soft)] ${className}`}
      style={style}
      aria-hidden="true"
    />
  );
}

/** Preset: sidebar thread list skeleton (shows 5 placeholder rows) */
export function ThreadListSkeleton() {
  return (
    <div className="space-y-1 pt-0.5" aria-hidden="true">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="flex flex-col gap-1.5 rounded-[10px] px-3 py-2"
        >
          {/* Title line — varied widths for realism */}
          <Skeleton
            className="h-3"
            style={{ width: `${60 + (i % 3) * 15}%` }}
          />
          {/* Preview line */}
          <Skeleton className="h-2.5" style={{ width: `${40 + (i % 4) * 10}%` }} />
        </div>
      ))}
    </div>
  );
}
