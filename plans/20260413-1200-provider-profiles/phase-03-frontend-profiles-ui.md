# Phase 03 — Frontend Profiles UI
**Date:** 2026-04-13  
**Priority:** P1 — parallel with Phase 2  
**Status:** Ready  
**Plan:** [plan.md](plan.md) | **Depends on:** [phase-01-data-model.md](phase-01-data-model.md)

---

## Overview

Replace `ApiKeysSettings.tsx` with a new `ProfilesSettings` component that lets users create,
edit, and delete `ProviderProfile` objects. The form renders provider-specific fields
conditionally. Storage is handled by the new `utils/profiles.ts` module from Phase 1.
The `SettingsSection` type and the Settings page routing are updated to point to
the new component.

---

## Key Insights

- `ApiKeysSettings.tsx` currently renders exactly 3 password inputs (lines 82–96).
  It owns `draftKeys: UserApiKeys` state and calls back `onSave(draftKeys)` to `App.tsx:485`.
- `App.tsx` holds `apiKeys: UserApiKeys` state and persists it via `useEffect` — this state
  slot is replaced by `profiles: ProviderProfile[]` + `activeProfileId: string`.
- `SettingsSection` union (`types.ts:68-72`) includes `"api-keys"` — rename to `"profiles"`.
- The `showKeys` per-field visibility state (`ApiKeysSettings.tsx:13-17`) pattern is reused
  per profile's `apiKey` field in the edit form.
- Provider-specific fields to show/hide:
  - `openrouter`: `apiKey`, `baseUrl` (optional override)
  - `anthropic`: `apiKey`
  - `openai`: `apiKey`
  - `azure_openai`: `apiKey`, `deployment` (required), `apiVersion` (optional), `baseUrl` (endpoint URL, optional)
  - `openai_compatible`: `apiKey`, `baseUrl` (required)

---

## Requirements

1. `ProfilesSettings` component replaces `ApiKeysSettings` in `SettingsPage`.
2. Profile list view: shows all profiles as rows with name + provider badge + Edit / Delete buttons.
3. Profile form (inline or modal): fields `name`, `provider` (select), `apiKey`, `model`,
   and conditional `baseUrl` / `deployment` / `apiVersion`.
4. Validation per provider: `openai_compatible` requires `baseUrl`; `azure_openai` requires
   `deployment`; all require non-empty `apiKey` and `model`.
5. "Add Profile" opens an empty form; editing opens a pre-filled copy.
6. Delete prompts with inline confirm (no modal) — clicking Delete once shows "Confirm?" button.
7. `App.tsx` replaces `apiKeys` / `handleApiKeysSave` with `profiles` / `activeProfileId` state.
8. `SettingsSection` type adds `"profiles"`, removes `"api-keys"` (or keeps both for transition).

---

## Architecture

### `ProfilesSettings` component skeleton

```tsx
// frontend/src/components/settings/ProfilesSettings.tsx
type Props = {
  profiles: ProviderProfile[];
  activeProfileId: string;
  onSave: (profiles: ProviderProfile[], activeProfileId: string) => void;
};

export function ProfilesSettings({ profiles, activeProfileId, onSave }: Props) {
  const [draft, setDraft] = useState<ProviderProfile[]>(profiles);
  const [editing, setEditing] = useState<ProviderProfile | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  function handleSaveProfile(profile: ProviderProfile) {
    const next = draft.some(p => p.id === profile.id)
      ? draft.map(p => p.id === profile.id ? profile : p)
      : [...draft, profile];
    setDraft(next);
    setEditing(null);
    onSave(next, activeProfileId);
  }

  function handleDelete(id: string) {
    if (confirmDelete !== id) { setConfirmDelete(id); return; }
    const next = draft.filter(p => p.id !== id);
    const nextActive = id === activeProfileId ? (next[0]?.id ?? "") : activeProfileId;
    setDraft(next);
    setConfirmDelete(null);
    onSave(next, nextActive);
  }

  return (
    <div>
      {draft.map(p => <ProfileRow key={p.id} profile={p}
        isActive={p.id === activeProfileId}
        confirmDelete={confirmDelete === p.id}
        onEdit={() => setEditing({ ...p })}
        onDelete={() => handleDelete(p.id)} />)}
      <button onClick={() => setEditing(newEmptyProfile())}>Add Profile</button>
      {editing && <ProfileForm profile={editing} onSave={handleSaveProfile}
                               onCancel={() => setEditing(null)} />}
    </div>
  );
}
```

### `ProfileForm` — conditional fields

```tsx
function ProfileForm({ profile, onSave, onCancel }: { ... }) {
  const [form, setForm] = useState(profile);
  const [showKey, setShowKey] = useState(false);
  const errors = validateProfile(form);

  return (
    <form onSubmit={e => { e.preventDefault(); if (!errors) onSave(form); }}>
      <input value={form.name} onChange={...} placeholder="Profile name" />
      <select value={form.provider} onChange={e => setForm({...form, provider: e.target.value})}>
        {PROVIDER_OPTIONS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
      </select>
      <input value={form.model} onChange={...} placeholder="Model ID" />
      <div>
        <input type={showKey ? "text" : "password"} value={form.apiKey} onChange={...} />
        <button type="button" onClick={() => setShowKey(s => !s)}>show/hide</button>
      </div>
      {/* Conditional fields */}
      {(form.provider === "openai_compatible" || form.provider === "openrouter") && (
        <input value={form.baseUrl ?? ""} onChange={...} placeholder="Base URL" />
      )}
      {form.provider === "azure_openai" && (<>
        <input value={form.deployment ?? ""} onChange={...} placeholder="Deployment name" />
        <input value={form.apiVersion ?? ""} onChange={...} placeholder="API version" />
        <input value={form.baseUrl ?? ""} onChange={...} placeholder="Azure endpoint URL (optional)" />
      </>)}
      {errors && <p className="text-red-500">{errors}</p>}
      <button type="submit" disabled={!!errors}>Save</button>
      <button type="button" onClick={onCancel}>Cancel</button>
    </form>
  );
}
```

### Validation helper

```ts
function validateProfile(p: ProviderProfile): string | null {
  if (!p.name.trim()) return "Name is required";
  if (!p.model.trim()) return "Model is required";
  if (!p.apiKey.trim()) return "API key is required";
  if (p.provider === "openai_compatible" && !p.baseUrl?.trim())
    return "Base URL is required for OpenAI-compatible provider";
  if (p.provider === "azure_openai" && !p.deployment?.trim())
    return "Deployment name is required for Azure OpenAI";
  return null;
}
```

### `App.tsx` state changes

```tsx
// Remove:
const [apiKeys, setApiKeys] = useState<UserApiKeys>(loadApiKeys);
// Replace with:
const [profiles, setProfiles]         = useState<ProviderProfile[]>(loadProfiles);
const [activeProfileId, setActiveProfileId] = useState<string>(
  () => loadProfiles()[0]?.id ?? ""
);

// Remove handleApiKeysSave; add:
function handleProfilesSave(nextProfiles: ProviderProfile[], nextActiveId: string) {
  setProfiles(nextProfiles);
  setActiveProfileId(nextActiveId);
  saveProfiles(nextProfiles);
}
```

### `SettingsSection` update — `types.ts:68-72`

```ts
export type SettingsSection =
  | "general"
  | "appearance"
  | "profiles"          // replaces "api-keys"
  | "model-settings"
  | "security";
```

---

## Related Code Files

- `frontend/src/components/settings/ApiKeysSettings.tsx:13-17,82-96` — replaced
- `frontend/src/App.tsx:485-487` — `handleApiKeysSave` (replaced by `handleProfilesSave`)
- `frontend/src/types.ts:7-11,68-72` — `UserApiKeys` (deprecated), `SettingsSection`
- `frontend/src/constants.ts:82-86` — `EMPTY_API_KEYS` (unused after this phase)
- `frontend/src/components/SettingsPage.tsx` — routes to new `ProfilesSettings`

---

## Implementation Steps

1. Create `frontend/src/components/settings/ProfilesSettings.tsx` with list + form.
2. Create `newEmptyProfile()` helper in `utils/profiles.ts`.
3. Add `PROVIDER_OPTIONS` constant (label/value pairs for the `<select>`).
4. Replace `ApiKeysSettings` import in `SettingsPage.tsx` with `ProfilesSettings`.
5. Update `types.ts:SettingsSection` to include `"profiles"`.
6. Refactor `App.tsx`: remove `apiKeys`/`saveApiKeys`/`handleApiKeysSave`; add `profiles`/`activeProfileId`.
7. Pass `profiles` and `activeProfileId` down to `ProfilesSettings` via `SettingsPage`.
8. Remove `EMPTY_API_KEYS` usage outside `apiKeys.ts`; leave the file in place but unused
   (Phase 4 removes the final import).

---

## Todo

- [ ] Create `ProfilesSettings.tsx` (list view + form)
- [ ] Create `ProfileForm` sub-component with conditional provider fields
- [ ] Add `validateProfile()` utility
- [ ] Add `newEmptyProfile()` to `utils/profiles.ts`
- [ ] Add `PROVIDER_OPTIONS` constant to `constants.ts` or `profiles.ts`
- [ ] Update `SettingsPage.tsx` to render `ProfilesSettings`
- [ ] Update `types.ts:SettingsSection` (`"api-keys"` → `"profiles"`)
- [ ] Refactor `App.tsx` state: `apiKeys` → `profiles` + `activeProfileId`

---

## Success Criteria

- User can add a profile for each of the 5 provider types and save.
- `openai_compatible` profile without `baseUrl` shows a validation error and cannot be saved.
- `azure_openai` profile without `deployment` shows a validation error.
- Old `api-keys.v1` data is visible as migrated profiles on first load.
- Deleting a profile that is `activeProfileId` sets `activeProfileId` to the next profile.
- No TypeScript compile errors (`tsc --noEmit`).

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| `SettingsSection` rename breaks router/nav links | Medium | Search for all `"api-keys"` string refs in `SettingsPage`, `Header`, `Sidebar` |
| Stale `apiKeys` prop still passed somewhere | Medium | Remove `apiKeys` from App state; let TypeScript errors surface missing cleanups |
| Profile form state reset on parent re-render | Low | `editing` state lives in `ProfilesSettings`, not App |

---

## Security Considerations

- `apiKey` rendered in `<input type="password">` by default; toggle to text only on explicit
  user action (`showKey` state).
- Never display `apiKey` in the profile list row.
- `saveProfiles` stores keys in `localStorage` — same risk as current `saveApiKeys`.

---

## Next Steps

Phase 4 consumes `profiles` and `activeProfileId` from `App.tsx` state to power the model
selector dropdown and include the active profile in every request.
