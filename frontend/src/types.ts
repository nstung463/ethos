export type ModelInfo = {
  id: string;
  object: string;
  owned_by?: string;
};

export type UserApiKeys = {
  openrouter: string;
  anthropic: string;
  openai: string;
};

export type Attachment = {
  id: string;
  filename: string;
  contentType?: string;
  size?: number;
};

export type Role = "user" | "assistant" | "system";
export type ComposerMode = "build" | "review" | "explain";

export type Message = {
  id: string;
  role: Role;
  content: string;
  reasoning?: string;
  toolEvents?: string[];
  followUps?: string[];
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
  attachments: Attachment[];
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
