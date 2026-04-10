import { FormEvent, startTransition, useEffect, useRef, useState } from "react";
import type { AppView, ChatThread, ComposerMode, ModelInfo } from "./types";
import { getModeConfig } from "./constants";
import { loadThreads, saveThreads } from "./utils/storage";
import { createEmptyThread, createId, mergeReasoning, summarizeTitle } from "./utils/threads";
import { fetchModels, streamChat } from "./utils/stream";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import ChatArea from "./components/ChatArea";
import Composer from "./components/Composer";
import SettingsPage from "./components/SettingsPage";

type Theme = "dark" | "light";

const THEME_STORAGE_KEY = "ethos-theme";

function getInitialThreads(): ChatThread[] {
  if (typeof window === "undefined") return [];
  return loadThreads();
}

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === "dark" || stored === "light") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [threads, setThreads] = useState<ChatThread[]>(getInitialThreads);
  const [activeThreadId, setActiveThreadId] = useState(() => getInitialThreads()[0]?.id ?? "");
  const [draft, setDraft] = useState("");
  const [loadingModels, setLoadingModels] = useState(true);
  const [status, setStatus] = useState("Connecting…");
  const [error, setError] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [appView, setAppView] = useState<AppView>("chat");
  const abortRef = useRef<AbortController | null>(null);
  const reasoningStartRef = useRef<number | null>(null);

  // Persist threads
  useEffect(() => {
    saveThreads(threads);
  }, [threads]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  // Load models on mount
  useEffect(() => {
    const controller = new AbortController();
    setLoadingModels(true);

    fetchModels(controller.signal)
      .then((items) => {
        setModels(items);
        setStatus(items.length > 0 ? "Connected" : "No models found");
        startTransition(() => {
          setThreads((current) => {
            if (current.length > 0) {
              return current.map((t) => ({
                ...t,
                model: t.model || items[0]?.id || "",
              }));
            }
            if (items[0]?.id) return [createEmptyThread(items[0].id)];
            return current;
          });
        });
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "Unable to reach Ethos API";
        setError(msg);
        setStatus("API unavailable");
      })
      .finally(() => setLoadingModels(false));

    return () => controller.abort();
  }, []);

  // Keep activeThreadId in sync
  useEffect(() => {
    if (!activeThreadId && threads.length > 0) {
      setActiveThreadId(threads[0].id);
    }
  }, [activeThreadId, threads]);

  function updateThread(threadId: string, updater: (t: ChatThread) => ChatThread) {
    setThreads((current) =>
      current.map((t) => (t.id === threadId ? updater(t) : t))
    );
  }

  function handleNewChat() {
    const next = createEmptyThread(models[0]?.id || "", activeThread?.mode ?? "build");
    startTransition(() => {
      setThreads((current) => [next, ...current]);
      setActiveThreadId(next.id);
      setDraft("");
      setError("");
      setStatus("New conversation ready");
    });
  }

  function handleSelectThread(id: string) {
    startTransition(() => {
      setActiveThreadId(id);
      setError("");
    });
  }

  function handleDeleteThread(id: string) {
    setThreads((current) => {
      const remaining = current.filter((t) => t.id !== id);
      if (activeThreadId === id) setActiveThreadId(remaining[0]?.id ?? "");
      return remaining;
    });
  }

  function handleModelChange(modelId: string) {
    if (!activeThread) return;
    updateThread(activeThread.id, (t) => ({
      ...t,
      model: modelId,
      updatedAt: new Date().toISOString(),
    }));
  }

  function handleModeChange(mode: ComposerMode) {
    if (!activeThread) return;
    updateThread(activeThread.id, (t) => ({
      ...t,
      mode,
      updatedAt: new Date().toISOString(),
    }));
  }

  function injectSuggestion(text: string) {
    setDraft(text);
  }

  async function handleSubmit(event?: FormEvent) {
    event?.preventDefault();
    const prompt = draft.trim();
    if (!prompt || !activeThread || !activeModel || isStreaming) return;

    setError("");
    setStatus(`Running in ${modeConfig.label.toLowerCase()} mode`);

    const userMsg = {
      id: createId("msg"),
      role: "user" as const,
      content: prompt,
      createdAt: new Date().toISOString(),
      status: "done" as const,
    };

    const assistantMsg = {
      id: createId("msg"),
      role: "assistant" as const,
      content: "",
      reasoning: "",
      toolEvents: [] as string[],
      createdAt: new Date().toISOString(),
      status: "streaming" as const,
    };

    const nextMessages = [...activeThread.messages, userMsg, assistantMsg];

    updateThread(activeThread.id, (t) => ({
      ...t,
      model: activeModel,
      title: t.messages.length === 0 ? summarizeTitle(prompt) : t.title,
      messages: nextMessages,
      updatedAt: new Date().toISOString(),
    }));

    setDraft("");
    setIsStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;
    reasoningStartRef.current = null;

    try {
      await streamChat({
        model: activeModel,
        messages: nextMessages,
        modeInstruction: modeConfig.instruction,
        signal: controller.signal,
        onContent: (chunk) => {
          updateThread(activeThread.id, (t) => ({
            ...t,
            messages: t.messages.map((m) =>
              m.id === assistantMsg.id
                ? { ...m, content: `${m.content}${chunk}` }
                : m
            ),
            updatedAt: new Date().toISOString(),
          }));
        },
        onReasoning: (chunk) => {
          if (!reasoningStartRef.current) {
            reasoningStartRef.current = Date.now();
          }
          updateThread(activeThread.id, (t) => ({
            ...t,
            messages: t.messages.map((m) =>
              m.id === assistantMsg.id ? mergeReasoning(m, chunk) : m
            ),
            updatedAt: new Date().toISOString(),
          }));
        },
      });

      const thinkingDuration = reasoningStartRef.current
        ? Math.round((Date.now() - reasoningStartRef.current) / 1000)
        : undefined;
      reasoningStartRef.current = null;

      updateThread(activeThread.id, (t) => ({
        ...t,
        messages: t.messages.map((m) =>
          m.id === assistantMsg.id ? { ...m, status: "done", thinkingDuration } : m
        ),
        updatedAt: new Date().toISOString(),
      }));
      setStatus("Ready");
    } catch (err: unknown) {
      const msg =
        err instanceof DOMException && err.name === "AbortError"
          ? "Generation stopped"
          : err instanceof Error
          ? err.message
          : "Unknown error";

      updateThread(activeThread.id, (t) => ({
        ...t,
        messages: t.messages.map((m) =>
          m.id === assistantMsg.id
            ? {
                ...m,
                status: "error",
                error: msg,
                content: m.content || "The assistant did not return any text.",
              }
            : m
        ),
      }));
      setError(msg);
      setStatus("Error");
    } finally {
      abortRef.current = null;
      setIsStreaming(false);
    }
  }

  function handleStop() {
    abortRef.current?.abort();
    abortRef.current = null;
    setStatus("Stopped");
  }

  function handleToggleTheme() {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  }

  const activeThread = threads.find((t) => t.id === activeThreadId) ?? threads[0] ?? null;
  const activeModel = activeThread?.model || models[0]?.id || "";
  const activeMode = activeThread?.mode ?? "build";
  const modeConfig = getModeConfig(activeMode);

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--app-bg)] text-[var(--text-primary)]">
      <Sidebar
        threads={threads}
        activeThreadId={activeThreadId}
        onNewChat={handleNewChat}
        onSelectThread={handleSelectThread}
        onDeleteThread={handleDeleteThread}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((v) => !v)}
        onOpenSettings={() => setAppView("settings")}
      />

      <div className="flex flex-col flex-1 min-w-0">
        <Header
          thread={activeThread}
          models={models}
          loadingModels={loadingModels}
          onModelChange={handleModelChange}
          theme={theme}
          onToggleTheme={handleToggleTheme}
        />

        <ChatArea
          thread={activeThread}
          modeConfig={modeConfig}
          onSuggestion={injectSuggestion}
        />

        <Composer
          draft={draft}
          mode={activeMode}
          modeConfig={modeConfig}
          isStreaming={isStreaming}
          activeModel={activeModel}
          status={status}
          error={error}
          onChange={setDraft}
          onSubmit={handleSubmit}
          onStop={handleStop}
          onModeChange={handleModeChange}
          onSuggestion={injectSuggestion}
        />
      </div>

      {/* Settings Modal Overlay */}
      {appView === "settings" && (
        <SettingsPage onClose={() => setAppView("chat")} theme={theme} onThemeChange={handleToggleTheme} />
      )}
    </div>
  );
}
