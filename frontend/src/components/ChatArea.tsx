import { useEffect, useRef } from "react";
import type { ChatThread } from "../types";
import MessageBubble from "./MessageBubble";

export default function ChatArea({
  thread,
  onFollowUpClick,
}: {
  thread: ChatThread | null;
  onFollowUpClick: (prompt: string) => void;
}) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thread?.messages.length, thread?.messages.at(-1)?.content]);

  const messages = thread?.messages ?? [];

  return (
    <div className="flex-1 overflow-y-auto py-3 sm:py-4">
        <div className="max-w-4xl mx-auto space-y-3 sm:space-y-4 pb-4 px-2">
        {messages.map((message, index) => (
          <MessageBubble
            key={message.id}
            message={message}
            isLastMessage={index === messages.length - 1}
            onFollowUpClick={onFollowUpClick}
          />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
