# Phase 02 — Backend API
**Date:** 2026-04-13  
**Priority:** P1 — parallel with Phase 3  
**Status:** Ready  
**Plan:** [plan.md](plan.md) | **Depends on:** [phase-01-data-model.md](phase-01-data-model.md)

---

## Overview

Extend the backend to accept a full provider profile config per-request inside
`metadata.profile` and use it to build the LLM client. This replaces the narrow
`metadata.user_api_keys` whitelist (3 providers) with a structured profile object that
covers `azure_openai` endpoints and arbitrary `openai_compatible` base URLs. The existing
env-var model registry path is untouched; the profile is an additive override.

---

## Key Insights

- `_extract_user_api_keys` (`src/api/routes/v1.py:118-129`) hard-codes the provider whitelist
  (`openrouter`, `anthropic`, `openai`) and ignores `azure_openai` endpoint / `base_url`.
- `build_chat_model` (`src/config.py:113-154`) has three dispatch paths. The `openai_compatible`
  escape hatch is missing: any provider not in `OPENAI_COMPATIBLE_PROVIDERS` falls to the
  native path, which fails for arbitrary base URLs.
- `ModelSpec` (`src/config.py:80-87`) has no `base_url`, `api_version`, or `deployment`. These
  must be added (Phase 1) before `build_chat_model` can consume them.
- `ChatRequest` uses `extra="allow"` (Pydantic), so `metadata` already accepts arbitrary dicts;
  no schema change is strictly required, but a typed `ProfilePayload` TypedDict improves safety.
- Azure's `AzureChatOpenAI` (via `init_chat_model("azure_openai:...")`) accepts `azure_endpoint`
  and `api_version` as constructor kwargs — passable through `init_chat_model`.
- The `REQUEST_API_KEY_FIELDS` dict (`src/config.py:72-77`) is a parallel mapping that becomes
  redundant once `build_chat_model` accepts a full profile dict; it can be kept for backward
  compat but bypassed on the profile path.

---

## Requirements

1. `metadata.profile` (optional) accepted alongside (and taking priority over) `metadata.user_api_keys`.
2. Profile shape mirrors `ProviderProfile` from Phase 1:
   `provider`, `api_key`, `model`, `base_url?`, `deployment?`, `api_version?`.
3. New provider `openai_compatible` routes through the OpenAI-compatible path using the
   profile's `base_url` (required for this provider type) and `api_key`.
4. `azure_openai` profile can specify `deployment`, `api_version`, `api_key`, and optionally
   `base_url` (Azure endpoint URL).
5. When `metadata.profile` is present and valid, it bypasses the registry lookup: the backend
   uses `profile.model` directly, ignoring `request.model` registry resolution.
6. When `metadata.profile` is absent, existing `_resolve_model_id` + `_extract_user_api_keys`
   path is used unchanged — full backward compatibility.
7. No server-side profile storage. Profiles are stateless per-request.

---

## Architecture

### New helper — `src/api/routes/v1.py`

```python
# Typed dict for the profile payload received from the frontend
from typing import TypedDict

class ProfilePayload(TypedDict, total=False):
    provider: str       # required
    api_key: str        # required
    model: str          # required
    base_url: str       # openai_compatible / azure endpoint
    deployment: str     # azure_openai deployment name
    api_version: str    # azure_openai api version

def _extract_profile(request: ChatRequest) -> ProfilePayload | None:
    metadata = request.metadata or {}
    raw = metadata.get("profile")
    if not isinstance(raw, dict):
        return None
    provider = str(raw.get("provider", "")).strip().lower()
    model    = str(raw.get("model", "")).strip()
    api_key  = str(raw.get("api_key", "")).strip()
    if not provider or not model:
        return None   # malformed — fall back to registry path
    return ProfilePayload(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=str(raw.get("base_url", "")).strip() or None,
        deployment=str(raw.get("deployment", "")).strip() or None,
        api_version=str(raw.get("api_version", "")).strip() or None,
    )
```

### Extended `build_chat_model` — `src/config.py`

```python
def build_chat_model(
    provider: str,
    model_name: str,
    *,
    api_keys: Mapping[str, str] | None = None,
    # New optional profile-level overrides (populated from per-request profile):
    base_url: str | None = None,
    api_version: str | None = None,
    deployment: str | None = None,
) -> BaseChatModel:
    provider = PROVIDER_ALIASES.get(provider.strip().lower(), provider.strip().lower())

    # NEW: openai_compatible escape hatch — custom base_url from profile
    if provider == "openai_compatible":
        if not base_url:
            raise ValueError("openai_compatible provider requires base_url")
        kwargs = {"base_url": base_url, "temperature": 0.0}
        if api_keys:
            api_key = api_keys.get("api_key") or api_keys.get("openai", "")
            if api_key:
                kwargs["api_key"] = api_key
        return init_chat_model(f"openai:{model_name}", **kwargs)

    if provider in OPENAI_COMPATIBLE_PROVIDERS:
        conf = OPENAI_COMPATIBLE_PROVIDERS[provider]
        resolved_base = base_url or os.getenv(conf["base_url_env"], conf["base_url"])
        request_key = resolve_request_api_key(provider, api_keys)
        api_key = request_key or os.getenv(conf["api_key_env"], "")
        kwargs = {"base_url": resolved_base, "temperature": 0.0}
        if api_key:
            kwargs["api_key"] = api_key
        return init_chat_model(f"openai:{model_name}", **kwargs)

    if provider == "azure_openai":
        resolved_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION") \
                           or os.getenv("OPENAI_API_VERSION") or "2024-12-01-preview"
        kwargs = {"temperature": 0.0, "api_version": resolved_version}
        if base_url:                     # azure endpoint URL
            kwargs["azure_endpoint"] = base_url
        if deployment:
            kwargs["azure_deployment"] = deployment
        request_key = resolve_request_api_key(provider, api_keys)
        if request_key:
            kwargs["api_key"] = request_key
        return init_chat_model(f"azure_openai:{model_name}", **kwargs)

    # native providers (anthropic, openai, google_genai, …) — unchanged
    ...
```

### Route handler change — `src/api/routes/v1.py:chat_completions`

```python
async def chat_completions(request: ChatRequest, ...):
    profile = _extract_profile(request)

    if profile:
        # Profile path: bypass registry; build model directly from profile fields
        provider = profile["provider"]
        model_name = profile["model"]
        llm = build_chat_model(
            provider, model_name,
            api_keys={"api_key": profile.get("api_key", "")},
            base_url=profile.get("base_url"),
            api_version=profile.get("api_version"),
            deployment=profile.get("deployment"),
        )
    else:
        # Existing registry path — unchanged
        model_id = _resolve_model_id(request.model)
        spec = registry[model_id]
        user_api_keys = _extract_user_api_keys(request)
        llm = build_chat_model(spec.provider, spec.model, api_keys=user_api_keys)

    agent = create_ethos_agent(model=llm, backend=backend)
    ...
```

---

## Related Code Files

- `src/api/routes/v1.py:28-40` — `_resolve_model_id`
- `src/api/routes/v1.py:118-129` — `_extract_user_api_keys` (kept; only bypassed when profile present)
- `src/config.py:72-77` — `REQUEST_API_KEY_FIELDS`
- `src/config.py:113-154` — `build_chat_model` (extended)
- `src/config.py:80-87` — `ModelSpec` (extended in Phase 1)
- `src/api/models/chat.py` — `ChatRequest` (`metadata: dict | None`)

---

## Implementation Steps

1. After Phase 1, confirm `ModelSpec` has the new optional fields in `src/config.py`.
2. Add `_extract_profile()` to `src/api/routes/v1.py` below `_extract_user_api_keys`.
3. Extend `build_chat_model` signature with `base_url`, `api_version`, `deployment` kwargs.
4. Add `openai_compatible` dispatch block at the top of `build_chat_model` (before the
   `OPENAI_COMPATIBLE_PROVIDERS` check).
5. Pass `base_url` / `api_version` / `deployment` through existing `azure_openai` branch.
6. Update `chat_completions` handler to call `_extract_profile` and branch accordingly.
7. Update `generate_title_task` and `generate_follow_ups_task` in
   `src/api/services/chat_tasks.py` if they also call `build_chat_model` directly.

---

## Todo

- [ ] Add `_extract_profile()` to `src/api/routes/v1.py`
- [ ] Extend `build_chat_model` with `base_url`, `api_version`, `deployment` params
- [ ] Add `openai_compatible` dispatch branch in `build_chat_model`
- [ ] Thread profile kwargs through `azure_openai` branch in `build_chat_model`
- [ ] Branch `chat_completions` on `profile` vs registry path
- [ ] Add tests: `test_v1_route_helpers.py` — `_extract_profile` for each provider type
- [ ] Add tests: `test_config.py` — `build_chat_model` with `openai_compatible` and azure overrides

---

## Success Criteria

- `POST /v1/chat/completions` with `metadata.profile = {provider:"anthropic", api_key:"sk-...", model:"claude-opus-4-5"}` routes through the Anthropic native path.
- Same endpoint with `provider:"openai_compatible", base_url:"https://my-proxy/v1", model:"gpt-4o"` uses the custom base URL.
- Existing request without `metadata.profile` continues to use registry resolution.
- `ETHOS_MODEL` / `ETHOS_MODEL_REGISTRY` env vars still drive `GET /v1/models` response.
- No regression in existing `tests/test_v1_route_helpers.py`.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| `azure_endpoint` kwarg rejected by current langchain-openai | Medium | Verify against installed version; fall back to env-var if kwarg unsupported |
| `init_chat_model("openai:...")` ignores `base_url` on some versions | Low | Test with pinned version; use `ChatOpenAI(base_url=...)` directly if needed |
| Profile with wrong provider crashes agent mid-stream | Medium | Validate `provider` enum in `_extract_profile`; return 400 for unknown provider |

---

## Security Considerations

- `api_key` from the profile is used directly and never logged. Add a `log.debug` guard:
  `logger.debug("profile provider=%s model=%s", provider, model_name)` — no key in log.
- Per-request keys are transmitted in plaintext over HTTP between frontend and backend.
  Ensure TLS in production; document in deployment guide.
- `openai_compatible` with arbitrary `base_url` could be pointed at internal network hosts.
  Accept risk for now (operator-controlled deployment); document in CLAUDE.md.

---

## Next Steps

After Phase 2: Phase 4 wires the frontend to send `metadata.profile`.
After Phase 3: Phase 4 renders profile selector in Header.
