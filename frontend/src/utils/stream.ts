import { API_BASE_URL } from "../constants";
import type { Message, StreamChunk } from "../types";
import { toApiMessages } from "./threads";

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
  signal,
  onContent,
  onReasoning,
}: {
  model: string;
  messages: Message[];
  modeInstruction: string;
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
