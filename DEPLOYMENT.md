# Deployment

## Supported Environments

| Platform | Status |
|---|---|
| Windows | Tested |
| Linux | Tested |
| macOS | Tested |

### Verified With

| Component | Version |
|---|---|
| Python | 3.10 |
| Docker | 24+ |
| FastAPI | 0.100+ |
| Uvicorn | 0.20+ |

---

## Local Deployment

### Prerequisites

- Python 3.10+
- pip

### Steps

```bash
# 1. Clone the repository
git clone <repo-url>
cd lyzr

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set LYZR_API_KEY (get one at https://console.lyzr.ai)

# 5. Run the application
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Run Tests

```bash
pytest tests/ -v
```

### Run Demo Pipeline

```bash
python demo_pipeline.py
```

### Run End-to-End Verification

```bash
python e2e_verify.py
```

---

## Docker Deployment

### Prerequisites

- Docker
- Docker Compose

### Steps

```bash
# 1. Clone the repository
git clone <repo-url>
cd lyzr

# 2. Configure environment
cp .env.example .env
# Edit .env and set LYZR_API_KEY

# 3. Build and start
docker compose up --build
```

The application is now available at `http://localhost:8000`.

### Stop

```bash
docker compose down
```

### Run tests in Docker

```bash
docker compose run --rm mission-engine python -m pytest tests/ -v
```

### Run demo in Docker

```bash
docker compose run --rm mission-engine python demo_pipeline.py
```

---

## Cloud Deployment

### Minimal requirements

| Resource | Spec |
|---|---|
| CPU | 1 vCPU |
| RAM | 512 MB |
| Disk | 1 GB |
| Python | 3.10+ |

### Render

1. Push to GitHub
2. Create a new **Web Service** on Render
3. Connect your repository
4. Set:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**: Add `LYZR_API_KEY`

### Railway

```bash
railway login
railway init
railway up
```

### Fly.io

```bash
fly launch
fly deploy
```

### AWS ECS / Google Cloud Run

Build the Docker image and push to a container registry, then deploy
with the container command `uvicorn app:app --host 0.0.0.0 --port 8000`.

---

## Health Verification

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

### Startup Validation Script

A comprehensive validation script is included:

```bash
# Local
python startup_validator.py

# Docker
docker compose run --rm mission-engine python startup_validator.py
```

It verifies:
- Python version
- All required directories
- All critical and project module imports
- Workflow registration (travel, dummy, checklist)
- FastAPI route registration
- All deployment files exist
- Environment variable presence

---

## Expected Logs

### Healthy startup (uvicorn)

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Startup validation (all passing)

```
============================================================
  SUMMARY
============================================================
  Passed: 42
  Failed: 0
  Total:  42

  [OK] Python version >= 3.10
  [OK] Directory exists: mission_engine/core
  ...
  All checks passed.
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `ModuleNotFoundError` | Missing dependencies | `pip install -r requirements.txt` |
| `LYZR_API_KEY not set` | Missing `.env` file | Copy `.env.example` to `.env` and set the key |
| `Address already in use` | Port 8000 occupied | Change port: `--port 8001` |
| Tests fail with `lyzr` import | Running outside project root | Run from the repository root directory |
| Docker build slow | No Docker layer caching | Run `docker compose build --no-cache` once |
