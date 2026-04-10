import { STORAGE_KEY, LEGACY_STORAGE_KEY } from "../constants";
import type { ChatThread, Message, ComposerMode } from "../types";

function createId(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

function normalizeThread(thread: ChatThread | Record<string, unknown>): ChatThread {
  const rawMessages = Array.isArray(thread.messages)
    ? (thread.messages as Array<Record<string, unknown>>)
    : [];

  const messages: Message[] = rawMessages.map((msg) => ({
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
    createdAt: typeof msg.createdAt === "string" ? msg.createdAt : new Date().toISOString(),
    status:
      msg.status === "streaming" || msg.status === "error" || msg.status === "done"
        ? msg.status
        : "done",
    error: typeof msg.error === "string" ? msg.error : "",
    thinkingDuration: typeof msg.thinkingDuration === "number" ? msg.thinkingDuration : undefined,
  }));

  return {
    id: typeof thread.id === "string" ? thread.id : createId("chat"),
    title: typeof thread.title === "string" ? thread.title : "New conversation",
    model: typeof thread.model === "string" ? thread.model : "",
    mode:
      thread.mode === "build" || thread.mode === "review" || thread.mode === "explain"
        ? (thread.mode as ComposerMode)
        : "build",
    messages,
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
