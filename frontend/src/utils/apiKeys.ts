import { API_KEYS_STORAGE_KEY, EMPTY_API_KEYS } from "../constants";
import type { UserApiKeys } from "../types";

function normalizeApiKeys(value: unknown): UserApiKeys {
  if (!value || typeof value !== "object") {
    return { ...EMPTY_API_KEYS };
  }

  const raw = value as Record<string, unknown>;
  return {
    openrouter: typeof raw.openrouter === "string" ? raw.openrouter : "",
    anthropic: typeof raw.anthropic === "string" ? raw.anthropic : "",
    openai: typeof raw.openai === "string" ? raw.openai : "",
  };
}

export function loadApiKeys(): UserApiKeys {
  const raw = localStorage.getItem(API_KEYS_STORAGE_KEY);
  if (!raw) {
    return { ...EMPTY_API_KEYS };
  }

  try {
    return normalizeApiKeys(JSON.parse(raw));
  } catch {
    return { ...EMPTY_API_KEYS };
  }
}

export function saveApiKeys(apiKeys: UserApiKeys): void {
  localStorage.setItem(API_KEYS_STORAGE_KEY, JSON.stringify(normalizeApiKeys(apiKeys)));
}

export function clearApiKeys(): void {
  localStorage.removeItem(API_KEYS_STORAGE_KEY);
}
