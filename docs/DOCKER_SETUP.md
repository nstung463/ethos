# Ethos Full Stack Docker Setup

Production-ready setup: OpenWebUI (Frontend) + Ethos API + Open Terminal.

See also:

- [OPENWEBUI_ETHOS_ARCHITECTURE.md](/W:/panus/ethos/docs/OPENWEBUI_ETHOS_ARCHITECTURE.md)

That document explains the ownership boundary between OpenWebUI, Ethos, and Open Terminal, including managed files vs sandbox files.

## Quick Start

### 1. Setup Environment

```bash
cd W:/panus/ethos

# Copy template and edit
cp .env.example .env

# Edit .env with your API key
nano .env
# Or Windows:
notepad .env
```

Required in `.env`:

- `OPEN_TERMINAL_API_KEY`: Random secret (e.g., `openssl rand -hex 32`)
- `OPENROUTER_API_KEY` (or `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`)

### 2. Start Full Stack

```bash
docker-compose up -d
```

### 3. Access Services

- **OpenWebUI** (Frontend): http://localhost:3000
- **Ethos API**: http://localhost:8080
- **Open Terminal API**: http://localhost:8000

### 4. Verify Health

```bash
# Check all services running
docker-compose ps

# Check Ethos API models
curl http://localhost:8080/v1/models

# Check Open Terminal
curl -H "Authorization: Bearer $(grep OPEN_TERMINAL_API_KEY .env | cut -d= -f2)" \
  http://localhost:8000/health

# Check Ethos managed files compatibility API
curl http://localhost:8080/api/files/

# Check Ethos terminal compatibility API
curl http://localhost:8080/api/terminals/
```

## Usage

### In OpenWebUI

1. Open http://localhost:3000
2. Chat → Select model (should auto-detect Ethos)
3. Ask: "Create a file test.py with print('hello'), then run it"
4. AI will:
   - Write file to `/home/user/test.py` (open-terminal container)
   - Execute: `python test.py`
   - Show output: `hello`

Important:

- the file created by the agent is a sandbox file first
- it appears in the sandbox file browser, not automatically in managed files
- if a sandbox file should become durable application state, Ethos must import/promote it

## File Structure

```
workspace/          ← Ethos workspace (synced with container)
logs/              ← Ethos logs (synced with container)
docker-compose.yml ← Full stack config
Dockerfile         ← Ethos API image
.env               ← Environment variables (create from .env.example)
```

Managed files live under:

```text
workspace/managed_files/
```

Those are different from files living inside the Open Terminal runtime filesystem.

## Docker Volumes

```bash
# View Open Terminal data
docker volume inspect ethos-open-terminal-data

# View OpenWebUI data
docker volume inspect ethos-openwebui-data
```

## Logs

```bash
# Ethos API logs
docker logs ethos-api -f

# Open Terminal logs
docker logs ethos-open-terminal -f

# OpenWebUI logs
docker logs ethos-openwebui -f
```

## Stop & Cleanup

```bash
# Stop all services
docker-compose down

# Stop + remove volumes (⚠️ deletes data)
docker-compose down -v
```

## Troubleshooting

### Services won't start?

```bash
# Check logs
docker-compose logs

# Check if ports are in use
# Port 8000 (Open Terminal), 8080 (Ethos API), 3000 (OpenWebUI) must be free
```

### API Key mismatch?

```bash
# Verify .env is loaded
docker-compose config | grep OPEN_TERMINAL_API_KEY

# Must match in both services
# If changed, restart:
docker-compose restart ethos-api open-terminal
```

### Frontend points to the wrong API?

The OpenWebUI frontend uses `PUBLIC_*` build-time variables. If those values change, rebuild the `openwebui` image:

```bash
docker compose build openwebui
docker compose up -d openwebui
```

### Files not persisting?

```bash
# Check workspace volume
docker volume ls | grep open-terminal-data
docker run -it -v ethos-open-terminal-data:/mnt alpine ls -la /mnt
```

## Production Notes

⚠️ **For production deployment:**

- Use strong `OPEN_TERMINAL_API_KEY` (generate with `openssl rand -hex 32`)
- Use environment file securely (don't commit `.env`)
- Add reverse proxy (nginx) in front
- Set resource limits in `docker-compose.yml`
- Use `restart: always` for critical services
- Enable logging aggregation (e.g., ELK stack)

## Advanced Configuration

Edit `docker-compose.yml` to:

- Change port bindings
- Add environment variables
- Mount additional volumes
- Use different image tags
- Configure resource limits

Example resource limits:

```yaml
services:
  ethos-api:
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 4G
        reservations:
          cpus: "1"
          memory: 2G
```
