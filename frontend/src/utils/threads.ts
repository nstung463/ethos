import type { ChatThread, ComposerMode, Message } from "../types";

export function createId(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

export function createEmptyThread(model = "", mode: ComposerMode = "build"): ChatThread {
  return {
    id: createId("chat"),
    remoteId: undefined,
    title: "New conversation",
    model,
    mode,
    messages: [],
    attachments: [],
    updatedAt: new Date().toISOString(),
  };
}

export function summarizeTitle(text: string) {
  const normalized = text.replace(/\s+/g, " ").trim();
  return normalized ? normalized.slice(0, 56) : "New conversation";
}

export function getRelativeGroupLabel(dateString: string) {
  const input = new Date(dateString);
  const today = new Date();
  const startOfInput = new Date(input.getFullYear(), input.getMonth(), input.getDate()).getTime();
  const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
  const diffDays = Math.round((startOfToday - startOfInput) / 86400000);

  if (diffDays <= 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return "This week";
  return input.toLocaleDateString(undefined, { month: "long", year: "numeric" });
}

export function groupThreads(threads: ChatThread[]) {
  const groups: Array<{ label: string; items: ChatThread[] }> = [];
  threads
    .slice()
    .sort((a, b) => Date.parse(b.updatedAt) - Date.parse(a.updatedAt))
    .forEach((thread) => {
      const label = getRelativeGroupLabel(thread.updatedAt);
      const current = groups.at(-1);
      if (!current || current.label !== label) {
        groups.push({ label, items: [thread] });
      } else {
        current.items.push(thread);
      }
    });
  return groups;
}

export function getLatestPreview(thread: ChatThread) {
  const latest = thread.messages.at(-1);
  if (!latest) return "Fresh conversation";
  if (latest.role === "assistant" && latest.status === "streaming") {
    return latest.content || "Thinking...";
  }
  return latest.content || "Fresh conversation";
}

export function mergeReasoning(message: Message, chunk: string): Message {
  const lines = chunk.split("\n");
  const thinkingLines: string[] = [];
  const toolEvents = [...(message.toolEvents ?? [])];

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      thinkingLines.push(line);
      continue;
    }
    if (trimmed.startsWith("Using tool `")) {
      toolEvents.push(trimmed);
    } else {
      thinkingLines.push(line);
    }
  }

  const nextReasoning = [message.reasoning ?? "", thinkingLines.join("\n")]
    .filter(Boolean)
    .join("")
    .trim();

  return { ...message, reasoning: nextReasoning, toolEvents };
}

export function getToolLabel(input: string) {
  const match = input.match(/Using tool `([^`]+)`/);
  return match?.[1] ?? input;
}

export function getToolParams(input: string) {
  const normalized = input.trim();
  const match = normalized.match(/^Using tool `([^`]+)`\(([\s\S]*)\)$/);
  return match?.[2]?.trim() ?? "";
}

export function formatToolParams(input: string, maxLength = 360) {
  const params = getToolParams(input);
  if (!params) return "No parameters";

  const compact = params.replace(/\s+/g, " ").trim();
  if (compact.length <= maxLength) return compact;
  return `${compact.slice(0, maxLength).trimEnd()}...`;
}

export function toApiMessages(messages: Message[], modeInstruction: string) {
  return [
    { role: "system" as const, content: modeInstruction },
    ...messages
      .filter((m) => m.role !== "system")
      .map(({ role, content }) => ({ role, content })),
  ];
}
