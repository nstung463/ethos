import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { ChatThread, ComposerMode } from "../types";
import { createEmptyThread } from "../utils/threads";
import { uploadManagedFile } from "../utils/stream";
import { useThreads } from "../context/ThreadsContext";

interface FileUploadOptions {
  activeThread: ChatThread | null;
  activeModel: string;
  activeMode: ComposerMode;
  activeProfileId: string;
  activeBackendMode: "sandbox" | "local";
  activeLocalRootDir: string;
  setStatus: (s: string) => void;
  setError: (e: string) => void;
}

export function useFileUpload({
  activeThread,
  activeModel,
  activeMode,
  activeProfileId,
  activeBackendMode,
  activeLocalRootDir,
  setStatus,
  setError,
}: FileUploadOptions) {
  const navigate = useNavigate();
  const { setThreads, updateThread } = useThreads();
  const [isUploading, setIsUploading] = useState(false);

  async function handleUploadFiles(files: File[]) {
    if (files.length === 0) return;

    setError("");
    setStatus(files.length === 1 ? "Uploading file..." : "Uploading files...");
    setIsUploading(true);

    try {
      const uploaded = await Promise.all(files.map((f) => uploadManagedFile(f)));

      if (!activeThread) {
        const nextThread = createEmptyThread(activeModel, activeMode);
        setThreads((current) => [
          {
            ...nextThread,
            profileId: activeProfileId,
            backendMode: activeBackendMode,
            localRootDir: activeBackendMode === "local" ? activeLocalRootDir : "",
            attachments: uploaded,
            updatedAt: new Date().toISOString(),
          },
          ...current,
        ]);
        navigate(`/app/${nextThread.id}`);
      } else {
        updateThread(activeThread.id, (thread) => {
          const seen = new Set(thread.attachments.map((a) => a.id));
          const nextAttachments = [...thread.attachments];
          for (const a of uploaded) {
            if (!seen.has(a.id)) {
              nextAttachments.push(a);
              seen.add(a.id);
            }
          }
          return { ...thread, attachments: nextAttachments, updatedAt: new Date().toISOString() };
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
      attachments: thread.attachments.filter((a) => a.id !== attachmentId),
      updatedAt: new Date().toISOString(),
    }));
  }

  return { isUploading, handleUploadFiles, handleRemoveAttachment };
}
