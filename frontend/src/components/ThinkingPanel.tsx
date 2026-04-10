import { useEffect, useRef, useState, type ReactNode } from "react";
import { getToolLabel } from "../utils/threads";

function SpinnerIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 14 14" fill="none" className="shrink-0 animate-spin text-[var(--accent)]">
      <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.25" />
      <path d="M7 1.5A5.5 5.5 0 0112.5 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 14 14" fill="none" className="shrink-0 text-[var(--success)]">
      <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M4.5 7l2 2 3-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      className={`shrink-0 text-[var(--text-faint)] transition-transform duration-200 ${open ? "rotate-180" : ""}`}
    >
      <path d="M2.5 4.5l3.5 3 3.5-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function WrenchIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="shrink-0 text-[var(--text-faint)]">
      <path
        d="M9.5 1.5a2.5 2.5 0 00-2.4 3.17L2.5 9.3a.7.7 0 000 1l.2.2a.7.7 0 001 0l4.63-4.6A2.5 2.5 0 009.5 1.5zm0 1.5a1 1 0 110 2 1 1 0 010-2z"
        fill="currentColor"
      />
    </svg>
  );
}

function SlidePanel({ open, children }: { open: boolean; children: ReactNode }) {
  const innerRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(0);

  useEffect(() => {
    const el = innerRef.current;
    if (!el) return;
    setHeight(open ? el.scrollHeight : 0);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const el = innerRef.current;
    if (!el) return;
    const observer = new ResizeObserver(() => {
      setHeight(el.scrollHeight);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [open]);

  return (
    <div style={{ height, overflow: "hidden", transition: "height 0.28s cubic-bezier(0.4, 0, 0.2, 1)" }}>
      <div ref={innerRef}>{children}</div>
    </div>
  );
}

function ToolRow({ label, isLast }: { label: string; isLast: boolean }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={!isLast ? "border-b border-[var(--border-subtle)]" : ""}>
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center gap-1.5 px-2.5 py-1.5 text-left text-[11px] text-[var(--text-soft)] transition-colors hover:bg-[var(--surface-soft)] hover:text-[var(--text-secondary)] cursor-pointer"
      >
        <WrenchIcon />
        <span className="flex-1 font-mono">{label}</span>
        <ChevronIcon open={expanded} />
      </button>
      <SlidePanel open={expanded}>
        <div className="px-2.5 pb-1.5 pt-0">
          <div className="rounded-md border border-[var(--border-subtle)] bg-[var(--app-bg)] px-2.5 py-1.5 font-mono text-[11px] text-[var(--text-faint)]">
            <div className="mb-1 text-[9px] font-sans uppercase tracking-wider text-[var(--text-fainter)]">Tool call</div>
            <span className="text-[var(--accent)]">{label}</span>
            <span className="text-[var(--text-fainter)]">(...)</span>
          </div>
        </div>
      </SlidePanel>
    </div>
  );
}

export default function ThinkingPanel({
  reasoning,
  toolEvents,
  isStreaming,
  thinkingDuration,
}: {
  reasoning?: string;
  toolEvents?: string[];
  isStreaming: boolean;
  thinkingDuration?: number;
}) {
  const tools = toolEvents ?? [];
  const hasReasoning = !!reasoning?.trim();
  const hasContent = hasReasoning || tools.length > 0;
  const [open, setOpen] = useState(isStreaming);
  const prevStreamingRef = useRef(isStreaming);

  useEffect(() => {
    if (isStreaming && !prevStreamingRef.current) {
      setOpen(true);
    }
    prevStreamingRef.current = isStreaming;
  }, [isStreaming]);

  if (!hasContent) return null;

  function getHeaderLabel() {
    if (isStreaming) return "Thinking...";
    if (thinkingDuration !== undefined) {
      if (thinkingDuration < 1) return "Thought for less than a second";
      if (thinkingDuration === 1) return "Thought for 1 second";
      return `Thought for ${thinkingDuration} seconds`;
    }
    return "Thought";
  }

  return (
    <div className="mb-4">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="group flex items-center gap-1.5 text-xs text-[var(--text-soft)] transition-colors hover:text-[var(--text-muted)] cursor-pointer"
      >
        {isStreaming ? <SpinnerIcon /> : <CheckIcon />}
        <span className={isStreaming ? "thinking-shimmer" : "text-[var(--text-soft)]"}>{getHeaderLabel()}</span>
        {tools.length > 0 && !isStreaming ? (
          <span className="rounded-full border border-[var(--border-subtle)] bg-[var(--surface-badge)] px-1.5 py-px text-[9px] text-[var(--text-fainter)]">
            {tools.length} tool{tools.length !== 1 ? "s" : ""}
          </span>
        ) : null}
        <ChevronIcon open={open} />
      </button>

      <SlidePanel open={open}>
        <div className="mt-1.5 overflow-hidden rounded-lg border border-[var(--border-subtle)] bg-[var(--panel-bg-soft)]">
          {tools.length > 0 ? (
            <div className={hasReasoning ? "border-b border-[var(--border-subtle)]" : ""}>
              <div className="px-2.5 pt-1 pb-0.5">
                <span className="text-[8px] font-medium uppercase tracking-wide text-[var(--text-fainter)]">Tools used</span>
              </div>
              {tools.map((event, i) => (
                <ToolRow key={i} label={getToolLabel(event)} isLast={i === tools.length - 1} />
              ))}
            </div>
          ) : null}

          {hasReasoning ? (
            <div className="px-2.5 pt-2 pb-2.5">
              {tools.length > 0 ? (
                <div className="mb-1.5 text-[8px] font-medium uppercase tracking-wide text-[var(--text-fainter)]">Reasoning</div>
              ) : null}
              <pre className="text-[11px] leading-[1.6] whitespace-pre-wrap break-words font-mono text-[var(--text-faint)]">
                {reasoning}
              </pre>
            </div>
          ) : null}

          {isStreaming ? (
            <div className="flex items-center gap-1.5 px-2.5 pb-2">
              <span className="inline-flex gap-1">
                <span className="typing-dot" />
                <span className="typing-dot" style={{ animationDelay: "0.18s" }} />
                <span className="typing-dot" style={{ animationDelay: "0.36s" }} />
              </span>
            </div>
          ) : null}
        </div>
      </SlidePanel>
    </div>
  );
}
