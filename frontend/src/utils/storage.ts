import { STORAGE_KEY, LEGACY_STORAGE_KEY } from "../constants";
import type { Attachment, ChatThread, Message, ComposerMode } from "../types";

function createId(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

function normalizeThread(thread: ChatThread | Record<string, unknown>): ChatThread {
  const rawMessages = Array.isArray(thread.messages)
    ? (thread.messages as Array<Record<string, unknown>>)
    : [];

  const messages: Message[] = rawMessages.map((msg) => ({
    ...(msg.permissionRequest && typeof msg.permissionRequest === "object"
      ? (() => {
          const permissionRequest = msg.permissionRequest as Record<string, unknown>;
          const behavior = permissionRequest.behavior;
          const reason = permissionRequest.reason;
          const toolName =
            typeof permissionRequest.tool_name === "string" ? permissionRequest.tool_name : undefined;
          const suggestedThreadMode =
            permissionRequest.suggested_thread_mode === "default" ||
            permissionRequest.suggested_thread_mode === "accept_edits" ||
            permissionRequest.suggested_thread_mode === "bypass_permissions" ||
            permissionRequest.suggested_thread_mode === "dont_ask"
              ? permissionRequest.suggested_thread_mode
              : undefined;
          return behavior === "ask" || behavior === "deny"
            ? typeof reason === "string"
              ? {
                  permissionRequest: {
                    behavior,
                    reason,
                    tool_name: toolName,
                    suggested_thread_mode: suggestedThreadMode,
                  },
                }
              : {}
            : {};
        })()
      : {}),
    id: typeof msg.id === "string" ? msg.id : createId("msg"),
    role:
      msg.role === "assistant" || msg.role === "system" || msg.role === "user"
        ? msg.role
        : "assistant",
    content: typeof msg.content === "string" ? msg.content : "",
    reasoning: typeof msg.reasoning === "string" ? msg.reasoning : "",
    toolEvents: Array.isArray(msg.toolEvents)
      ? msg.toolEvents.filter((x): x is string => typeof x === "string")
      : [],
    followUps: Array.isArray(msg.followUps)
      ? msg.followUps.filter((x): x is string => typeof x === "string")
      : [],
    createdAt: typeof msg.createdAt === "string" ? msg.createdAt : new Date().toISOString(),
    status:
      msg.status === "streaming" || msg.status === "error" || msg.status === "done"
        ? msg.status
        : "done",
    error: typeof msg.error === "string" ? msg.error : "",
    thinkingDuration: typeof msg.thinkingDuration === "number" ? msg.thinkingDuration : undefined,
  }));

  const rawAttachments = Array.isArray(thread.attachments)
    ? (thread.attachments as Array<Record<string, unknown>>)
    : [];

  const attachments: Attachment[] = rawAttachments
    .map((attachment) => ({
      id: typeof attachment.id === "string" ? attachment.id : "",
      filename: typeof attachment.filename === "string" ? attachment.filename : "",
      contentType:
        typeof attachment.contentType === "string" ? attachment.contentType : undefined,
      size: typeof attachment.size === "number" ? attachment.size : undefined,
    }))
    .filter((attachment) => attachment.id && attachment.filename);

  return {
    id: typeof thread.id === "string" ? thread.id : createId("chat"),
    remoteId: typeof thread.remoteId === "string" ? thread.remoteId : undefined,
    title: typeof thread.title === "string" ? thread.title : "New conversation",
    model: typeof thread.model === "string" ? thread.model : "",
    profileId: typeof thread.profileId === "string" ? thread.profileId : undefined,
    backendMode:
      thread.backendMode === "local" || thread.backendMode === "sandbox"
        ? thread.backendMode
        : "sandbox",
    localRootDir: typeof thread.localRootDir === "string" ? thread.localRootDir : "",
    mode:
      thread.mode === "build" || thread.mode === "review" || thread.mode === "explain"
        ? (thread.mode as ComposerMode)
        : "build",
    messages,
    attachments,
    updatedAt:
      typeof thread.updatedAt === "string" ? thread.updatedAt : new Date().toISOString(),
  };
}

export function loadThreads(): ChatThread[] {
  const raw = localStorage.getItem(STORAGE_KEY) ?? localStorage.getItem(LEGACY_STORAGE_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as Array<ChatThread | Record<string, unknown>>;
    return Array.isArray(parsed) ? parsed.map(normalizeThread) : [];
  } catch {
    return [];
  }
}

export function saveThreads(threads: ChatThread[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(threads));
}
