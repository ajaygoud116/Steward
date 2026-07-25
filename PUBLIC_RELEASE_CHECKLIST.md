# Public Release Checklist

## Secrets & Credentials

- [ ] `.env` is NOT tracked by git (confirmed: `.env` is in `.gitignore`)
- [ ] No real API keys in any `.py`, `.md`, `.yml`, or `.json` file
- [ ] `.env.example` contains placeholder values only (`sk-your-api-key-here`)
- [ ] No hardcoded tokens, passwords, or connection strings
- [ ] No `*.pem`, `*.key`, or `*.crt` files in the repository

## Local Paths & Personal Information

- [ ] No absolute local paths (`C:\Users\...`, `/Users/...`, `/home/...`)
- [ ] No personal names, email addresses, or usernames in source files
- [ ] No machine-specific hostnames or IP addresses
- [ ] No IDE/editor config files (`.vscode/`, `.idea/`)

## Generated & Runtime Data

- [ ] `data/missions/` (271 JSON files) excluded via `.gitignore`
- [ ] `data/preferences/` excluded via `.gitignore`
- [ ] All `__pycache__/` directories excluded via `.gitignore`
- [ ] `.pytest_cache/` excluded via `.gitignore`
- [ ] No `*.pyc` bytecode files tracked

## Internal Documents (Recommend Deletion)

- [ ] `BLUEPRINT.md` deleted (100 KB internal design doc)
- [ ] `BRUTAL_REVIEW.md` deleted (internal code review)
- [ ] `ARCHITECTURE_AUDIT.md` deleted (internal audit)
- [ ] `CODE_VERIFICATION.md` deleted (internal verification report)
- [ ] `ENGINEERING_EVIDENCE_REPORT.md` deleted (internal evidence report)
- [ ] `FAILURE_MATRIX.md` deleted (internal failure analysis)
- [ ] `SUPERFLOW_STAGES.md` deleted (internal design doc)
- [ ] `TEST_AUDIT.md` deleted (internal test audit)
- [ ] `E2E_VERIFICATION.md` kept or regenerated (self-documenting artifact)

## Repository Structure

- [ ] `README.md` present and accurate
- [ ] `LICENSE` file present (if applicable — project currently has none)
- [ ] `DEPLOYMENT.md` present with local, Docker, and cloud instructions
- [ ] `.env.example` present with all documented variables
- [ ] `Dockerfile` present and builds successfully
- [ ] `docker-compose.yml` present and starts the application
- [ ] `.github/workflows/ci.yml` present
- [ ] `requirements.txt` has all runtime dependencies
- [ ] `.gitignore` covers all classified categories

## Functional Verification

- [ ] `pip install -r requirements.txt` succeeds
- [ ] `python startup_validator.py` exits with code 0
- [ ] `python -m pytest tests/ -x --tb=short` — all tests pass
- [ ] `python demo_pipeline.py` — 16/16 criteria demonstrated
- [ ] `python e2e_verify.py` — 109/109 checks pass
- [ ] `docker compose build` succeeds
- [ ] `docker compose up` — `GET /health` returns `{"status":"ok"}`

## Git Hygiene

- [ ] Commit history reviewed — no secrets in prior commits
- [ ] Branch name is `main` (or default branch)
- [ ] Version tag applied (e.g., `v1.0.0`)
- [ ] Tag is signed or annotated
- [ ] Release branch is up to date with `main`

## GitHub Release

- [ ] Repository set to **Public** on GitHub
- [ ] Release description written
- [ ] Release notes include:
    - What this project does
    - Quick-start instructions
    - Link to DEPLOYMENT.md
- [ ] Topics/tags set on GitHub (e.g., `mission-engine`, `workflow`, `python`, `fastapi`)
- [ ] README badge added: CI status, Python version
