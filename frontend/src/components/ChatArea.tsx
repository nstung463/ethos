import { useEffect, useRef } from "react";
import type { ChatThread, PermissionMode, ThreadPermissionsBundle } from "../types";
import MessageBubble from "./MessageBubble";

export default function ChatArea({
  thread,
  onFollowUpClick,
  threadPermissions,
  onApproveOnce,
  onApproveForChat,
  onBypassForChat,
  onPromoteThreadPermissions,
  onOpenSecuritySettings,
}: {
  thread: ChatThread | null;
  onFollowUpClick: (prompt: string) => void;
  threadPermissions: ThreadPermissionsBundle | null;
  onApproveOnce: (messageId: string) => Promise<void>;
  onApproveForChat: (messageId: string, mode: PermissionMode) => Promise<void>;
  onBypassForChat: (messageId: string) => Promise<void>;
  onPromoteThreadPermissions: () => Promise<void>;
  onOpenSecuritySettings: () => void;
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
            threadPermissions={threadPermissions}
            onApproveOnce={onApproveOnce}
            onApproveForChat={onApproveForChat}
            onBypassForChat={onBypassForChat}
            onPromoteThreadPermissions={onPromoteThreadPermissions}
            onOpenSecuritySettings={onOpenSecuritySettings}
          />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
