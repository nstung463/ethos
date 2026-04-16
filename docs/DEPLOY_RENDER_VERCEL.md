# Ethos v1 Deployment: Render + Vercel

This is the simplest production-style deployment path for the current Ethos stack:

- **Backend**: Render Web Service
- **Frontend**: Vercel

It matches the current codebase structure:

- FastAPI backend from the repository root
- Vite frontend from `frontend/`

## Architecture

```text
Vercel (frontend)
  -> VITE_API_BASE_URL=https://your-backend.onrender.com
  -> calls /v1/models, /v1/chat/completions, /api/files/*

Render (backend)
  -> runs Dockerfile at repo root
  -> serves FastAPI on PORT or 8080
  -> reads model config from environment variables
```

## Before You Start

You need:

- A GitHub repo containing this project
- A Render account
- A Vercel account
- Required backend secrets such as `DAYTONA_API_KEY`

Important current behavior:

- The frontend can store user API keys locally in the browser and send them per request.
- The backend still needs a model catalog configured through environment variables so `/v1/models` returns at least one model.

## Backend on Render

### 1. Create the service

In Render:

1. Click `New`
2. Choose `Web Service`
3. Connect your GitHub repo
4. Select the branch to deploy, usually `main`

### 2. Fill the service settings

Recommended values:

- `Name`: `ethos-api`
- `Language`: `Docker`
- `Root Directory`: empty
- `Region`: nearest to your users
- `Instance Type`: `Free` for v1, paid if you need no sleep

Advanced settings:

- `Health Check Path`: `/v1/models`
- `Docker Build Context Directory`: `.`
- `Dockerfile Path`: `./Dockerfile`
- `Docker Command`: leave empty
- `Pre-Deploy Command`: leave empty
- `Auto-Deploy`: `On Commit`

Notes:

- The app now reads `PORT` from Render automatically and falls back to `8080` locally.
- Render free instances spin down after inactivity and can take roughly 50-60 seconds to wake up.

### 3. Add environment variables

Minimum required environment variables:

```text
ETHOS_RELOAD=false
LOG_LEVEL=INFO
DAYTONA_API_KEY=your_daytona_key
```

Then configure the model catalog using one of these approaches.

#### Option A: Single model

```text
ETHOS_PROVIDER=openrouter
ETHOS_MODEL=openai/gpt-4o-mini
```

#### Option B: Multiple models

```json
ETHOS_MODEL_REGISTRY=[
  {"id":"ethos-openrouter","provider":"openrouter","model":"anthropic/claude-3.7-sonnet"},
  {"id":"ethos-openai","provider":"openai","model":"gpt-4o-mini"}
]
```

Optional fallback provider keys:

```text
OPENROUTER_API_KEY=...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

Use those if you want the backend to keep working even when the user has not entered their own key in the UI.

### 4. Deploy and verify

Click `Create Web Service` and wait for the deploy to complete.

After the service is live, open:

```text
https://your-service.onrender.com/v1/models
```

Expected result:

- HTTP `200`
- JSON response with a `data` array of models

If `/v1/models` fails, check:

- `DAYTONA_API_KEY`
- `ETHOS_MODEL_REGISTRY` JSON formatting
- `ETHOS_PROVIDER` / `ETHOS_MODEL`
- `Dockerfile Path`

## Frontend on Vercel

### 1. Create the frontend project

In Vercel:

1. Click `New Project`
2. Import the same GitHub repo
3. Override the auto-detected preset if Vercel guesses the backend instead of the frontend

### 2. Fill the project settings

Use these values:

- `Project Name`: `ethos-frontend`
- `Framework Preset`: `Vite`
- `Root Directory`: `frontend`
- `Build Command`: `npm run build`
- `Output Directory`: `dist`
- `Install Command`: `npm install`

### 3. Add the frontend environment variable

Set:

```text
VITE_API_BASE_URL=https://your-service.onrender.com
```

This is the variable used by the frontend in `frontend/src/constants.ts`.

### 4. Deploy and verify

After deployment, Vercel will give you a URL like:

```text
https://your-project.vercel.app
```

Test the app in this order:

1. Open the frontend
2. Confirm the chat page loads
3. Confirm the model selector populates
4. Open `Settings > API Keys`
5. Enter a provider key
6. Send a test message

## User API Keys in Production

Current behavior:

- API keys entered in the UI are stored in browser `localStorage`
- The frontend sends them in request metadata per request
- The backend uses them to override provider credentials for the current request only

Implications:

- This is convenient for a v1 or internal tool
- It is not equivalent to secure server-side credential storage
- Clearing browser storage removes the saved keys from that device

## Common Problems

### Frontend loads but no models appear

Usually one of these:

- `VITE_API_BASE_URL` is wrong
- backend `/v1/models` is failing
- no valid backend model config was set

### First request is very slow

Expected on Render free:

- the backend sleeps after inactivity
- the next request cold-starts the instance

### Vercel detects FastAPI instead of Vite

Override the settings manually:

- `Framework Preset`: `Vite`
- `Root Directory`: `frontend`

### Render deploy succeeds but health checks fail

Check:

- `Health Check Path` is `/v1/models`
- `Dockerfile Path` is `./Dockerfile`
- the backend logs show a successful startup

### User entered a key but requests still fail

Check:

- the selected model matches the provider for that key
- for example, an OpenRouter key only helps for an OpenRouter-backed model

## Recommended v1 Checklist

Before sharing the app:

1. Confirm Render `/v1/models` returns `200`
2. Confirm the Vercel frontend loads successfully
3. Confirm at least one chat request streams end to end
4. Confirm file upload still works
5. Confirm a user-entered API key works for the selected provider
6. Confirm your backend fallback keys are set if you want guest usage to work

## Related Files

- Backend entry: [`main.py`](../main.py)
- Backend Docker image: [`Dockerfile`](../Dockerfile)
- Frontend build config: [`frontend/package.json`](../frontend/package.json)
- Frontend API config: [`frontend/src/constants.ts`](../frontend/src/constants.ts)
- Docker/local setup: [`DOCKER_SETUP.md`](DOCKER_SETUP.md)
