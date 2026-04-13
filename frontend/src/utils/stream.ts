import { API_BASE_URL } from "../constants";
import type { Attachment, Message, StreamChunk, UserApiKeys } from "../types";
import { toApiMessages } from "./threads";

function buildMetadata(apiKeys: UserApiKeys) {
  return { user_api_keys: apiKeys };
}

export async function fetchModels(signal?: AbortSignal) {
  const response = await fetch(`${API_BASE_URL}/v1/models`, { signal });
  if (!response.ok) throw new Error(`Failed to load models (${response.status})`);
  const payload = (await response.json()) as { data?: Array<{ id: string; object: string }> };
  return payload.data ?? [];
}

export async function streamChat({
  model,
  messages,
  modeInstruction,
  sessionId,
  fileIds,
  apiKeys,
  signal,
  onContent,
  onReasoning,
}: {
  model: string;
  messages: Message[];
  modeInstruction: string;
  sessionId: string;
  fileIds: string[];
  apiKeys: UserApiKeys;
  signal: AbortSignal;
  onContent: (chunk: string) => void;
  onReasoning: (chunk: string) => void;
}) {
  const response = await fetch(`${API_BASE_URL}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      messages: toApiMessages(messages, modeInstruction),
      stream: true,
      session_id: sessionId,
      file_ids: fileIds,
      metadata: buildMetadata(apiKeys),
    }),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Chat request failed (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const event of events) {
      const line = event.split("\n").find((l) => l.startsWith("data: "));
      if (!line) continue;

      const data = line.slice(6);
      if (data === "[DONE]") return;

      const parsed = JSON.parse(data) as StreamChunk;
      const delta = parsed.choices?.[0]?.delta;
      if (delta?.content) onContent(delta.content);
      if (delta?.reasoning_content) onReasoning(delta.reasoning_content);
    }
  }
}

export async function uploadManagedFile(file: File, signal?: AbortSignal): Promise<Attachment> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/files/`, {
    method: "POST",
    body: formData,
    signal,
  });

  if (!response.ok) {
    throw new Error(`File upload failed (${response.status})`);
  }

  const payload = (await response.json()) as {
    id: string;
    filename: string;
    meta?: { content_type?: string; size?: number };
  };

  return {
    id: payload.id,
    filename: payload.filename,
    contentType: payload.meta?.content_type,
    size: payload.meta?.size,
  };
}

async function postTask<T>(
  path: string,
  {
    model,
    messages,
    modeInstruction,
    apiKeys,
    signal,
  }: {
    model: string;
    messages: Message[];
    modeInstruction: string;
    apiKeys: UserApiKeys;
    signal?: AbortSignal;
  },
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      messages: toApiMessages(messages, modeInstruction),
      metadata: buildMetadata(apiKeys),
    }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Task request failed (${response.status})`);
  }

  return (await response.json()) as T;
}

export async function generateTitle(input: {
  model: string;
  messages: Message[];
  modeInstruction: string;
  apiKeys: UserApiKeys;
  signal?: AbortSignal;
}) {
  return postTask<{ title?: string }>("/v1/tasks/title", input);
}

export async function generateFollowUps(input: {
  model: string;
  messages: Message[];
  modeInstruction: string;
  apiKeys: UserApiKeys;
  signal?: AbortSignal;
}) {
  return postTask<{ follow_ups?: string[] }>("/v1/tasks/follow-ups", input);
}
