# Phase 01 — Data Model
**Date:** 2026-04-13  
**Priority:** P0 — all other phases depend on this  
**Status:** Ready  
**Plan:** [plan.md](plan.md)

---

## Overview

Introduce a `ProviderProfile` type on the frontend and extend the Python `ModelSpec` dataclass
with the same fields. Define the new localStorage schema (`ethos.frontend.profiles.v1`) and
the one-time migration from the old `ethos.frontend.api-keys.v1`. Add `profileId` to
`ChatThread` so threads remember which profile was active when they were created.

---

## Key Insights

- `UserApiKeys` (`types.ts:7-11`) and `EMPTY_API_KEYS` (`constants.ts:82-86`) are the only
  TypeScript sources of truth for the provider list; both must be replaced or deprecated.
- `normalizeApiKeys` (`utils/apiKeys.ts:4-15`) hard-codes three field names and silently
  drops anything else — it is a migration risk if we ever re-read old data after a schema change.
- `ChatThread.model` (`types.ts:39`) is an untyped `string`. Adding `profileId?: string` is
  additive and non-breaking; old threads without it fall back to the server default.
- `ModelSpec` (`src/config.py:80-87`) is a frozen dataclass with `{id, provider, model}`.
  Extending it with optional fields is backward-compatible with `get_model_registry()` since
  `json.loads` keys are mapped explicitly.
- The old `api-keys.v1` key must be read exactly once during migration, then deleted, so the
  migration never re-runs on subsequent loads.

---

## Requirements

1. New TypeScript type `ProviderProfile` with fields: `id`, `name`, `provider`,
   `apiKey`, `model`, and optionals `baseUrl`, `deployment`, `apiVersion`.
2. Provider enum restricted to: `openrouter | anthropic | openai | azure_openai | openai_compatible`.
3. New localStorage key `ethos.frontend.profiles.v1` storing `ProviderProfile[]`.
4. Migration: on load, if `profiles.v1` is absent but `api-keys.v1` exists, synthesise one
   profile per non-empty key in the old object, write to `profiles.v1`, delete `api-keys.v1`.
5. `ChatThread` gets optional `profileId?: string`.
6. `normalizeThread` (`utils/storage.ts:8-63`) must handle threads without `profileId` gracefully.
7. Python: `ModelSpec` extended with `base_url`, `api_version`, `deployment`, `extra_headers`
   — all optional with `None` defaults; frozen dataclass stays frozen.

---

## Architecture

### TypeScript — `frontend/src/types.ts`

```ts
export type ProviderType =
  | "openrouter"
  | "anthropic"
  | "openai"
  | "azure_openai"
  | "openai_compatible";

export type ProviderProfile = {
  id: string;           // uuid — stable across renames
  name: string;         // user-facing label e.g. "Work GPT-4o"
  provider: ProviderType;
  apiKey: string;
  model: string;        // e.g. "claude-opus-4-5", "openai/gpt-4o-mini"
  baseUrl?: string;     // openai_compatible or openrouter override
  deployment?: string;  // azure_openai deployment name
  apiVersion?: string;  // azure_openai api version
};

// Kept for migration only — do not use in new code
/** @deprecated use ProviderProfile */
export type UserApiKeys = { openrouter: string; anthropic: string; openai: string };

// Add to ChatThread:
export type ChatThread = {
  // ... existing fields ...
  model: string;        // kept for display; set from profile.model at creation
  profileId?: string;   // links back to ProviderProfile.id
};
```

### TypeScript — `frontend/src/constants.ts`

```ts
// Replace EMPTY_API_KEYS with:
export const PROFILES_STORAGE_KEY = "ethos.frontend.profiles.v1";
// Keep API_KEYS_STORAGE_KEY only for migration reads — mark deprecated
```

### TypeScript — `frontend/src/utils/profiles.ts` (new file)

```ts
import { PROFILES_STORAGE_KEY, API_KEYS_STORAGE_KEY } from "../constants";
import type { ProviderProfile } from "../types";
import { nanoid } from "nanoid"; // already in deps via uuid

function migrateFromApiKeys(): ProviderProfile[] {
  const raw = localStorage.getItem(API_KEYS_STORAGE_KEY);
  if (!raw) return [];
  try {
    const old = JSON.parse(raw) as Record<string, string>;
    const profiles: ProviderProfile[] = [];
    if (old.openrouter?.trim())
      profiles.push({ id: nanoid(), name: "OpenRouter", provider: "openrouter",
                      apiKey: old.openrouter, model: "openai/gpt-4o-mini" });
    if (old.anthropic?.trim())
      profiles.push({ id: nanoid(), name: "Anthropic", provider: "anthropic",
                      apiKey: old.anthropic, model: "claude-opus-4-5" });
    if (old.openai?.trim())
      profiles.push({ id: nanoid(), name: "OpenAI", provider: "openai",
                      apiKey: old.openai, model: "gpt-4o" });
    return profiles;
  } catch { return []; }
}

export function loadProfiles(): ProviderProfile[] {
  const raw = localStorage.getItem(PROFILES_STORAGE_KEY);
  if (!raw) {
    const migrated = migrateFromApiKeys();
    if (migrated.length > 0) {
      saveProfiles(migrated);
      localStorage.removeItem(API_KEYS_STORAGE_KEY);
    }
    return migrated;
  }
  try { return JSON.parse(raw) as ProviderProfile[]; }
  catch { return []; }
}

export function saveProfiles(profiles: ProviderProfile[]): void {
  localStorage.setItem(PROFILES_STORAGE_KEY, JSON.stringify(profiles));
}
```

### Python — `src/config.py`

```python
@dataclass(frozen=True)
class ModelSpec:
    id: str
    provider: str
    model: str
    base_url: str | None = None
    api_version: str | None = None
    deployment: str | None = None
    extra_headers: dict[str, str] | None = None
```

`get_model_registry()` continues mapping only `id/provider/model` from env JSON; the new
fields are populated only via per-request profile injection (Phase 2).

---

## Related Code Files

- `frontend/src/types.ts:7-11` — `UserApiKeys` (replaced)
- `frontend/src/types.ts:36-44` — `ChatThread` (add `profileId`)
- `frontend/src/constants.ts:5,82-86` — storage keys, `EMPTY_API_KEYS`
- `frontend/src/utils/apiKeys.ts` — fully superseded by `profiles.ts`
- `frontend/src/utils/storage.ts:8-63` — `normalizeThread` (add `profileId` passthrough)
- `src/config.py:80-87` — `ModelSpec` dataclass

---

## Implementation Steps

1. Edit `types.ts`: add `ProviderType`, `ProviderProfile`; add `profileId?` to `ChatThread`;
   mark `UserApiKeys` as `@deprecated` with JSDoc.
2. Edit `constants.ts`: add `PROFILES_STORAGE_KEY`; keep `API_KEYS_STORAGE_KEY` with `@deprecated`.
3. Create `utils/profiles.ts` with `loadProfiles`, `saveProfiles`, migration logic.
4. Edit `utils/storage.ts:normalizeThread` to pass through `profileId` when present.
5. Edit `src/config.py:ModelSpec` to add four optional fields with `None` defaults.

---

## Todo

- [ ] Add `ProviderType` union and `ProviderProfile` type to `types.ts`
- [ ] Add `profileId?: string` to `ChatThread` in `types.ts`
- [ ] Add `PROFILES_STORAGE_KEY` to `constants.ts`; deprecate `EMPTY_API_KEYS`
- [ ] Create `frontend/src/utils/profiles.ts` (loadProfiles, saveProfiles, migration)
- [ ] Update `utils/storage.ts:normalizeThread` to preserve `profileId`
- [ ] Extend `ModelSpec` in `src/config.py` with optional fields

---

## Success Criteria

- `loadProfiles()` returns migrated profiles when only old `api-keys.v1` key exists.
- After migration, `api-keys.v1` key is absent from localStorage.
- `ChatThread` objects without `profileId` still normalise correctly.
- `ModelSpec` construction without new fields is unchanged (no `TypeError`).
- Existing unit tests in `tests/` continue to pass.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| Migration double-runs on page reload | Low | `profiles.v1` written before `api-keys.v1` deleted |
| `nanoid` not available | Low | Use `crypto.randomUUID()` (available in modern browsers) |
| Old threads break after `profileId` added | Low | Field is optional; `normalizeThread` passes through unknown fields |

---

## Security Considerations

- API keys stored in `localStorage` are accessible to any JS on the origin. No change from
  current behaviour. Document that users should not use shared browsers.
- Do not log `apiKey` values anywhere in `profiles.ts`.

---

## Next Steps

After Phase 1 merges: begin Phase 2 (backend) and Phase 3 (Settings UI) in parallel.
