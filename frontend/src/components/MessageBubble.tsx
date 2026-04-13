import type { Message } from "../types";
import FollowUps from "./FollowUps";
import MessageContent from "./MessageContent";
import ThinkingPanel from "./ThinkingPanel";
import TypingIndicator from "./TypingIndicator";

export default function MessageBubble({
  message,
  isLastMessage,
  onFollowUpClick,
}: {
  message: Message;
  isLastMessage: boolean;
  onFollowUpClick: (prompt: string) => void;
}) {
  const isUser = message.role === "user";
  const isStreaming = message.status === "streaming";

  if (isUser) {
    return (
      <div className="flex justify-end px-4 py-1">
        <div
          className="max-w-[85%] min-w-[120px] rounded-2xl rounded-br-sm border border-[var(--border-subtle)] bg-[var(--panel-elevated)] px-3 py-2.5 leading-7 text-[var(--text-primary)] sm:px-4 sm:py-3"
          style={{ fontSize: "var(--message-text-size)" }}
        >
          <MessageContent content={message.content} />
        </div>
      </div>
    );
  }

  const hasThinking = (message.reasoning && message.reasoning.trim().length > 0) || (message.toolEvents && message.toolEvents.length > 0);

  return (
    <div className="flex gap-2 px-4 py-1 sm:gap-3">
      <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[var(--accent)] to-[var(--accent-2)] sm:h-7 sm:w-7">
        <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
          <path
            d="M7 1C3.69 1 1 3.69 1 7s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 2.25a1.5 1.5 0 110 3 1.5 1.5 0 010-3zM7 12a4.5 4.5 0 01-3.75-2.02C3.25 8.9 5.5 8.25 7 8.25s3.75.65 3.75 1.73A4.5 4.5 0 017 12z"
            fill="var(--accent-contrast)"
          />
        </svg>
      </div>

      <div className="min-w-0 flex-1 pt-0.5">
        {hasThinking ? (
          <ThinkingPanel
            reasoning={message.reasoning}
            toolEvents={message.toolEvents}
            isStreaming={isStreaming}
            thinkingDuration={message.thinkingDuration}
          />
        ) : null}

        <div className="leading-7 text-[var(--text-primary)]" style={{ fontSize: "var(--message-text-size)" }}>
          {message.content ? <MessageContent content={message.content} /> : isStreaming && !hasThinking ? <TypingIndicator /> : null}
        </div>

        {message.error ? (
          <div className="mt-2 rounded-lg border px-3 py-2 text-xs text-[var(--danger)]" style={{ background: "var(--danger-bg)", borderColor: "var(--danger-border)" }}>
            {message.error}
          </div>
        ) : null}

        {isLastMessage && message.status === "done" && (message.followUps?.length ?? 0) > 0 ? (
          <FollowUps followUps={message.followUps ?? []} onClick={onFollowUpClick} />
        ) : null}
      </div>
    </div>
  );
}
