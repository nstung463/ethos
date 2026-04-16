# Frontend Research: Provider Profiles Upgrade
**Date:** 2026-04-13  
**Scope:** W:/panus/ethos/frontend/src/

---

## 1. Current Data Structures

### `UserApiKeys` — `types.ts:7-11`
```ts
type UserApiKeys = {
  openrouter: string;
  anthropic: string;
  openai: string;
};
```
Flat object. One key per provider. No concept of a named profile, base URL override, or per-profile model.

### `ModelInfo` — `types.ts:1-5`
```ts
type ModelInfo = { id: string; object: string; owned_by?: string; };
```
Thin — no provider tag, no display name, no grouping.

### `ChatThread` — `types.ts:36-44`
```ts
type ChatThread = {
  id: string; title: string;
  model: string;        // bare model ID string, e.g. "openai/gpt-4o-mini"
  mode: ComposerMode;
  messages: Message[];
  attachments: Attachment[];
  updatedAt: string;
};
```
`model` is an untyped string. No `provider` field. No `profileId` linking back to a saved profile.

### `EMPTY_API_KEYS` — `constants.ts:82-86`
Hard-coded sentinel: `{ openrouter: "", anthropic: "", openai: "" }`.  
No extensibility — adding a fourth provider (e.g. `gemini`) requires touching this constant AND every normalizer.

---

## 2. Key File:Line References

| Concern | File | Lines |
|---|---|---|
| `UserApiKeys` type | `types.ts` | 7–11 |
| `ModelInfo` type | `types.ts` | 1–5 |
| `ChatThread` type (model field) | `types.ts` | 36–44 |
| `EMPTY_API_KEYS` constant | `constants.ts` | 82–86 |
| `API_KEYS_STORAGE_KEY` | `constants.ts` | 5 |
| `STORAGE_KEY` (threads) | `constants.ts` | 3 |
| `loadApiKeys` / `saveApiKeys` | `utils/apiKeys.ts` | 17–36 |
| `normalizeApiKeys` (hard-coded fields) | `utils/apiKeys.ts` | 4–15 |
| `normalizeThread` (model string) | `utils/storage.ts` | 8–63 |
| `ApiKeysSettings` form (3 fields) | `components/settings/ApiKeysSettings.tsx` | 82–96 |
| `handleApiKeysSave` callback | `App.tsx` | 485–487 |
| `activeModel` derived value | `App.tsx` | 107 |
| `streamChat` metadata payload | `utils/stream.ts` | 5–7, 40–48 |
| `buildMetadata` (wraps apiKeys) | `utils/stream.ts` | 5–7 |
| Model displayed in Composer footer | `Composer.tsx` | 381, 386 |

---

## 3. API Key Storage

- **Key:** `ethos.frontend.api-keys.v1` (localStorage)
- **Format:** `JSON.stringify({ openrouter, anthropic, openai })`
- **Load path:** `loadApiKeys()` → `normalizeApiKeys()` → hard-codes exactly three fields (`utils/apiKeys.ts:10-14`)
- **Save path:** `saveApiKeys()` → same normalizer strips unknown fields
- **Threads storage key:** `ethos.frontend.threads.v2` (with fallback to `.v1`)

---

## 4. How Model Is Selected and Sent to Backend

### Selection flow
1. `App.tsx:75` — `fetchModels()` hits `GET /v1/models`, returns `ModelInfo[]`.
2. `App.tsx:79` — First model auto-selected as `landingModelId`.
3. `App.tsx:107` — `activeModel = activeThread?.model || landingModelId || models[0]?.id`
4. `Header` receives `selectedModelId` + `models[]` and calls back `handleModelChange` (`App.tsx:241-252`).
5. Model change writes to `thread.model` (string) or `landingModelId`.

### Transmission to backend
`utils/stream.ts:37-49` — `streamChat` POST body:
```json
{
  "model": "<model-id-string>",
  "messages": [...],
  "stream": true,
  "session_id": "<thread-id>",
  "file_ids": [...],
  "metadata": { "user_api_keys": { "openrouter": "...", "anthropic": "...", "openai": "..." } }
}
```
API keys ride inside `metadata.user_api_keys`. Same shape used in `postTask` for `/v1/tasks/title` and `/v1/tasks/follow-ups`.

---

## 5. Settings UI — Current Form

`ApiKeysSettings.tsx` renders exactly three labeled `<input type="password">` fields:
- OpenRouter API Key (`openrouter`)
- Anthropic API Key (`anthropic`)
- OpenAI API Key (`openai`)

State: `draftKeys: UserApiKeys` — a local copy edited before "Save Keys" flushes via `onSave(draftKeys)` callback to `App.tsx:handleApiKeysSave` which sets `apiKeys` state (auto-persisted to localStorage via `useEffect`).

`showKeys` state tracks per-provider visibility toggle (`ApiKeysSettings.tsx:13-17`).

---

## 6. Gaps and Issues for Provider Profile Upgrade

### G-1: No profile abstraction
There is no `ProviderProfile` type. Everything is a single flat `UserApiKeys` object. To support named profiles ("Work", "Personal"), a new type and storage slot are required.

### G-2: Hard-coded provider list
Provider names appear in at least four places that must all be updated together:
- `UserApiKeys` type (`types.ts:7-11`)
- `EMPTY_API_KEYS` (`constants.ts:82-86`)
- `normalizeApiKeys` field list (`apiKeys.ts:10-14`)
- `ApiKeysSettings` rendered inputs (`ApiKeysSettings.tsx:82-96`)
- `showKeys` state shape (`ApiKeysSettings.tsx:13-17`)

No single source of truth for the provider list.

### G-3: No per-profile base URL or custom endpoint
`UserApiKeys` only stores API key strings. Custom base URLs (e.g. a self-hosted OpenAI-compatible proxy) are not representable.

### G-4: `ChatThread.model` is an untyped string
No provider tag. If the same model ID exists on two providers, there is no way to distinguish which profile/provider was active for a thread. A profile upgrade likely needs `thread.provider` or `thread.profileId`.

### G-5: `ModelInfo` has no provider tag
`ModelInfo.owned_by` is optional and unused. The model list returned from `/v1/models` is untagged — grouping models by provider in a picker requires either API changes or client-side inference from model ID prefix.

### G-6: Storage versioning will be needed
`API_KEYS_STORAGE_KEY = "ethos.frontend.api-keys.v1"` — any schema change (profiles array) should bump to `v2` and include a migration path. `normalizeApiKeys` currently silently drops unknown fields.

### G-7: `metadata.user_api_keys` coupling
The backend receives the full `UserApiKeys` object on every request. Profiles would need a decision: send the whole active profile's key, or send a profile ID and let backend resolve? Current coupling in `buildMetadata` (`stream.ts:5-7`) needs updating.

### G-8: No active-profile selection state
`App.tsx` holds `apiKeys: UserApiKeys` as a single piece of state. A profiles system needs `activeProfileId: string` and `profiles: ProviderProfile[]` — and corresponding Header/Composer UI to switch profiles.

---

## 7. Unresolved Questions

1. **Profile scope:** Should a profile be selectable per-thread, or global for all threads?
2. **Backend contract:** Should the frontend send `metadata.user_api_keys` (current) or `metadata.profile_id` (requires backend profile store)?
3. **Model-to-provider mapping:** Should the frontend filter models by the active profile's provider, or show all models regardless?
4. **Storage migration:** Is a one-time migration of the existing flat `api-keys.v1` blob into a single "default" profile acceptable, or do we need a silent fallback?
5. **Daytona / OpenTerminal keys:** These are currently backend-only env vars. Should provider profiles eventually surface these in the frontend UI too?
