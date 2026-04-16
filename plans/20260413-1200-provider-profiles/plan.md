# Provider Profiles — Implementation Plan
**Date:** 2026-04-13  
**Status:** Ready for implementation  
**Priority:** High

---

## Problem

The frontend stores a flat `UserApiKeys` object (3 hardcoded providers, key-only).
The backend resolves model+provider from a server-side registry, accepting per-request keys only
for `openrouter`, `anthropic`, and `openai`. Neither side supports named profiles, custom base
URLs, Azure endpoints, or OpenAI-compatible proxies configurable from the UI.

## Goal

Replace `UserApiKeys` with a `ProviderProfile` system. Each profile is a complete LLM config
(provider + api key + model + optional base_url / deployment / api_version). Users CRUD profiles
in Settings; the active profile drives the model selector and is sent per-request to the backend.
The existing `ETHOS_MODEL` env-var flow is preserved as the server-side default.

---

## Phases

| # | Phase | Status | File |
|---|---|---|---|
| 1 | Data Model — TypeScript types, storage schema, Python dataclass, migration | Ready | [phase-01-data-model.md](phase-01-data-model.md) |
| 2 | Backend API — accept profile config per-request, extend `build_chat_model` | Ready | [phase-02-backend-api.md](phase-02-backend-api.md) |
| 3 | Frontend Profiles UI — `ProfilesSettings` component, CRUD, validation | Ready | [phase-03-frontend-profiles-ui.md](phase-03-frontend-profiles-ui.md) |
| 4 | Model Selector — wire profiles into Header dropdown, thread storage, request payload | Ready | [phase-04-model-selector.md](phase-04-model-selector.md) |

---

## Dependency Order

```
Phase 1 (types + storage)
  └── Phase 2 (backend accepts profile fields)     ← independent of Phase 3
  └── Phase 3 (Settings UI uses new types)         ← independent of Phase 2
        └── Phase 4 (selector + request wiring)   ← requires Phase 2 + 3
```

Phases 2 and 3 can be developed in parallel after Phase 1 merges.

---

## Key Constraints

- **No server-side profile store.** Profiles live in `localStorage` only; the full profile
  config is transmitted per-request inside `metadata.profile`.
- **Backward compatibility.** The `ETHOS_MODEL_REGISTRY` / `ETHOS_MODEL` env-var path must
  keep working. Per-request profile overrides it only when the frontend sends one.
- **YAGNI.** Daytona/OpenTerminal keys, multi-workspace profiles, and profile sharing are
  explicitly out of scope.
- **Storage migration.** Old `ethos.frontend.api-keys.v1` is migrated on first load into a
  single "Default" profile; the old key is then deleted.

---

## Supported Providers (in scope)

`openrouter` · `anthropic` · `openai` · `azure_openai` · `openai_compatible`

---

## Files Changed (overview)

**Frontend**  
`frontend/src/types.ts` · `frontend/src/constants.ts` · `frontend/src/utils/apiKeys.ts` (replaced by `profiles.ts`) · `frontend/src/utils/stream.ts` · `frontend/src/components/settings/ApiKeysSettings.tsx` (replaced by `ProfilesSettings.tsx`) · `frontend/src/App.tsx`

**Backend**  
`src/config.py` · `src/api/routes/v1.py` · `src/api/models/chat.py`
