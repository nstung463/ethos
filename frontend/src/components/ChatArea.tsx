import { useEffect, useRef } from "react";
import type { ChatThread, ModeConfig } from "../types";
import EmptyState from "./EmptyState";
import MessageBubble from "./MessageBubble";

export default function ChatArea({
  thread,
  modeConfig,
  onSuggestion,
}: {
  thread: ChatThread | null;
  modeConfig: ModeConfig;
  onSuggestion: (text: string) => void;
}) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thread?.messages.length, thread?.messages.at(-1)?.content]);

  const messages = thread?.messages ?? [];

  return (
    <div className="flex-1 overflow-y-auto py-3 sm:py-4">
      {messages.length === 0 ? (
        <EmptyState modeConfig={modeConfig} onSuggestion={onSuggestion} />
      ) : (
        <div className="max-w-4xl mx-auto space-y-3 sm:space-y-4 pb-4 px-2">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
