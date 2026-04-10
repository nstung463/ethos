import { useDeferredValue, useState, type ReactNode } from "react";
import {
  Bot,
  ChevronDown,
  FolderPlus,
  Library,
  LayoutPanelLeft,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
  Settings,
} from "lucide-react";
import type { ChatThread } from "../types";
import ThreadItem from "./ThreadItem";

function SidebarGlyph({
  children,
  title,
  onClick,
}: {
  children: ReactNode;
  title: string;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex h-9 w-9 items-center justify-center rounded-[10px] text-[var(--text-soft)] transition hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] cursor-pointer"
      title={title}
      aria-label={title}
    >
      {children}
    </button>
  );
}

function SectionHeader({
  title,
  expanded,
  onToggle,
  action,
}: {
  title: string;
  expanded: boolean;
  onToggle: () => void;
  action?: ReactNode;
}) {
  return (
    <div className="mb-1 flex items-center gap-1 px-1">
        <button
          type="button"
          onClick={onToggle}
          className="flex min-w-0 flex-1 items-center gap-1 rounded-lg px-2 py-1 text-[9.5px] font-normal tracking-[0.02em] text-[var(--text-faint)] transition hover:bg-[var(--surface-soft)] hover:text-[var(--text-muted)] cursor-pointer"
        >
        <ChevronDown size={12} strokeWidth={1.9} className={expanded ? "rotate-0 transition-transform" : "-rotate-90 transition-transform"} />
        <span className="truncate">{title}</span>
      </button>
      {action}
    </div>
  );
}

function QuickAction({
  label,
  hint,
  onClick,
  icon,
}: {
  label: string;
  hint?: string;
  onClick?: () => void;
  icon: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex h-9 w-full items-center gap-3 rounded-[10px] px-3 text-sm text-[var(--text-secondary)] transition hover:bg-[var(--surface-hover)] cursor-pointer"
    >
      <span className="flex size-[18px] items-center justify-center text-[var(--text-soft)]">{icon}</span>
      <span className="truncate">{label}</span>
      {hint ? (
        <span className="ml-auto rounded-md border border-[var(--border-subtle)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-faint)] transition group-hover:border-[var(--border-strong)] group-hover:text-[var(--text-muted)]">
          {hint}
        </span>
      ) : null}
    </button>
  );
}

function ProjectItem({
  label,
  count,
  active = false,
}: {
  label: string;
  count: string;
  active?: boolean;
}) {
  return (
    <button
      type="button"
      className={[
        "flex h-9 w-full items-center gap-2 rounded-[10px] px-3 text-left transition cursor-pointer",
        active
          ? "bg-[var(--surface-active)] text-[var(--surface-active-text)]"
          : "text-[var(--text-secondary)] hover:bg-[var(--surface-hover)]",
      ].join(" ")}
    >
      <span className="min-w-0 flex-1 truncate text-[13px] font-medium">{label}</span>
      <span className={active ? "text-[11px] text-[var(--text-muted)]" : "text-[11px] text-[var(--text-soft)]"}>{count}</span>
    </button>
  );
}

export default function Sidebar({
  threads,
  activeThreadId,
  onNewChat,
  onSelectThread,
  onDeleteThread,
  collapsed,
  onToggle,
  onOpenSettings,
}: {
  threads: ChatThread[];
  activeThreadId: string;
  onNewChat: () => void;
  onSelectThread: (id: string) => void;
  onDeleteThread: (id: string) => void;
  collapsed: boolean;
  onToggle: () => void;
  onOpenSettings: () => void;
}) {
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);
  const [projectsExpanded, setProjectsExpanded] = useState(true);
  const [tasksExpanded, setTasksExpanded] = useState(true);

  const needle = deferredSearch.trim().toLowerCase();
  const filtered = threads.filter((thread) => {
    if (!needle) return true;
    return thread.title.toLowerCase().includes(needle) || thread.messages.some((message) => message.content.toLowerCase().includes(needle));
  });

  return (
    <aside
      className={`relative h-full shrink-0 overflow-hidden border-r border-[var(--border-subtle)] bg-[var(--panel-bg)] text-[var(--text-primary)] transition-[width] duration-300 ease-out ${
        collapsed ? "w-16" : "w-[280px]"
      }`}
    >
      <div
        className={`absolute inset-0 flex h-full flex-col items-center py-3 transition-all duration-300 ease-out ${
          collapsed ? "translate-x-0 opacity-100" : "-translate-x-4 opacity-0 pointer-events-none"
        }`}
      >
        <div className="mb-3 flex w-full flex-col items-center gap-2">
          <SidebarGlyph title="Expand sidebar" onClick={onToggle}>
            <PanelLeftOpen size={16} strokeWidth={1.8} />
          </SidebarGlyph>
          <SidebarGlyph title="New task" onClick={onNewChat}>
            <Plus size={16} strokeWidth={1.9} />
          </SidebarGlyph>
        </div>

        <div className="mt-auto flex flex-col items-center gap-2">
          <SidebarGlyph title="Settings" onClick={onOpenSettings}>
            <Settings size={16} strokeWidth={1.8} />
          </SidebarGlyph>
        </div>
      </div>

      <div
        className={`absolute inset-0 flex h-full flex-col transition-all duration-300 ease-out ${
          collapsed ? "translate-x-6 opacity-0 pointer-events-none" : "translate-x-0 opacity-100"
        }`}
      >
        <header className="flex h-14 shrink-0 items-center justify-between px-3">
          <div className="flex min-w-0 items-center gap-3">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-xl text-[var(--accent-contrast)]"
            style={{ background: "var(--surface-sidebar-logo)", color: "var(--surface-active-text)", boxShadow: "0 6px 18px color-mix(in oklab, var(--shadow-panel) 40%, transparent)" }}
          >
            <Bot aria-hidden="true" size={18} strokeWidth={1.8} />
          </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-[var(--text-primary)]">ethos</div>
              <div className="truncate text-xs text-[var(--text-soft)]">Workspace</div>
            </div>
          </div>

          <SidebarGlyph title="Collapse sidebar" onClick={onToggle}>
            <PanelLeftClose size={16} strokeWidth={1.8} />
          </SidebarGlyph>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
          <nav className="space-y-1 pb-4">
            <QuickAction
              label="New task"
              onClick={onNewChat}
              icon={<Plus size={18} strokeWidth={1.9} />}
            />
            <QuickAction
              label="Agents"
              icon={<Bot size={18} strokeWidth={1.8} />}
            />
            <div className="rounded-[10px] border border-[var(--border-subtle)] bg-[var(--surface-soft)] px-3">
              <div className="flex h-9 items-center gap-3">
                <span className="flex size-[18px] items-center justify-center text-[var(--text-soft)]">
                  <Search size={16} strokeWidth={1.8} />
                </span>
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search"
                  className="min-w-0 flex-1 bg-transparent text-sm text-[var(--text-secondary)] outline-none placeholder:text-[var(--text-faint)]"
                />
                <span className="rounded-md border border-[var(--border-subtle)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-faint)]">Ctrl+K</span>
              </div>
            </div>
            <QuickAction
              label="Library"
              icon={<Library size={18} strokeWidth={1.8} />}
            />
          </nav>

          <div className="space-y-4">
            <section>
              <SectionHeader
                title="Projects"
                expanded={projectsExpanded}
                onToggle={() => setProjectsExpanded((value) => !value)}
                action={
                  <SidebarGlyph title="Add project">
                    <FolderPlus size={14} strokeWidth={1.9} />
                  </SidebarGlyph>
                }
              />
              {projectsExpanded ? (
                <div className="space-y-1">
                  <ProjectItem label="Build system" count="4" />
                  <ProjectItem label="Ethos rollout" count="2" active />
                  <ProjectItem label="Research notes" count="9" />
                </div>
              ) : null}
            </section>

            <section>
              <SectionHeader title="All tasks" expanded={tasksExpanded} onToggle={() => setTasksExpanded((value) => !value)} />
              {tasksExpanded ? (
                <div className="space-y-1">
                  {filtered.length > 0 ? (
                    filtered.map((thread) => (
                      <ThreadItem
                        key={thread.id}
                        thread={thread}
                        isActive={thread.id === activeThreadId}
                        onSelect={() => onSelectThread(thread.id)}
                        onDelete={() => onDeleteThread(thread.id)}
                      />
                    ))
                  ) : (
                    <div className="px-3 py-4 text-center text-xs text-[var(--text-soft)]">{search ? "No tasks found" : "No tasks yet"}</div>
                  )}
                </div>
              ) : null}
            </section>
          </div>
        </div>

        <footer className="shrink-0 border-t border-[var(--border-subtle)] bg-[var(--surface-soft)] px-3 pb-3 pt-2 backdrop-blur-sm">
          <div className="mb-2 flex items-center gap-1">
            <SidebarGlyph title="Settings" onClick={onOpenSettings}>
              <Settings size={16} strokeWidth={1.8} />
            </SidebarGlyph>
            <SidebarGlyph title="Layout">
              <LayoutPanelLeft size={16} strokeWidth={1.8} />
            </SidebarGlyph>
            <div className="ml-auto rounded-full border border-[var(--border-subtle)] bg-[var(--surface-badge)] px-2 py-1 text-[11px] font-medium text-[var(--text-muted)]">
              System online
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-[12px] border border-[var(--border-subtle)] bg-[var(--surface-badge)] px-2.5 py-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#f59e0b] text-[#111110]">
              <Bot size={15} strokeWidth={2} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium text-[var(--text-primary)]">Ethos App</div>
              <div className="truncate text-[11px] text-[var(--text-soft)]">frontend v0.1.0</div>
            </div>
          </div>
        </footer>
      </div>
    </aside>
  );
}
