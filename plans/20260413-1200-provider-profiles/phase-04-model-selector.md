# Phase 04 — Model Selector
**Date:** 2026-04-13  
**Priority:** P2 — final integration  
**Status:** Ready  
**Plan:** [plan.md](plan.md) | **Depends on:** [phase-02-backend-api.md](phase-02-backend-api.md), [phase-03-frontend-profiles-ui.md](phase-03-frontend-profiles-ui.md)

---

## Overview

Wire `profiles` + `activeProfileId` (from Phase 3) into the Header model dropdown and into
every request sent to the backend (Phase 2). Replace the `/v1/models` fetch with a
profiles-derived list. Store `profileId` on `ChatThread` (Phase 1 type). Handle the
fallback case where the active profile has been deleted.

---

## Key Insights

- The current model selection flow (research frontend §4) is:
  `GET /v1/models` → `setModels` → `landingModelId` → `activeModel` (`App.tsx:107`) →
  displayed in `Header` → written to `thread.model`.
  This entire chain is replaced by profiles.
- `streamChat` and `postTask` in `utils/stream.ts` pass `apiKeys: UserApiKeys` today
  (`stream.ts:5-7,40-48`). After this phase they accept `profile: ProviderProfile`.
- `Header` receives `selectedModelId: string` + `models: ModelInfo[]` and calls back
  `handleModelChange` (`App.tsx:241-252`). The new contract: `Header` receives
  `profiles: ProviderProfile[]` + `activeProfileId` and calls back `onProfileChange(id)`.
- `Composer.tsx:381,386` displays `activeModel` as text — after this phase it displays
  `activeProfile?.name ?? "No profile"`.
- `GET /v1/models` is still used to validate that the server is reachable (status check).
  Keep the fetch but stop using its result to populate the selector.
- When `profiles` is empty, the composer must show a prompt to add a profile rather than
  silently failing on send.

---

## Requirements

1. Header model dropdown replaced by a profile selector showing `profile.name` +
   provider badge. Same position, same visual weight.
2. `activeProfileId` in `App.tsx` drives both the Header display and the request metadata.
3. `streamChat` / `generateTitle` / `generateFollowUps` in `stream.ts` accept
   `profile: ProviderProfile` and build `metadata.profile` from it.
4. `metadata.user_api_keys` is no longer sent (or sent as empty `{}` for backward compat).
5. `ChatThread.profileId` is set to `activeProfileId` when a thread is created or when the
   first message is sent.
6. If the active profile is deleted between sessions, fall back to `profiles[0]?.id ?? ""`.
7. If `profiles` is empty, disable the send button and show "Add a profile in Settings".
8. `GET /v1/models` fetch is retained for the connectivity status check only.

---

## Architecture

### `buildMetadata` — `utils/stream.ts`

```ts
// Replace:
function buildMetadata(apiKeys: UserApiKeys) {
  return { user_api_keys: apiKeys };
}

// With:
function buildMetadata(profile: ProviderProfile) {
  return {
    profile: {
      provider: profile.provider,
      api_key:  profile.apiKey,
      model:    profile.model,
      base_url:   profile.baseUrl    ?? undefined,
      deployment: profile.deployment ?? undefined,
      api_version: profile.apiVersion ?? undefined,
    },
  };
}
```

### `streamChat` signature change — `utils/stream.ts:16-48`

```ts
// Replace `apiKeys: UserApiKeys` param with `profile: ProviderProfile`
// Update call site in App.tsx accordingly
export async function streamChat({
  model,   // still sent as request.model; backend ignores it when profile is present
  messages, modeInstruction, sessionId, fileIds,
  profile, // replaces apiKeys
  signal, onContent, onReasoning,
}: {
  ...
  profile: ProviderProfile;
  ...
}) {
  const body = JSON.stringify({
    model: profile.model,   // use profile.model as the request model string
    messages: ...,
    stream: true,
    session_id: sessionId,
    file_ids: fileIds,
    metadata: buildMetadata(profile),
  });
  ...
}
```

### `App.tsx` — model/profile state consolidation

```tsx
// Remove:
const [models, setModels]           = useState<ModelInfo[]>([]);
const [landingModelId, setLandingModelId] = useState("");
// Keep for connectivity check only — don't use result for selector
// const activeModel = activeThread?.model || landingModelId || models[0]?.id || "";

// New derived value:
const activeProfile = profiles.find(p => p.id === activeProfileId) ?? profiles[0] ?? null;

function handleProfileChange(profileId: string) {
  setActiveProfileId(profileId);
  if (activeThread) {
    updateThread(activeThread.id, { profileId });  // update thread's stored profile
  } else {
    setLandingProfileId(profileId);
  }
}
```

### Thread creation — `handleSend` in `App.tsx`

```tsx
// When creating a new thread or sending the first message:
const threadProfileId = activeThread?.profileId ?? activeProfileId;
const profile = profiles.find(p => p.id === threadProfileId) ?? activeProfile;
if (!profile) { /* show error */ return; }

// Pass profile to streamChat:
await streamChat({
  model: profile.model,
  profile,
  ...
});
```

### `Header` component props change

```tsx
// Old:
<Header selectedModelId={activeModel} models={models} onModelChange={handleModelChange} />

// New:
<Header
  profiles={profiles}
  activeProfileId={activeProfileId}
  onProfileChange={handleProfileChange}
/>
```

Inside `Header`, render a `<select>` or custom dropdown with `profile.name` options.
Keep the existing dropdown styling.

### `Composer.tsx` footer change — lines 381, 386

```tsx
// Old: displayed activeModel string
// New:
<span className="text-xs text-muted">{activeProfile?.name ?? "No profile"}</span>
```

### Fallback — deleted profile recovery — `App.tsx`

```tsx
// In the useEffect that loads profiles (or on every render):
useEffect(() => {
  if (profiles.length > 0 && !profiles.find(p => p.id === activeProfileId)) {
    setActiveProfileId(profiles[0].id);
  }
}, [profiles, activeProfileId]);
```

### Empty profiles guard — `Composer.tsx`

```tsx
const canSend = !!activeProfile && !isStreaming && inputValue.trim().length > 0;

// In the send button:
<button disabled={!canSend} title={!activeProfile ? "Add a profile in Settings first" : undefined}>
  Send
</button>
{!activeProfile && (
  <p className="text-xs text-amber-500">Add a provider profile in Settings to start chatting.</p>
)}
```

---

## Related Code Files

- `frontend/src/App.tsx:75-107` — `fetchModels`, `landingModelId`, `activeModel`
- `frontend/src/App.tsx:241-252` — `handleModelChange`
- `frontend/src/App.tsx:485-487` — `handleApiKeysSave` (replaced in Phase 3)
- `frontend/src/utils/stream.ts:5-7,16-48` — `buildMetadata`, `streamChat`
- `frontend/src/utils/stream.ts:110-162` — `generateTitle`, `generateFollowUps` (`postTask`)
- `frontend/src/components/Header.tsx` — model selector
- `frontend/src/components/Composer.tsx:381,386` — model display in footer
- `frontend/src/types.ts:1-5` — `ModelInfo` (no longer populated; type kept for connectivity check)

---

## Implementation Steps

1. Update `buildMetadata` in `stream.ts` to accept `ProviderProfile` and emit `metadata.profile`.
2. Update `streamChat` signature: `apiKeys` → `profile`; set `model: profile.model` in body.
3. Update `postTask` and `generateTitle` / `generateFollowUps` signatures similarly.
4. In `App.tsx`: remove `models`/`landingModelId` state (or reduce to connectivity-only);
   derive `activeProfile` from `profiles` + `activeProfileId`.
5. Rename `handleModelChange` → `handleProfileChange`; update thread `profileId` on change.
6. Update `handleSend` to pass `profile` instead of `apiKeys`.
7. Update `Header` props and internal dropdown to render profiles.
8. Update `Composer.tsx` footer to display `activeProfile.name`.
9. Add empty-profiles guard in `Composer.tsx` send button.
10. Add fallback `useEffect` to reset `activeProfileId` when active profile is deleted.
11. Remove remaining imports of `UserApiKeys`, `loadApiKeys`, `saveApiKeys`, `EMPTY_API_KEYS`.

---

## Todo

- [ ] Rewrite `buildMetadata` in `stream.ts`
- [ ] Update `streamChat` param: `apiKeys` → `profile`
- [ ] Update `postTask` / `generateTitle` / `generateFollowUps` params
- [ ] Refactor `App.tsx`: remove `models`/`landingModelId`, add `activeProfile` derived value
- [ ] Rename `handleModelChange` → `handleProfileChange` and update `ChatThread.profileId`
- [ ] Update `Header` component props + dropdown
- [ ] Update `Composer.tsx` footer label + empty-profiles guard
- [ ] Add fallback `useEffect` for deleted profile recovery
- [ ] Remove all remaining `UserApiKeys` / `loadApiKeys` / `EMPTY_API_KEYS` imports
- [ ] Verify `tsc --noEmit` passes

---

## Success Criteria

- Selecting a profile in Header changes `activeProfileId`; next message uses that profile's
  `apiKey` and `model` on the backend.
- `metadata.profile` appears in the network request payload (DevTools); `metadata.user_api_keys`
  is absent.
- Thread created with profile A still uses profile A's config even after switching to profile B
  in a new chat (because `thread.profileId` is stored).
- Deleting the active profile automatically selects the next available profile.
- When no profiles exist, the send button is disabled with a tooltip.
- `GET /v1/models` still fires on load for connectivity status; its result is not used for
  the selector dropdown.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| `Header` props change breaks other consumers | Low | `Header` is only used in `App.tsx` |
| Thread `profileId` drift (profile renamed/deleted) | Medium | Store profile snapshot on thread at creation? No — YAGNI; fallback to current active profile |
| `generateTitle` / `generateFollowUps` still pass `apiKeys` | Medium | Update in same PR; TypeScript will surface the mismatch |
| `Composer` still receives `activeModel` prop | Low | Remove prop; TypeScript compile error guides cleanup |

---

## Security Considerations

- `apiKey` travels in request body as plaintext. Identical security posture to current
  `user_api_keys` — no regression.
- `profile.apiKey` must not be logged in browser console. Remove any `console.log(profile)`.

---

## Next Steps

After Phase 4 merges, the `UserApiKeys` type and `utils/apiKeys.ts` can be deleted in a
cleanup PR. The `api-keys` section in `SettingsSection` can be removed. The `/v1/models`
endpoint can be repurposed to return server-side registry entries for advanced users.
