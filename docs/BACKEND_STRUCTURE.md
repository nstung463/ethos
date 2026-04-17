# Backend Structure

Ethos backend is now organized around a scalable application layout:

```text
src/app/
  bootstrap.py            # FastAPI factory and lifecycle
  router.py               # top-level router assembly
  dependencies.py         # shared FastAPI dependencies
  core/                   # settings, logging, shared runtime concerns
  modules/
    chat/                 # chat completions and metadata tasks
    files/                # managed file APIs
    terminals/            # sandbox terminal proxy APIs
  services/               # cross-module service layer
```

`src/app` is the application boundary.
New features should be added as modules instead of introducing a second HTTP tree.

Recommended next modules:

- `src/app/modules/auth`
- `src/app/modules/users`
- `src/app/modules/billing`
- `src/app/modules/marketing`
- `src/app/modules/admin`

Business module examples now exist as scaffolds:

- `auth`
- `users`
- `payments`
- `marketing`
- `admin`

Module template:

```text
src/app/modules/<domain>/
  router.py
  schemas.py
  service.py
  repository.py   # when persistence starts
  policy.py       # authz/rules when needed
```

Migration strategy:

1. Add or extend one domain at a time under `src/app/modules/*`.
2. Introduce database/repository code only inside the target module.
3. Keep cross-cutting infra in `src/app/core` or `src/app/services`.

AI runtime structure should evolve separately under `src/ai/` so business APIs
and agent internals do not keep mixing together.

Canonical AI paths after the current migration:

- `src/ai/agents/ethos.py`
- `src/ai/agents/subagents.py`
- `src/ai/prompts/catalog.py`
- `src/ai/middleware/*`
- `src/ai/tools/*`
