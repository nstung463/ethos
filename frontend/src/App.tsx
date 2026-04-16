import { FormEvent, startTransition, useEffect, useRef, useState } from "react";
import { Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { MonitorSmartphone, Presentation, Shapes, Sparkles } from "lucide-react";
import type { AppView, ChatThread, ComposerMode, ProviderProfile } from "./types";
import { CHAT_SUGGESTIONS, QUICK_ACTIONS, getModeConfig } from "./constants";
import { loadProfiles, saveProfiles } from "./utils/profiles";
import { loadThreads, saveThreads } from "./utils/storage";
import { createEmptyThread, createId, mergeReasoning, summarizeTitle } from "./utils/threads";
import { ensureAuthToken } from "./utils/auth";
import {
  createRemoteThread,
  fetchModels,
  generateFollowUps,
  generateTitle,
  streamChat,
  uploadManagedFile,
} from "./utils/stream";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import ChatArea from "./components/ChatArea";
import Composer from "./components/Composer";
import EmptyState from "./components/EmptyState";
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

function getInitialProfiles(): ProviderProfile[] {
  if (typeof window === "undefined") return [];
  return loadProfiles();
}

function ChatWorkspace() {
  const navigate = useNavigate();
  const { threadId = "" } = useParams<{ threadId: string }>();
  const [threads, setThreads] = useState<ChatThread[]>(getInitialThreads);
  const [profiles, setProfiles] = useState<ProviderProfile[]>(getInitialProfiles);
  const [activeProfileId, setActiveProfileId] = useState<string>(
    () => getInitialProfiles()[0]?.id ?? "",
  );
  const [draft, setDraft] = useState("");
  const [status, setStatus] = useState("Connecting...");
  const [error, setError] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [appView, setAppView] = useState<AppView>("chat");
  const [landingMode, setLandingMode] = useState<ComposerMode>("build");
  const abortRef = useRef<AbortController | null>(null);
  const reasoningStartRef = useRef<number | null>(null);

  useEffect(() => {
    saveThreads(threads);
  }, [threads]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  // Connectivity check — keep fetching /v1/models but don't use result for selector
  useEffect(() => {
    const controller = new AbortController();
    ensureAuthToken()
      .then(() => fetchModels(controller.signal))
      .then((items) => {
        setStatus(items.length > 0 ? "Connected" : "Connected (no server models)");
      })
      .catch(() => {
        setStatus("API unavailable");
      });
    return () => controller.abort();
  }, []);

  // Fallback: if active profile was deleted, select first available
  useEffect(() => {
    if (profiles.length > 0 && !profiles.find((p) => p.id === activeProfileId)) {
      setActiveProfileId(profiles[0].id);
    }
  }, [profiles, activeProfileId]);

  useEffect(() => {
    if (threadId && threads.length > 0 && !threads.some((thread) => thread.id === threadId)) {
      navigate("/app", { replace: true });
    }
  }, [navigate, threadId, threads]);

  const activeThread = threads.find((thread) => thread.id === threadId) ?? null;
  const hasMessages = (activeThread?.messages.length ?? 0) > 0;
  const activeProfile =
    profiles.find((p) => p.id === (activeThread?.profileId ?? activeProfileId)) ??
    profiles.find((p) => p.id === activeProfileId) ??
    profiles[0] ??
    null;
  const activeModel = activeProfile?.model ?? activeThread?.model ?? "";
  const activeMode = activeThread?.mode ?? landingMode;
  const modeConfig = getModeConfig(activeMode);
  const quickActionIcons = [Presentation, Shapes, MonitorSmartphone, Sparkles];
  const quickActionStyles =
    theme === "dark"
      ? [
          {
            card: "border-[#59462a] bg-[linear-gradient(180deg,#21170e_0%,#2f2214_100%)] hover:border-[#c58a2b] hover:bg-[linear-gradient(180deg,#2a1d11_0%,#3a2a18_100%)]",
            badge: "bg-[#3a2917] text-[#f2bf6a] shadow-[0_10px_24px_rgba(0,0,0,0.24)]",
            title: "text-[#fde3b1]",
            body: "text-[#c9a46b]",
          },
          {
            card: "border-[#214c46] bg-[linear-gradient(180deg,#0d1b19_0%,#122623_100%)] hover:border-[#3ea091] hover:bg-[linear-gradient(180deg,#11211e_0%,#18302c_100%)]",
            badge: "bg-[#14322d] text-[#6fe0cf] shadow-[0_10px_24px_rgba(0,0,0,0.24)]",
            title: "text-[#b9f1e8]",
            body: "text-[#7db7ae]",
          },
          {
            card: "border-[#28456f] bg-[linear-gradient(180deg,#101826_0%,#152135_100%)] hover:border-[#5689df] hover:bg-[linear-gradient(180deg,#142032_0%,#1b2b45_100%)]",
            badge: "bg-[#172b49] text-[#8db7ff] shadow-[0_10px_24px_rgba(0,0,0,0.24)]",
            title: "text-[#d8e6ff]",
            body: "text-[#90abd3]",
          },
          {
            card: "border-[#4a3363] bg-[linear-gradient(180deg,#191320_0%,#241a2f_100%)] hover:border-[#8e61c9] hover:bg-[linear-gradient(180deg,#21182a_0%,#2d2040_100%)]",
            badge: "bg-[#2d2140] text-[#d0a5ff] shadow-[0_10px_24px_rgba(0,0,0,0.24)]",
            title: "text-[#eddcff]",
            body: "text-[#b496d4]",
          },
        ]
      : [
          {
            card: "border-[#f0c98d] bg-[linear-gradient(180deg,#fff7e9_0%,#f6e3bf_100%)] hover:border-[#d8a44d] hover:bg-[linear-gradient(180deg,#fff2d7_0%,#efd19f_100%)]",
            badge: "bg-[#fff1cf] text-[#9a5b00] shadow-[0_10px_24px_rgba(217,164,77,0.22)]",
            title: "text-[#543100]",
            body: "text-[#7c5b22]",
          },
          {
            card: "border-[#9dd5ce] bg-[linear-gradient(180deg,#effcf8_0%,#d1f0e8_100%)] hover:border-[#46aa9b] hover:bg-[linear-gradient(180deg,#e3faf4_0%,#bae7dd_100%)]",
            badge: "bg-[#dcf7f0] text-[#0d7a69] shadow-[0_10px_24px_rgba(70,170,155,0.2)]",
            title: "text-[#11483f]",
            body: "text-[#2f6e63]",
          },
          {
            card: "border-[#a9c7f7] bg-[linear-gradient(180deg,#f3f8ff_0%,#dbe9ff_100%)] hover:border-[#5c8fe8] hover:bg-[linear-gradient(180deg,#ebf3ff_0%,#c9ddff_100%)]",
            badge: "bg-[#e3eeff] text-[#2457b8] shadow-[0_10px_24px_rgba(92,143,232,0.22)]",
            title: "text-[#173770]",
            body: "text-[#42639d]",
          },
          {
            card: "border-[#d3b0f0] bg-[linear-gradient(180deg,#fbf4ff_0%,#ead8fb_100%)] hover:border-[#a05ed8] hover:bg-[linear-gradient(180deg,#f8eeff_0%,#dfc1f7_100%)]",
            badge: "bg-[#f1e5ff] text-[#7d39bb] shadow-[0_10px_24px_rgba(160,94,216,0.2)]",
            title: "text-[#522276]",
            body: "text-[#7f58a3]",
          },
        ];

  function updateThread(threadIdToUpdate: string, updater: (thread: ChatThread) => ChatThread) {
    setThreads((current) =>
      current.map((thread) => (thread.id === threadIdToUpdate ? updater(thread) : thread)),
    );
  }

  async function hydrateThreadMetadata(
    thread: ChatThread,
    modeInstruction: string,
    options: { generateTitle: boolean },
    profile: ProviderProfile,
  ) {
    const taskInput = {
      model: profile.model,
      messages: thread.messages,
      modeInstruction,
      profile,
    };

    const tasks = [
      options.generateTitle ? generateTitle(taskInput) : Promise.resolve<{ title?: string }>({}),
      generateFollowUps(taskInput),
    ] as const;

    const [titleResult, followUpsResult] = await Promise.allSettled(tasks);

    if (titleResult.status === "fulfilled") {
      const nextTitle = titleResult.value.title?.trim();
      if (nextTitle) {
        updateThread(thread.id, (current) => ({
          ...current,
          title: nextTitle,
          updatedAt: new Date().toISOString(),
        }));
      }
    }

    if (followUpsResult.status === "fulfilled") {
      updateThread(thread.id, (current) => ({
        ...current,
        messages: current.messages.map((message, index, array) =>
          index === array.length - 1 && message.role === "assistant"
            ? {
                ...message,
                followUps: Array.isArray(followUpsResult.value.follow_ups)
                  ? followUpsResult.value.follow_ups
                  : [],
              }
            : message,
        ),
        updatedAt: new Date().toISOString(),
      }));
    }
  }

  function handleNewChat() {
    abortRef.current?.abort();
    abortRef.current = null;
    setDraft("");
    setError("");
    setStatus("New conversation ready");
    navigate("/app");
  }

  function handleSelectThread(id: string) {
    setError("");
    navigate(`/app/${id}`);
  }

  function handleDeleteThread(id: string) {
    setThreads((current) => current.filter((thread) => thread.id !== id));
    if (threadId === id) {
      navigate("/app");
    }
  }

  function handleProfileChange(profileId: string) {
    setActiveProfileId(profileId);
    if (activeThread) {
      const p = profiles.find((x) => x.id === profileId);
      updateThread(activeThread.id, (thread) => ({
        ...thread,
        profileId,
        model: p?.model ?? thread.model,
        updatedAt: new Date().toISOString(),
      }));
    }
  }

  function handleModeChange(mode: ComposerMode) {
    if (activeThread) {
      updateThread(activeThread.id, (thread) => ({
        ...thread,
        mode,
        updatedAt: new Date().toISOString(),
      }));
      return;
    }

    setLandingMode(mode);
  }

  function injectSuggestion(text: string) {
    setDraft(text);
  }

  async function handleUploadFiles(files: File[]) {
    if (files.length === 0) return;

    setError("");
    setStatus(files.length === 1 ? "Uploading file..." : "Uploading files...");
    setIsUploading(true);

    try {
      const uploaded = await Promise.all(files.map((file) => uploadManagedFile(file)));

      if (!activeThread) {
        const nextThread = createEmptyThread(activeModel, activeMode);
        setThreads((current) => [
          {
            ...nextThread,
            profileId: activeProfileId,
            attachments: uploaded,
            updatedAt: new Date().toISOString(),
          },
          ...current,
        ]);
        navigate(`/app/${nextThread.id}`);
      } else {
        updateThread(activeThread.id, (thread) => {
          const seen = new Set(thread.attachments.map((attachment) => attachment.id));
          const nextAttachments = [...thread.attachments];
          for (const attachment of uploaded) {
            if (!seen.has(attachment.id)) {
              nextAttachments.push(attachment);
              seen.add(attachment.id);
            }
          }

          return {
            ...thread,
            attachments: nextAttachments,
            updatedAt: new Date().toISOString(),
          };
        });
      }

      setStatus(uploaded.length === 1 ? "File attached" : "Files attached");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "File upload failed";
      setError(msg);
      setStatus("Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  function handleRemoveAttachment(attachmentId: string) {
    if (!activeThread) return;
    updateThread(activeThread.id, (thread) => ({
      ...thread,
      attachments: thread.attachments.filter((attachment) => attachment.id !== attachmentId),
      updatedAt: new Date().toISOString(),
    }));
  }

  async function handleSubmit(event?: FormEvent) {
    event?.preventDefault();

    const prompt = draft.trim();
    const pendingAttachments = activeThread?.attachments ?? [];
    if ((!prompt && pendingAttachments.length === 0) || !activeProfile || isStreaming || isUploading) return;

    setError("");
    setStatus(`Running in ${modeConfig.label.toLowerCase()} mode`);

    const now = new Date().toISOString();
    const baseThread = activeThread ?? createEmptyThread(activeModel, activeMode);
    if (!baseThread.profileId) baseThread.profileId = activeProfileId;
    const userMsg = {
      id: createId("msg"),
      role: "user" as const,
      content: prompt || pendingAttachments.map((attachment) => `Attached file: ${attachment.filename}`).join("\n"),
      createdAt: now,
      status: "done" as const,
    };
    const assistantMsg = {
      id: createId("msg"),
      role: "assistant" as const,
      content: "",
      reasoning: "",
      toolEvents: [] as string[],
      createdAt: now,
      status: "streaming" as const,
    };
    const nextMessages = [...baseThread.messages, userMsg, assistantMsg];
      const nextThread: ChatThread = {
        ...baseThread,
        model: activeModel,
        mode: activeMode,
        title: baseThread.messages.length === 0 ? summarizeTitle(prompt) : baseThread.title,
        messages: nextMessages,
        updatedAt: now,
      };

    setThreads((current) => {
      const existingIndex = current.findIndex((thread) => thread.id === nextThread.id);
      if (existingIndex === -1) {
        return [nextThread, ...current];
      }

      return current.map((thread) => (thread.id === nextThread.id ? nextThread : thread));
    });

    if (!activeThread) {
      navigate(`/app/${nextThread.id}`);
    }

    setDraft("");
    setIsStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;
    reasoningStartRef.current = null;

    try {
      const remoteThreadId = nextThread.remoteId ?? (await createRemoteThread(controller.signal));
      if (!nextThread.remoteId) {
        updateThread(nextThread.id, (thread) => ({
          ...thread,
          remoteId: remoteThreadId,
          updatedAt: new Date().toISOString(),
        }));
      }

      await streamChat({
        model: activeModel,
        messages: nextMessages,
        modeInstruction: modeConfig.instruction,
        threadId: remoteThreadId,
        fileIds: pendingAttachments.map((attachment) => attachment.id),
        profile: activeProfile,
        signal: controller.signal,
        onContent: (chunk) => {
          updateThread(nextThread.id, (thread) => ({
            ...thread,
            messages: thread.messages.map((message) =>
              message.id === assistantMsg.id
                ? { ...message, content: `${message.content}${chunk}` }
                : message,
            ),
            updatedAt: new Date().toISOString(),
          }));
        },
        onReasoning: (chunk) => {
          if (!reasoningStartRef.current) {
            reasoningStartRef.current = Date.now();
          }

          updateThread(nextThread.id, (thread) => ({
            ...thread,
            messages: thread.messages.map((message) =>
              message.id === assistantMsg.id ? mergeReasoning(message, chunk) : message,
            ),
            updatedAt: new Date().toISOString(),
          }));
        },
      });

      const thinkingDuration = reasoningStartRef.current
        ? Math.round((Date.now() - reasoningStartRef.current) / 1000)
        : undefined;
      reasoningStartRef.current = null;

      updateThread(nextThread.id, (thread) => ({
        ...thread,
        messages: thread.messages.map((message) =>
          message.id === assistantMsg.id ? { ...message, status: "done", thinkingDuration } : message,
        ),
        updatedAt: new Date().toISOString(),
      }));
      void hydrateThreadMetadata(
        {
          ...nextThread,
          messages: nextMessages.map((message) =>
            message.id === assistantMsg.id ? { ...message, status: "done", thinkingDuration } : message,
          ),
        },
        modeConfig.instruction,
        { generateTitle: baseThread.messages.length === 0 },
        activeProfile,
      );
      setStatus("Ready");
    } catch (err: unknown) {
      const msg =
        err instanceof DOMException && err.name === "AbortError"
          ? "Generation stopped"
          : err instanceof Error
            ? err.message
            : "Unknown error";

      updateThread(nextThread.id, (thread) => ({
        ...thread,
        messages: thread.messages.map((message) =>
          message.id === assistantMsg.id
            ? {
                ...message,
                status: "error",
                error: msg,
                content: message.content || "The assistant did not return any text.",
              }
            : message,
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

  function handleProfilesSave(nextProfiles: ProviderProfile[], nextActiveId: string) {
    setProfiles(nextProfiles);
    setActiveProfileId(nextActiveId);
    saveProfiles(nextProfiles);
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--app-bg)] text-[var(--text-primary)]">
      <Sidebar
        threads={threads}
        activeThreadId={threadId}
        onNewChat={handleNewChat}
        onSelectThread={handleSelectThread}
        onDeleteThread={handleDeleteThread}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((value) => !value)}
        onOpenSettings={() => setAppView("settings")}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header
          thread={activeThread}
          profiles={profiles}
          activeProfileId={activeProfileId}
          onProfileChange={handleProfileChange}
          theme={theme}
          onToggleTheme={handleToggleTheme}
          showConversationActions={hasMessages}
        />

        {hasMessages ? (
          <>
            <ChatArea thread={activeThread} onFollowUpClick={injectSuggestion} />

            <Composer
              draft={draft}
              mode={activeMode}
              modeConfig={modeConfig}
              variant="chat"
              isStreaming={isStreaming}
              isUploading={isUploading}
              activeModel={activeProfile?.name ?? activeModel}
              attachments={activeThread?.attachments ?? []}
              status={status}
              error={error}
              suggestionPrompts={CHAT_SUGGESTIONS}
              onChange={setDraft}
              onSubmit={handleSubmit}
              onStop={handleStop}
              onUploadFiles={handleUploadFiles}
              onRemoveAttachment={handleRemoveAttachment}
              onModeChange={handleModeChange}
              onSuggestion={injectSuggestion}
            />
          </>
        ) : (
          <div className="flex flex-1 justify-center overflow-y-auto px-4 pb-8 pt-2 sm:px-6 sm:pb-10 sm:pt-3">
            <div className="w-full max-w-5xl">
              <EmptyState />

              <div className="mx-auto max-w-3xl">
                <Composer
                  draft={draft}
                  mode={activeMode}
                  modeConfig={modeConfig}
                  variant="landing"
                  isStreaming={isStreaming}
                  isUploading={isUploading}
                  activeModel={activeProfile?.name ?? activeModel}
                  attachments={activeThread?.attachments ?? []}
                  status={status}
                  error={error}
                  suggestionPrompts={CHAT_SUGGESTIONS}
                  onChange={setDraft}
                  onSubmit={handleSubmit}
                  onStop={handleStop}
                  onUploadFiles={handleUploadFiles}
                  onRemoveAttachment={handleRemoveAttachment}
                  onModeChange={handleModeChange}
                  onSuggestion={injectSuggestion}
                />
              </div>

              <div className="mx-auto mt-5 flex max-w-4xl flex-wrap items-center justify-center gap-2 px-2">
                {CHAT_SUGGESTIONS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => injectSuggestion(prompt)}
                    className="rounded-full border border-[var(--border-subtle)] bg-[var(--surface-soft)] px-3 py-1.5 text-xs text-[var(--text-secondary)] transition-all hover:border-[var(--border-strong)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] cursor-pointer"
                  >
                    {prompt}
                  </button>
                ))}
              </div>

                <div className="mx-auto mt-6 grid max-w-4xl grid-cols-1 gap-3 px-6 text-left sm:grid-cols-2 xl:grid-cols-4">
                  {QUICK_ACTIONS.map((action, index) => {
                    const Icon = quickActionIcons[index % quickActionIcons.length];
                    const style = quickActionStyles[index % quickActionStyles.length];
                    return (
                      <button
                        key={action.title}
                        onClick={() => injectSuggestion(action.prompt)}
                        type="button"
                        className={`group rounded-[1.4rem] border p-4 transition-all duration-200 hover:-translate-y-0.5 cursor-pointer ${style.card}`}
                      >
                        <div className={`mb-4 flex h-11 w-11 items-center justify-center rounded-2xl ${style.badge}`}>
                          <Icon size={18} strokeWidth={1.9} />
                        </div>
                        <div className={`mb-1 text-sm font-semibold ${style.title}`}>{action.title}</div>
                        <div className={`text-xs leading-5 ${style.body}`}>{action.prompt}</div>
                      </button>
                    );
                  })}
                </div>
            </div>
          </div>
        )}
      </div>

      {appView === "settings" ? (
        <SettingsPage
          onClose={() => setAppView("chat")}
          theme={theme}
          onThemeChange={handleToggleTheme}
          profiles={profiles}
          activeProfileId={activeProfileId}
          onProfilesSave={handleProfilesSave}
        />
      ) : null}
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/app" replace />} />
      <Route path="/app" element={<ChatWorkspace />} />
      <Route path="/app/:threadId" element={<ChatWorkspace />} />
      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  );
}
