FastAPI backend prototype for DMS migration.

This folder contains a minimal FastAPI skeleton and an `auth` module
implementing JWT-based authentication to serve as a migration starting point.

Quick start (from project root):

```bash
python -m venv .venv-backend
.venv-backend\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Next steps: wire the DB URL in `app/core/config.py` and implement additional APIs.
