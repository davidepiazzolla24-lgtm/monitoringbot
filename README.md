# Monitoring Bot

A small FastAPI backend with a React/Vite frontend for tracking service status, incidents, and alerting rules. Authentication is simulated for OAuth2/SSO flows with role-based authorization (viewer vs admin).

## Backend

Run the API locally:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Endpoints include:
- `GET /status` – service health snapshots
- `GET /timeline` – chronological event feed (also pushed over `ws://localhost:8000/ws/events`)
- `GET/POST /incidents` – list and create incidents (admin only for create/close)
- `GET/POST /rules` – manage alerting rules (admin for writes)
- `POST /auth/token` – dummy token issuer to simulate OAuth2 tokens

Use bearer tokens `viewer-token` or `admin-token`, or send `X-Company-SSO` with those values to emulate SSO.

## Frontend

The React UI lives under `frontend/` with simple pages for Status, Timeline, Incidents, and Settings. To run the dev server:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies API calls to the backend running on port 8000 and exposes WebSocket events through the same path.
