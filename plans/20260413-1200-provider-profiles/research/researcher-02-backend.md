# Backend Research: Provider Profiles Upgrade
**Date:** 2026-04-13  
**Scope:** src/api/, src/config.py, src/graph.py, main.py

---

## 1. Request Schema (src/api/models/chat.py)

`ChatRequest` (Pydantic, `extra="allow"`) carries:

| Field | Type | Notes |
|---|---|---|
| `model` | `str` | Registry model ID (e.g. `"ethos"`, `"ethos-azure"`) |
| `messages` | `list[Message]` | OpenAI-compatible |
| `stream` | `bool` | SSE streaming flag |
| `session_id` / `chat_id` | `str \| None` | Thread identity |
| `file_ids` / `files` | lists | Attachment references |
| `metadata` | `dict \| None` | Catch-all: carries `user_api_keys`, `session_id`, `file_ids` |

**Provider/model are NOT first-class request fields.** The client sends a `model` string that maps to a `ModelSpec` (id → provider + model) via the server-side registry. Per-request API keys are passed through `metadata.user_api_keys`.

---

## 2. Model Resolution Path

```
POST /v1/chat/completions
  → ChatRequest.model  (registry ID, e.g. "ethos")
  → _resolve_model_id()           # validates against get_model_registry()
  → registry lookup: ModelSpec { id, provider, model }
  → _extract_user_api_keys()      # reads metadata.user_api_keys.{openrouter,anthropic,openai}
  → build_chat_model(spec.provider, spec.model, api_keys=user_api_keys)
  → create_ethos_agent(model=model, backend=backend)
```

`get_model_registry()` reads `ETHOS_MODEL_REGISTRY` (JSON array) or falls back to
`ETHOS_PROVIDER` + `ETHOS_MODEL` env vars producing a single `ModelSpec(id="ethos")`.

---

## 3. LLM Client Construction (src/config.py → build_chat_model)

Three code paths:

### 3a. OpenAI-compatible third-party (openrouter, deepseek, together, groq, xai, fireworks, perplexity)
```python
base_url = os.getenv(conf["base_url_env"], conf["base_url"])
api_key  = request_api_key or os.getenv(conf["api_key_env"], "")
return init_chat_model(f"openai:{model_name}", base_url=base_url, api_key=api_key, temperature=0.0)
```
`base_url` is overridable per-provider via env var (`OPENROUTER_BASE_URL`, etc.).

### 3b. Azure OpenAI
```python
api_version = os.getenv("AZURE_OPENAI_API_VERSION") or os.getenv("OPENAI_API_VERSION") or "2024-12-01-preview"
return init_chat_model(f"azure_openai:{model_name}", api_version=api_version, temperature=0.0)
```
Falls through to LangChain's `langchain-openai` AzureChatOpenAI, which reads
`AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY` from environment.

### 3c. Native providers (anthropic, openai, google_genai, bedrock, etc.)
```python
return init_chat_model(f"{provider}:{model_name}", temperature=0.0, **optional_api_key)
```
LangChain resolves credentials from standard env vars.

**PROVIDER_ALIASES** map: `gemini→google_genai`, `google→google_genai`, `amazon/bedrock→bedrock`, `azure→azure_openai`.

**REQUEST_API_KEY_FIELDS** (what per-request keys are accepted):  
`openrouter`, `anthropic`, `openai`, `azure_openai` → field names in `metadata.user_api_keys`.

---

## 4. Agent Construction (src/graph.py → create_ethos_agent)

```python
def create_ethos_agent(root_dir=None, backend=None, model=None):
    if model is None:
        model = get_model()        # reads env, no request context
    ...
    return create_agent(model=model, tools=..., system_prompt=..., middleware=..., checkpointer=MemorySaver())
```

The `model` object is the fully-constructed `BaseChatModel`. The agent factory is
**stateless with respect to provider config** — it accepts a ready-made model object.
A new agent is created per request in `chat_completions`.

---

## 5. Where Provider Profile Config Would Be Injected

There are two clean injection points:

### A. Registry layer (src/config.py → ModelSpec / get_model_registry)
`ModelSpec` currently holds `{id, provider, model}`. A profile concept maps here:
add profile fields (e.g. `base_url`, `api_key_env`, `api_version`, `temperature`, `extra_kwargs`)
to `ModelSpec` and pass them into `build_chat_model`.

### B. Per-request override (metadata.user_api_keys → _extract_user_api_keys)
Currently only `openrouter`, `anthropic`, `openai` are whitelisted. Azure and custom
endpoints are absent. Extending the whitelist or generalising to accept `base_url` and
`api_key` per-request would be the runtime injection point.

---

## 6. Gaps for Azure / Custom Endpoint Support

| Gap | Location | Detail |
|---|---|---|
| Azure endpoint not per-request | `REQUEST_API_KEY_FIELDS` | `azure_openai` listed but `AZURE_OPENAI_ENDPOINT` is always env-only; no way to override endpoint at request time |
| Custom base_url per registry entry | `ModelSpec` | No `base_url` field; only the hardcoded map in `OPENAI_COMPATIBLE_PROVIDERS` supplies URLs |
| Per-profile api_version | `build_chat_model` | Azure `api_version` is env-global; can't differ between two azure registry entries |
| Arbitrary OpenAI-compatible provider | `OPENAI_COMPATIBLE_PROVIDERS` | Must be in the hardcoded dict; no "custom openai-compatible" escape hatch from registry |
| Per-profile temperature / extra kwargs | `build_chat_model` | Hardcoded `temperature=0.0`; profile would need to carry these |
| Missing deepseek/groq/etc in per-request keys | `REQUEST_API_KEY_FIELDS` | Only openrouter/anthropic/openai accepted; groq, deepseek, xai, fireworks not whitelisted |

---

## 7. Data Flow Summary

```
.env / ETHOS_MODEL_REGISTRY
       │
       ▼
get_model_registry() → list[ModelSpec]      # server startup + per-request
       │
       ▼
_resolve_model_id(request.model)            # validates model ID
       │
       ▼
build_chat_model(spec.provider, spec.model, api_keys=user_api_keys)
  ├─ OPENAI_COMPATIBLE_PROVIDERS dict       # base_url lookup
  ├─ azure_openai branch                    # api_version from env
  └─ init_chat_model(provider:model, ...)   # LangChain constructs client
       │
       ▼
create_ethos_agent(model=llm, backend=backend)  # LangGraph agent
       │
       ▼
StreamingResponse / ainvoke
```

---

## 8. Unresolved Questions

1. **Profile storage** — should profiles live in env-only (`ETHOS_MODEL_REGISTRY` extension), in a DB, or in a config file? The current system is entirely env-driven with no persistence layer.
2. **Per-request Azure endpoint** — `AzureChatOpenAI` (LangChain) reads `AZURE_OPENAI_ENDPOINT` at construction; passing it as a kwarg via `init_chat_model` needs verification against current langchain-openai version.
3. **Thread/session model affinity** — `create_ethos_agent` is called per request; `MemorySaver` is ephemeral. If a profile changes mid-session, conversation state is not migrated.
4. **Secret management** — per-request `user_api_keys` are transmitted in `metadata` plaintext; profiles stored server-side would need a secrets strategy.
5. **Frontend model selector** — the `/v1/models` response only exposes `spec.id`; provider/model details are hidden. Profile names exposed here need a UX decision on display vs. internal naming.
