export type ModelInfo = {
  id: string;
  object: string;
  owned_by?: string;
};

export type Role = "user" | "assistant" | "system";
export type ComposerMode = "build" | "review" | "explain";

export type Message = {
  id: string;
  role: Role;
  content: string;
  reasoning?: string;
  toolEvents?: string[];
  createdAt: string;
  status?: "streaming" | "done" | "error";
  error?: string;
  thinkingDuration?: number; // seconds
};

export type ChatThread = {
  id: string;
  title: string;
  model: string;
  mode: ComposerMode;
  messages: Message[];
  updatedAt: string;
};

export type StreamChunk = {
  choices?: Array<{
    delta?: {
      content?: string;
      reasoning_content?: string;
    };
    finish_reason?: string | null;
  }>;
};

export type ModeConfig = {
  id: ComposerMode;
  label: string;
  eyebrow: string;
  instruction: string;
  placeholder: string;
  suggestions: string[];
};

export type AppView = "chat" | "settings";

export type SettingsSection =
  | "general"
  | "appearance"
  | "api-keys"
  | "model-settings"
  | "security";
