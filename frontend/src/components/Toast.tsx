import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { CheckCircle, Info, X, XCircle } from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────

type ToastVariant = "success" | "error" | "info";

interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  toast: {
    success: (message: string) => void;
    error: (message: string) => void;
    info: (message: string) => void;
  };
}

// ── Context ────────────────────────────────────────────────────────────────────

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within <ToastProvider>");
  return ctx;
}

// ── Variant config (no JSX at module level) ────────────────────────────────────

type VariantConfig = { cls: string; Icon: typeof CheckCircle };

const VARIANT_CONFIG: Record<ToastVariant, VariantConfig> = {
  success: {
    cls: "border-[var(--success)] bg-[var(--success-bg)]",
    Icon: CheckCircle,
  },
  error: {
    cls: "border-[var(--danger-border)] bg-[var(--danger-bg)]",
    Icon: XCircle,
  },
  info: {
    cls: "border-[var(--border-strong)] bg-[var(--panel-elevated)]",
    Icon: Info,
  },
};

// ── Icon color per variant ─────────────────────────────────────────────────────

const ICON_COLOR: Record<ToastVariant, string> = {
  success: "text-[var(--success)]",
  error: "text-[var(--danger)]",
  info: "text-[var(--accent)]",
};

// ── Single Toast entry component ───────────────────────────────────────────────

const AUTO_DISMISS_MS = 4000;

function ToastEntry({
  item,
  onDismiss,
}: {
  item: ToastItem;
  onDismiss: (id: string) => void;
}) {
  const [visible, setVisible] = useState(false);
  const timerRef = useRef<ReturnType<typeof window.setTimeout> | undefined>(undefined);

  // Animate in
  useEffect(() => {
    const frameId = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(frameId);
  }, []);

  // Auto-dismiss
  useEffect(() => {
    timerRef.current = window.setTimeout(() => {
      setVisible(false);
      window.setTimeout(() => onDismiss(item.id), 300);
    }, AUTO_DISMISS_MS);
    return () => window.clearTimeout(timerRef.current);
  }, [item.id, onDismiss]);

  const handleDismiss = () => {
    window.clearTimeout(timerRef.current);
    setVisible(false);
    window.setTimeout(() => onDismiss(item.id), 300);
  };

  const { cls, Icon } = VARIANT_CONFIG[item.variant];
  const iconColor = ICON_COLOR[item.variant];

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`flex min-w-[260px] max-w-[380px] items-start gap-2.5 rounded-xl border px-3.5 py-3 shadow-lg transition-all duration-300 ease-out ${cls} ${
        visible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
      }`}
    >
      <Icon size={16} strokeWidth={2} className={`shrink-0 ${iconColor}`} />
      <span className="flex-1 text-sm text-[var(--text-primary)] leading-snug">
        {item.message}
      </span>
      <button
        type="button"
        onClick={handleDismiss}
        className="shrink-0 rounded-md p-0.5 text-[var(--text-soft)] transition hover:text-[var(--text-primary)]"
        aria-label="Dismiss"
      >
        <X size={14} strokeWidth={2} />
      </button>
    </div>
  );
}

// ── Provider ───────────────────────────────────────────────────────────────────

const MAX_TOASTS = 5;

function createId() {
  return Math.random().toString(36).slice(2);
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((curr) => curr.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((message: string, variant: ToastVariant) => {
    setToasts((curr) => {
      const next: ToastItem = { id: createId(), message, variant };
      return [...curr.slice(-(MAX_TOASTS - 1)), next];
    });
  }, []);

  const value: ToastContextValue = {
    toast: {
      success: (msg) => addToast(msg, "success"),
      error: (msg) => addToast(msg, "error"),
      info: (msg) => addToast(msg, "info"),
    },
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      {createPortal(
        <div
          aria-live="polite"
          aria-atomic="false"
          className="fixed bottom-5 right-5 z-[200] flex flex-col items-end gap-2.5"
        >
          {toasts.map((t) => (
            <ToastEntry key={t.id} item={t} onDismiss={dismiss} />
          ))}
        </div>,
        document.body,
      )}
    </ToastContext.Provider>
  );
}
