# OpenWebUI + Ethos Architecture

> **Status:** The product UI is now the **Ethos frontend** in [`frontend/`](../frontend/). This document remains as a reference for OpenWebUI-shaped API compatibility and for anyone still comparing that integration model.

This document explains the integration boundary between OpenWebUI, Ethos API, and Open Terminal (historical / alternative UI).

It exists to answer four questions quickly:

1. Which service owns what?
2. How do files and sandbox state flow through the system?
3. Which API routes are compatibility surfaces for the OpenWebUI frontend?
4. Which parts of OpenWebUI are intentionally bypassed?

## Summary

The current setup treats OpenWebUI as a frontend shell.

Ethos owns:

- chat model API at `/v1/*`
- managed files API at `/api/files/*`
- sandbox and terminal compatibility API at `/api/terminals/*`
- translation from OpenWebUI UI actions to Open Terminal backend calls

Open Terminal owns:

- actual sandbox filesystem
- terminal sessions
- process execution
- file tree under the sandbox root

OpenWebUI owns:

- chat UI
- file browser UI
- terminal UI
- rendering of streamed chat/tool output

OpenWebUI does not own sandbox or file state anymore.

## Ownership Boundaries

There are two file domains. Do not mix them.

### 1. Managed Files

Managed files are durable files known to Ethos.

Examples:

- uploaded documents
- files attached into chat
- published artifacts copied out of a sandbox

Managed files are served by Ethos at:

- `POST /api/files/`
- `GET /api/files/`
- `GET /api/files/{id}`
- `GET /api/files/{id}/content`
- `DELETE /api/files/{id}`

Storage:

- metadata index: `workspace/managed_files/index.json`
- binary content: `workspace/managed_files/files/`

Implementation:

- [api/routes/files.py](/W:/panus/ethos/api/routes/files.py)
- [api/services/file_store.py](/W:/panus/ethos/api/services/file_store.py)

### 2. Sandbox Files

Sandbox files live inside Open Terminal's runtime filesystem.

Examples:

- `/home/user/hello.py`
- generated outputs from commands
- temporary runtime state

Sandbox files are not managed files by default.

They are exposed to the UI through Ethos compatibility routes:

- `GET /api/terminals/{sandbox_id}/files/list`
- `GET /api/terminals/{sandbox_id}/files/read`
- `GET /api/terminals/{sandbox_id}/files/view`
- `POST /api/terminals/{sandbox_id}/files/upload`
- `POST /api/terminals/{sandbox_id}/files/mkdir`
- `DELETE /api/terminals/{sandbox_id}/files/delete`
- `POST /api/terminals/{sandbox_id}/files/move`

Implementation:

- [api/routes/terminals.py](/W:/panus/ethos/api/routes/terminals.py)

### 3. Promotion From Sandbox To Managed Files

If a sandbox file should become a durable file known to the app, Ethos must import it explicitly.

Route:

- `POST /api/files/import-from-sandbox`

This keeps the boundary clear:

- sandbox files are runtime state
- managed files are durable application state

## Current Request Flows

### Chat Flow

1. User types in OpenWebUI.
2. OpenWebUI calls `POST /v1/chat/completions` on Ethos.
3. Ethos runs the LangGraph agent.
4. If the agent uses sandbox-backed tools, those tools delegate into the backend implementation in `src/backends/*`.
5. Ethos streams OpenAI-compatible chunks back to OpenWebUI.
6. OpenWebUI renders the response.

Important:

- Chat requests should be considered Ethos-owned orchestration.
- OpenWebUI should not be the source of truth for tools, sandbox state, or file context injection.

### Managed File Upload Flow

1. User uploads a file from the UI.
2. OpenWebUI frontend calls `POST /api/files/` on Ethos.
3. Ethos stores file content in `workspace/managed_files/files/`.
4. Ethos records metadata in `workspace/managed_files/index.json`.
5. OpenWebUI receives a file record and uses that id for rendering or attaching.

### Sandbox File Browser Flow

1. User opens the Files tab while a terminal/sandbox is selected.
2. OpenWebUI frontend calls `/api/terminals/default/files/*` on Ethos.
3. Ethos proxies those calls to Open Terminal.
4. Open Terminal reads or mutates the real sandbox filesystem.
5. Ethos returns Open Terminal responses in a shape the OpenWebUI frontend already understands.

### Terminal Session Flow

1. OpenWebUI requests `POST /api/terminals/default/api/terminals`.
2. Ethos creates a session on Open Terminal.
3. OpenWebUI opens `WS /api/terminals/default/api/terminals/{session_id}` to Ethos.
4. Ethos forwards websocket traffic to Open Terminal.
5. Terminal I/O flows through Ethos, but the session itself lives in Open Terminal.

## Compatibility Surface For OpenWebUI

The OpenWebUI frontend was patched to prefer external files and terminal APIs.

Frontend switch points:

- [src/lib/constants.ts](/W:/panus/open-webui/src/lib/constants.ts)
- [src/lib/apis/files/index.ts](/W:/panus/open-webui/src/lib/apis/files/index.ts)
- [src/lib/apis/terminal/index.ts](/W:/panus/open-webui/src/lib/apis/terminal/index.ts)

Build-time frontend env:

- `PUBLIC_EXTERNAL_FILES_API_BASE_URL`
- `PUBLIC_EXTERNAL_TERMINALS_API_BASE_URL`
- `PUBLIC_EXTERNAL_SANDBOX_API_BASE_URL`
- `PUBLIC_DISABLE_PYODIDE_FILE_NAV`

Important:

- these `PUBLIC_*` variables are build-time values for the Svelte frontend
- changing them requires rebuilding the OpenWebUI image

Relevant files:

- [open-webui/Dockerfile](/W:/panus/open-webui/Dockerfile)
- [docker-compose.yml](/W:/panus/ethos/docker-compose.yml)

## What Is Intentionally Disabled Or Bypassed

The desired architecture is that OpenWebUI should not control sandbox or file semantics.

What the current implementation avoids:

- OpenWebUI built-in file storage as the source of truth
- browser-local Pyodide file navigation as the sandbox file browser
- direct assumption that `/mnt/uploads` is the authoritative filesystem

Current practical effect:

- OpenWebUI file previews and downloads use Ethos managed file routes
- OpenWebUI sandbox browser and terminal use Ethos compatibility routes
- Pyodide file nav is disabled when external terminals API is configured

## Service Map

### OpenWebUI

Container:

- `ethos-openwebui`

Purpose:

- build and serve the UI
- talk to Ethos for chat, files, and terminal/sandbox

### Ethos API

Container:

- `ethos-api`

Purpose:

- OpenAI-compatible chat API
- managed files API
- terminal compatibility API
- proxy/adapter layer for Open Terminal

### Open Terminal

Container:

- `ethos-open-terminal`

Purpose:

- real execution backend
- owns sandbox filesystem
- owns terminal sessions

## Route Reference

### Ethos chat routes

- `GET /v1/models`
- `POST /v1/chat/completions`

### Ethos managed file routes

- `POST /api/files/`
- `GET /api/files/`
- `GET /api/files/all`
- `GET /api/files/search`
- `POST /api/files/upload/dir`
- `POST /api/files/import-from-sandbox`
- `GET /api/files/{file_id}`
- `GET /api/files/{file_id}/content`
- `GET /api/files/{file_id}/content/html`
- `GET /api/files/{file_id}/process/status`
- `POST /api/files/{file_id}/data/content/update`
- `DELETE /api/files/{file_id}`

### Ethos terminal compatibility routes

- `GET /api/terminals/`
- `GET /api/terminals/{sandbox_id}/files/cwd`
- `POST /api/terminals/{sandbox_id}/files/cwd`
- `GET /api/terminals/{sandbox_id}/files/list`
- `GET /api/terminals/{sandbox_id}/files/read`
- `GET /api/terminals/{sandbox_id}/files/view`
- `POST /api/terminals/{sandbox_id}/files/upload`
- `POST /api/terminals/{sandbox_id}/files/mkdir`
- `DELETE /api/terminals/{sandbox_id}/files/delete`
- `POST /api/terminals/{sandbox_id}/files/move`
- `POST /api/terminals/{sandbox_id}/files/archive`
- `GET /api/terminals/{sandbox_id}/ports`
- `POST /api/terminals/{sandbox_id}/api/terminals`
- `WS /api/terminals/{sandbox_id}/api/terminals/{session_id}`

## Current Constraints

This integration is intentionally thin, but not complete.

Known constraints:

- terminal ownership is currently a single default sandbox id: `default`
- managed file storage currently uses a local JSON index, not a real DB
- sandbox identity is not yet bound to `chat_id`
- authorization is currently deployment-trust based, not a full user/session model

## Rebuild Rules

Rebuild `ethos-api` when:

- changing files under `api/`
- changing files under `src/`
- changing Python dependencies

Rebuild `openwebui` when:

- changing files under `open-webui/src/`
- changing `open-webui/Dockerfile`
- changing any `PUBLIC_*` frontend env values

Compose commands:

```powershell
docker compose build ethos-api openwebui
docker compose up -d ethos-api openwebui
```

## Where To Start Reading

If you are new to this stack, read in this order:

1. [docker-compose.yml](/W:/panus/ethos/docker-compose.yml)
2. [api/app.py](/W:/panus/ethos/api/app.py)
3. [api/routes/v1.py](/W:/panus/ethos/api/routes/v1.py)
4. [api/routes/files.py](/W:/panus/ethos/api/routes/files.py)
5. [api/routes/terminals.py](/W:/panus/ethos/api/routes/terminals.py)
6. [open-webui/src/lib/constants.ts](/W:/panus/open-webui/src/lib/constants.ts)

