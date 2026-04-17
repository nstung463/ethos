import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  /** Optional custom fallback UI */
  fallback?: ReactNode;
  /** If provided, a "Try again" button calls this + resets boundary state */
  onReset?: () => void;
  /** Label shown in the fallback for context (e.g. "Sidebar") */
  label?: string;
}

interface State {
  hasError: boolean;
  errorMessage: string;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, errorMessage: "" };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, errorMessage: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  handleReset = () => {
    this.props.onReset?.();
    this.setState({ hasError: false, errorMessage: "" });
  };

  render() {
    if (!this.state.hasError) return this.props.children;

    if (this.props.fallback) return this.props.fallback;

    return (
      <div
        role="alert"
        className="flex flex-col items-center justify-center gap-3 rounded-xl border border-[var(--danger-border)] bg-[var(--danger-bg)] p-6 text-center"
      >
        <AlertTriangle
          size={22}
          strokeWidth={1.8}
          className="text-[var(--danger)]"
        />
        <div>
          <p className="text-sm font-medium text-[var(--danger)]">
            {this.props.label
              ? `${this.props.label} crashed`
              : "Something went wrong"}
          </p>
          {this.state.errorMessage ? (
            <p className="mt-1 max-w-[320px] truncate text-[11px] text-[var(--text-muted)]">
              {this.state.errorMessage}
            </p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={this.handleReset}
          className="flex items-center gap-1.5 rounded-lg border border-[var(--danger-border)] px-3 py-1.5 text-xs text-[var(--danger)] transition hover:bg-[var(--danger-bg)] hover:opacity-80"
        >
          <RefreshCw size={13} strokeWidth={2} />
          Try again
        </button>
      </div>
    );
  }
}
