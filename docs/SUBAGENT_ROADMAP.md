# Ethos Subagent Roadmap

This document captures:

- The current Ethos subagent architecture
- The relevant Claude Code `AgentTool` architecture
- The key differences between them
- A staged roadmap for bringing Ethos closer to Claude Code
- Concrete implementation guidance for future coding work

The goal is to preserve this analysis in one place so the work can be resumed later without having to re-investigate the source code.

## Scope

Compared codebases:

- Ethos:
  - [src/subagents.py](/W:/panus/ethos/src/subagents.py)
  - [src/graph.py](/W:/panus/ethos/src/graph.py)
  - [src/middleware/memory.py](/W:/panus/ethos/src/middleware/memory.py)
  - [src/middleware/skills.py](/W:/panus/ethos/src/middleware/skills.py)
- Claude Code:
  - [tools/AgentTool/AgentTool.tsx](/W:/panus/claude-code-source/tools/AgentTool/AgentTool.tsx)
  - [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts)
  - [tools/AgentTool/forkSubagent.ts](/W:/panus/claude-code-source/tools/AgentTool/forkSubagent.ts)
  - [tools/AgentTool/resumeAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/resumeAgent.ts)

## Current Ethos Model

Ethos currently implements subagents as a DeepAgents-style `task` tool.

High-level flow:

1. `create_ethos_agent()` builds the main tool pool and a `task` tool.
2. `build_task_tool()` compiles declarative subagent specs into LangChain agents.
3. When the parent agent calls `task(description, subagent_type)`:
   - Ethos selects the child runnable
   - copies parent state while filtering private keys
   - resets child `messages` to a single `HumanMessage(description)`
   - runs `invoke()` or `ainvoke()`
   - extracts the final child message
   - returns it to the parent as a `ToolMessage` via `Command`

Relevant Ethos implementation points:

- Subagent spec structure:
  - [src/subagents.py](/W:/panus/ethos/src/subagents.py#L29)
- State filtering:
  - [src/subagents.py](/W:/panus/ethos/src/subagents.py#L48)
- Task tool builder:
  - [src/subagents.py](/W:/panus/ethos/src/subagents.py#L149)
- Parent state -> child state adaptation:
  - [src/subagents.py](/W:/panus/ethos/src/subagents.py#L199)
- Sync invoke:
  - [src/subagents.py](/W:/panus/ethos/src/subagents.py#L214)
- Async invoke:
  - [src/subagents.py](/W:/panus/ethos/src/subagents.py#L231)
- Default middleware used for both main agent and subagents:
  - [src/graph.py](/W:/panus/ethos/src/graph.py#L43)

This is a clean and useful model, but it is still much simpler than Claude Code's agent system.

## Claude Code AgentTool Model

Claude Code `AgentTool` is not just a "call child agent" helper. It is a full subagent runtime and orchestration subsystem.

High-level responsibilities handled by Claude Code:

- agent selection and filtering
- per-agent tool pool resolution
- per-agent permission mode resolution
- background subagent lifecycle
- progress streaming and UI integration
- sidechain transcript persistence
- metadata persistence
- resume support
- worktree isolation
- remote execution
- team/teammate spawning
- optional full-context fork mode
- agent-specific MCP lifecycle
- agent hooks and skill preloading

Key source locations:

- Input/output contract:
  - [tools/AgentTool/AgentTool.tsx](/W:/panus/claude-code-source/tools/AgentTool/AgentTool.tsx#L81)
- Main orchestration entrypoint:
  - [tools/AgentTool/AgentTool.tsx](/W:/panus/claude-code-source/tools/AgentTool/AgentTool.tsx#L196)
- Agent execution runtime:
  - [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts#L248)
- Fork mode:
  - [tools/AgentTool/forkSubagent.ts](/W:/panus/claude-code-source/tools/AgentTool/forkSubagent.ts#L18)
- Resume:
  - [tools/AgentTool/resumeAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/resumeAgent.ts#L42)

## Architectural Differences

### 1. Tool Contract

Ethos:

- `task(description, subagent_type)`
- minimal declarative input
- returns final child result immediately

Claude Code:

- `description`
- `prompt`
- `subagent_type`
- `model`
- `run_in_background`
- `name`
- `team_name`
- `mode`
- `isolation`
- `cwd`

Relevant source:

- Ethos:
  - [src/subagents.py](/W:/panus/ethos/src/subagents.py#L114)
- Claude Code:
  - [tools/AgentTool/AgentTool.tsx](/W:/panus/claude-code-source/tools/AgentTool/AgentTool.tsx#L81)

Impact:

- Ethos subagents are currently one-shot delegated tasks.
- Claude Code agents are configurable runtime entities.

### 2. Context Model

Ethos:

- parent state is filtered
- private fields are removed
- child receives one fresh `HumanMessage`
- child does not inherit full transcript

Relevant source:

- [src/subagents.py](/W:/panus/ethos/src/subagents.py#L199)

Claude Code:

- child may receive:
  - inherited conversation messages
  - prompt messages
  - user/system context
  - file read state cache
  - permission context
  - exact or resolved tool pool
  - MCP clients/resources
  - content replacement state
- fork mode can inherit the parent's effective system prompt and full tool context

Relevant source:

- [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts#L368)
- [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts#L380)
- [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts#L500)
- [tools/AgentTool/forkSubagent.ts](/W:/panus/claude-code-source/tools/AgentTool/forkSubagent.ts#L95)

Impact:

- Ethos does isolated delegation by description.
- Claude Code supports both isolated delegation and full-context fork-like execution.

### 3. Runtime Lifecycle

Ethos:

- compile child agents once
- invoke directly
- return final answer

Claude Code:

- construct full child runtime
- register hooks
- initialize agent-specific MCP
- record transcript
- stream progress
- update task registry
- persist metadata
- cleanup resources

Relevant source:

- [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts#L530)
- [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts#L648)
- [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts#L732)
- [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts#L747)

Impact:

- Ethos currently has subagent invocation.
- Claude Code has subagent lifecycle management.

### 4. Background Execution

Ethos:

- async path exists technically
- but `atask()` is still awaited inline by the parent
- no launched task ID
- no independent lifecycle

Relevant source:

- [src/subagents.py](/W:/panus/ethos/src/subagents.py#L231)

Claude Code:

- supports explicit background launch
- registers running subagents
- can notify later on completion/failure
- can expose output file / task ID

Relevant source:

- [tools/AgentTool/AgentTool.tsx](/W:/panus/claude-code-source/tools/AgentTool/AgentTool.tsx#L146)
- [tools/AgentTool/AgentTool.tsx](/W:/panus/claude-code-source/tools/AgentTool/AgentTool.tsx#L567)
- [tools/AgentTool/AgentTool.tsx](/W:/panus/claude-code-source/tools/AgentTool/AgentTool.tsx#L688)

Impact:

- Ethos has no managed background subagents yet.

### 5. Resume

Ethos:

- no resume path
- no transcript replay
- no task metadata

Claude Code:

- resume reads transcript and metadata
- reconstructs replacement state
- restores worktree path if possible
- reconstructs system prompt for forked agents
- relaunches background lifecycle

Relevant source:

- [tools/AgentTool/resumeAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/resumeAgent.ts#L63)
- [tools/AgentTool/resumeAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/resumeAgent.ts#L116)
- [tools/AgentTool/resumeAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/resumeAgent.ts#L166)

Impact:

- This is one of the biggest functional gaps between Ethos and Claude Code.

### 6. Isolation

Ethos:

- shares same repo / same cwd logic as parent agent
- no subagent-level filesystem isolation concept

Claude Code:

- supports `worktree` isolation
- supports `remote` isolation
- can attach worktree metadata to subagent lifecycle
- can clean up or keep worktree depending on changes

Relevant source:

- [tools/AgentTool/AgentTool.tsx](/W:/panus/claude-code-source/tools/AgentTool/AgentTool.tsx#L430)
- [tools/AgentTool/AgentTool.tsx](/W:/panus/claude-code-source/tools/AgentTool/AgentTool.tsx#L582)
- [tools/AgentTool/AgentTool.tsx](/W:/panus/claude-code-source/tools/AgentTool/AgentTool.tsx#L643)

Impact:

- Ethos cannot yet safely parallelize coding agents against the same repo in Claude Code style.

### 7. Permission and Tool Scoping

Ethos:

- child tools are either explicit in spec or inherited from base tools
- middleware can differ, but no dedicated permission model per child

Relevant source:

- [src/subagents.py](/W:/panus/ethos/src/subagents.py#L160)

Claude Code:

- resolves tool pool per child agent definition
- can use exact parent tools for fork mode
- can override permission mode
- can scope allowed tools
- can avoid or bubble permission prompts

Relevant source:

- [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts#L412)
- [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts#L465)
- [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts#L500)

Impact:

- Ethos still lacks the subagent permission surface necessary for more advanced orchestration.

### 8. MCP and Agent-Specific Resources

Ethos:

- subagents receive inherited base tool pool
- no agent-specific MCP startup/cleanup lifecycle

Claude Code:

- agents can define their own MCP requirements and MCP servers
- runtime connects them dynamically
- tools are merged and deduplicated
- new clients are cleaned up after execution

Relevant source:

- [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts#L95)
- [tools/AgentTool/runAgent.ts](/W:/panus/claude-code-source/tools/AgentTool/runAgent.ts#L648)

Impact:

- This is advanced functionality and should not be first priority for Ethos, but it matters if agent definitions become richer.

### 9. Fork Mode

Ethos:

- no equivalent

Claude Code:

- omitting `subagent_type` can trigger a special fork path
- child inherits full assistant/tool context
- parent prompt bytes are reused when possible
- recursive forking is blocked

Relevant source:

- [tools/AgentTool/forkSubagent.ts](/W:/panus/claude-code-source/tools/AgentTool/forkSubagent.ts#L18)
- [tools/AgentTool/forkSubagent.ts](/W:/panus/claude-code-source/tools/AgentTool/forkSubagent.ts#L73)
- [tools/AgentTool/AgentTool.tsx](/W:/panus/claude-code-source/tools/AgentTool/AgentTool.tsx#L318)

Impact:

- Powerful, but should be treated as a late-stage feature for Ethos.

### 10. Teams / Named Agents / Routing

Ethos:

- no team or routing abstraction

Claude Code:

- supports named spawned agents
- team / teammate spawning
- messaging/routing semantics

Relevant source:

- [tools/AgentTool/AgentTool.tsx](/W:/panus/claude-code-source/tools/AgentTool/AgentTool.tsx#L93)
- [tools/AgentTool/AgentTool.tsx](/W:/panus/claude-code-source/tools/AgentTool/AgentTool.tsx#L282)

Impact:

- Important for swarms/teams, but not necessary for first practical parity step.

## Summary Table

| Area | Ethos now | Claude Code | Priority |
|---|---|---|---|
| Sync task delegation | Yes | Yes | done |
| Async inline invocation | Yes | Yes | done |
| Managed background agents | No | Yes | P0 |
| Resume | No | Yes | P0 |
| Per-subagent transcript persistence | No | Yes | P0 |
| Progress streaming | No | Yes | P1 |
| Worktree isolation | No | Yes | P1 |
| Permission scoping | Minimal | Strong | P1 |
| Rich agent definitions | Basic | Strong | P1 |
| Agent-specific MCP lifecycle | No | Yes | P2 |
| Fork full context | No | Yes | P2 |
| Teams / message routing | No | Yes | P3 |
| Remote agents | No | Yes | P3 |

## Recommended Implementation Order

To get the largest practical gain with the least wasted effort, implement in this order:

1. Managed background subagents
2. Resume support
3. Transcript and metadata persistence
4. Progress streaming
5. Worktree isolation
6. Permission/tool scoping per subagent
7. Richer agent definition system
8. Agent-specific MCP lifecycle
9. Fork current context
10. Teams and remote agents

## Phase-by-Phase Roadmap

## Phase 0: Keep the Existing Task Tool as the Baseline

Current Ethos `task` behavior is still valuable:

- simple
- predictable
- easy to test
- low overhead

Do not remove it.

Instead:

- keep `task()` as the synchronous/inline path
- add managed runtime features around it

Suggested compatibility rule:

- `task(...)` remains the simple one-shot child execution API
- new runtime-oriented tools are added next to it

## Phase 1: Managed Async Subagent Runtime

### Goal

Turn subagents from simple child invocations into tracked runtime entities.

### Why this first

This unlocks:

- long-running delegated tasks
- user-visible progress
- later resume support
- later worktree support
- later task cancellation

### Recommended additions

New record model:

```text
SubagentRecord
  id
  subagent_type
  description
  status
  created_at
  updated_at
  result
  error
  transcript_path
  metadata_path
  cwd
  worktree_path?
```

Recommended statuses:

- `pending`
- `running`
- `completed`
- `failed`
- `cancelled`

New tools:

- `task_start`
- `task_check`
- `task_list`
- `task_cancel`
- `task_resume`

Suggested behavior:

- `task_start` launches a child runtime and returns `task_id`
- `task_check` returns current status and final result if completed
- `task_list` lists known subagent tasks
- `task_cancel` stops a running child if possible
- `task_resume` restarts a previously persisted task

### Suggested modules

- `src/subagents/runtime.py`
- `src/subagents/store.py`
- `src/subagents/types.py`

### Suggested implementation notes

- do not build this inside `src/subagents.py` only
- split responsibilities:
  - spec compilation
  - task launching
  - persistence
  - querying status

## Phase 2: Transcript and Metadata Persistence

### Goal

Persist enough state per child task to support:

- debugging
- status inspection
- resume
- post-mortem analysis

### Suggested storage shape

Under workspace:

```text
workspace/.ethos/tasks/<task-id>/
  meta.json
  messages.jsonl
  result.txt
  progress.jsonl
```

Minimum `meta.json` fields:

```json
{
  "id": "task-123",
  "subagent_type": "researcher",
  "description": "Investigate X",
  "status": "running",
  "created_at": "...",
  "updated_at": "...",
  "cwd": "...",
  "worktree_path": null,
  "parent_agent": "ethos"
}
```

### Suggested modules

- `src/subagents/transcript.py`
- `src/subagents/persistence.py`

### Suggested implementation notes

- append-only JSONL is enough initially
- avoid over-designing the format at first
- prioritize stability and inspectability

## Phase 3: Resume

### Goal

Allow a stopped or backgrounded child agent to continue later.

### Minimum viable resume

Resume should be able to:

- reload transcript
- reload metadata
- reconstruct child input state
- continue from a fresh appended instruction

### Important design choice

Ethos does not need Claude Code's full reconstruction complexity immediately.

Initial Ethos resume can be:

- "load previous transcript and task metadata"
- "append new user instruction"
- "spawn new child with reconstructed conversation state"

That is enough for a useful first version.

### Suggested modules

- `src/subagents/resume.py`

### Risks

- if transcript format changes later, resume can break
- if tool results are persisted inconsistently, resumed state can diverge

Mitigation:

- keep transcript schema simple and versioned

## Phase 4: Progress Streaming

### Goal

Expose child progress before completion.

### What to stream

At minimum:

- agent started
- tool started
- tool completed
- shell command running
- shell command completed
- final response ready
- failure

### Suggested design

Create an internal progress event sink:

- child runtime emits events
- events are written to `progress.jsonl`
- optionally mirrored to UI/log stream

Suggested event shape:

```json
{
  "timestamp": "...",
  "task_id": "task-123",
  "type": "tool_started",
  "name": "read_file",
  "payload": {
    "path": "/repo/file.py"
  }
}
```

### Suggested modules

- `src/subagents/progress.py`

## Phase 5: Worktree Isolation

### Goal

Allow coding-oriented subagents to work in isolated git worktrees.

### Why this matters

Without isolation:

- parallel coding agents can collide in the same worktree
- side effects are harder to inspect
- subagent changes are harder to attribute

### Initial Ethos feature set

Support:

- `isolation="worktree"`
- create temporary worktree before task run
- child runs with `cwd=worktree_path`
- on completion:
  - if no changes, cleanup
  - if changes, keep worktree and report path

### Suggested modules

- `src/subagents/worktree.py`

### Important implementation notes

- only do this for git repos
- validate repo root before operations
- keep cleanup conservative
- never delete ambiguous paths

## Phase 6: Permission and Tool Scoping

### Goal

Give each child a more intentional tool and permission surface.

### Extend `SubAgentSpec`

Current spec in Ethos:

- `name`
- `description`
- `system_prompt`
- `tools`
- `model`
- `middleware`

Recommended future fields:

- `allowed_tools`
- `permission_mode`
- `background`
- `isolation`
- `cwd`
- `skills`
- `memory`
- `mcp_servers`

Relevant current definition:

- [src/subagents.py](/W:/panus/ethos/src/subagents.py#L29)

### Practical target

Child runtime should be able to answer:

- what tools can I use?
- may I execute shell?
- may I edit files?
- should I run in background?
- do I need isolated cwd/worktree?

## Phase 7: Rich Agent Definition System

### Goal

Move beyond hard-coded Python dicts toward reusable agent definitions.

### Options

Option A:

- continue using Python dicts, just add more fields

Option B:

- support file-based definitions
- for example YAML or frontmatter-backed markdown files

Recommendation:

- start with richer Python spec
- add file-backed definitions only after the runtime is stable

Why:

- behavior should stabilize before externalizing config format

## Phase 8: Agent-Specific MCP Lifecycle

### Goal

Allow a child agent to declare additional MCP resources/tools that are not globally loaded.

### Why later

This is powerful but not needed for first practical parity.

### Suggested future design

Subagent spec may eventually declare:

- `mcp_servers`
- additive MCP requirements
- cleanup policy

## Phase 9: Fork Mode

### Goal

Support a Claude Code-like "fork the current conversation" path.

### Important warning

This is one of the hardest features to copy correctly.

It requires:

- transcript fidelity
- careful message reconstruction
- duplicate tool-use avoidance
- permission semantics clarity
- clear recursion guards

### Recommendation

Do not implement fork mode before:

- background runtime exists
- transcript persistence exists
- resume exists
- progress exists
- worktree isolation exists

Fork should be treated as a late-phase feature.

## Phase 10: Teams and Remote Execution

### Goal

Add higher-level orchestration:

- named workers
- routed messaging
- remote agent sessions

### Recommendation

Treat this as separate from core subagent parity.

It is useful, but not required for Ethos to gain most of Claude Code's practical value.

## Concrete Suggested Refactor for Ethos

### Current problem

[src/subagents.py](/W:/panus/ethos/src/subagents.py) currently mixes:

- subagent type definitions
- task tool schema
- child agent compilation
- state adaptation
- invoke logic

That was acceptable for the current simple model, but it will become hard to extend once backgrounding, persistence, and worktree isolation are added.

### Suggested split

Keep `src/subagents.py` as the public assembly layer, but move runtime logic out:

```text
src/
  subagents/
    __init__.py
    definitions.py
    builder.py
    runtime.py
    store.py
    transcript.py
    resume.py
    progress.py
    worktree.py
    types.py
```

Suggested responsibilities:

- `definitions.py`
  - built-in agent specs
- `types.py`
  - `SubAgentSpec`, `SubagentRecord`, progress event models
- `builder.py`
  - compile specs into runnable child agents
- `runtime.py`
  - run sync/async child executions
- `store.py`
  - task registry / status lookup
- `transcript.py`
  - persist transcript and progress
- `resume.py`
  - reconstruct task state
- `worktree.py`
  - isolated repo helpers

## P0 Implementation Plan

If implementation is resumed later, this should be the first coding milestone.

### P0 Objective

Add managed background subagents, task persistence, and resume support without breaking existing `task()` behavior.

### P0 Deliverables

1. Preserve current `task()` one-shot behavior.
2. Add `task_start`, `task_check`, `task_list`, `task_resume`.
3. Persist task metadata and transcript to disk.
4. Add tests for:
   - background task registration
   - persistence
   - status lookup
   - resume

### P0 Suggested file work

- new:
  - `src/subagents/runtime.py`
  - `src/subagents/store.py`
  - `src/subagents/transcript.py`
  - `src/subagents/resume.py`
  - `tests/test_subagent_runtime.py`
  - `tests/test_subagent_resume.py`
- modify:
  - [src/subagents.py](/W:/panus/ethos/src/subagents.py)
  - [src/graph.py](/W:/panus/ethos/src/graph.py)

### P0 Suggested tool API

`task`:

- remains synchronous delegation

`task_start`:

- inputs:
  - `description`
  - `subagent_type`
- returns:
  - `task_id`
  - `status`

`task_check`:

- inputs:
  - `task_id`
- returns:
  - `status`
  - `result?`
  - `error?`

`task_list`:

- returns all known managed subagent tasks

`task_resume`:

- inputs:
  - `task_id`
  - `message`
- behavior:
  - append message
  - reconstruct state
  - relaunch

## P1 Implementation Plan

### P1 Objective

Add progress streaming and worktree isolation.

### Deliverables

1. per-task progress event logging
2. optional UI/log integration for progress
3. `isolation="worktree"`
4. task metadata records worktree path
5. cleanup behavior for empty worktrees

## P2 Implementation Plan

### P2 Objective

Add richer subagent definitions and per-agent resource scoping.

### Deliverables

1. richer `SubAgentSpec`
2. tool allowlist / permission mode
3. optional child-specific skills/memory
4. optional child-specific MCP servers

## P3 Implementation Plan

### P3 Objective

Add advanced orchestration features.

### Deliverables

1. fork mode
2. named child routing
3. team abstractions
4. remote execution

## Recommended Near-Term Priority

If only a limited amount of work is done, prioritize these three:

1. managed background subagents
2. resume support
3. worktree isolation

These three deliver the biggest practical improvement for coding and research workflows.

## Final Recommendation

Ethos should not attempt to copy the entire Claude Code `AgentTool` in one pass.

That would create too much architecture churn at once.

The right path is:

1. keep the current simple `task` model intact
2. build a managed runtime around it
3. add persistence and resume
4. add isolation
5. only then consider fork mode and more advanced orchestration

This sequence keeps the codebase understandable while still moving Ethos toward the parts of Claude Code that matter most in practice.
