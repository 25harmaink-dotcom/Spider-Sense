# Spider-Sense frontend

Cinematic, fan-made student project; not affiliated with Marvel. The landing artwork is cropped from the AI-generated concept previously selected for this project; no source or artwork was copied from the reference websites. Not a real emergency service.

## Start locally (macOS)

Prerequisites: Python 3.10+ and Node.js 20.19+ or 22.12+ (Vite 8). Open a terminal in the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt pytest httpx
```

Create and securely store two independent secrets. The following is for an isolated local demo only. Keep the same audit secret for an existing database; changing it prevents existing history from verifying. Never commit secrets:

```bash
export SPIDER_SENSE_JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export SPIDER_SENSE_AUDIT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python -c 'from app.database import Base, engine; import app.models; Base.metadata.create_all(bind=engine)'
python -m uvicorn app.main:app --reload
```

For subsequent local runs, restore the *same* secrets you saved securely before running the server. A new JWT secret invalidates old tokens. For demo Hero accounts, in another terminal with the same virtual environment and secrets, run `python seed_heroes.py`. That script creates accounts with known passwords and is suitable **only for local demos**, never production. To create a Command account privately, run `python seed_command.py` and follow the prompts.

Open another terminal in the repository root and run:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to the local FastAPI service on port 8000; do not open the frontend via Vite's production preview unless a compatible reverse proxy is configured. API docs: http://127.0.0.1:8000/docs.

## Tests

From the root with the environment activated and both secrets set:

```bash
python -m pytest -q
cd frontend && npm run build && npm run lint
```

## Features and limitations

- Public signup is Citizen-only. The server checks roles and ownership; UI navigation is not authorization.
- Citizen and Command lists use server-side filters and pagination. Hero lists are unpaginated because the existing backend returns lists; heroes can claim, update, and review their own missions.
- Two role-scoped read routes were added: `GET /incidents/{id}/history` (reporting citizen) and `GET /hero/my-incidents` (claiming hero).
- Command can view all incidents, history and verify the existing hash/HMAC audit; reassignment is not implemented by this backend.
- JWT is stored in sessionStorage for this local student demo and expires according to the backend. JavaScript-accessible tokens are vulnerable to XSS; production needs a thorough security review and a suitable authentication/session design.
- The Hero map shows the selected Available or My Missions list. The Command map shows the current filtered page, not every page at once. Map tiles come from OpenStreetMap and require internet access. Markers and incident data still come from the API; several incidents may overlap.
- Citizen reporting uses a fixed list of New York areas. The chosen area stores an approximate representative coordinate, not an exact incident location. Older reports retain their original coordinates. This is not suitable for dispatch or emergencies.
- Online web fonts are optional; fallbacks are provided.
- The backend's SQLite database and this frontend are not hardened for real emergency or sensitive personal data.
