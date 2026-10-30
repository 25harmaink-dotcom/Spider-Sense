# Spider-Sense

A fan-made student project that connects incident reports with a fictional Hero response network. Citizens report incidents, Heroes claim and update them, and Command reviews activity and audit history. The interface is inspired by superhero stories; **this project is not affiliated with Marvel and is not a real emergency service**.

## Features

- Cinematic React landing page with an optional, skippable activation animation and reduced-motion support.
- Citizen-only public registration, JWT login, incident submission, and private access to the citizen's own reports and history.
- New York neighborhood dropdown: a predefined representative coordinate is sent to the API; no latitude/longitude entry is needed.
- Hero dashboard with available and claimed incidents, a map, claiming, and the status lifecycle: `reported → claimed → in_progress → resolved`.
- Command dashboard for viewing incident lists, assigned Hero IDs, history, and SHA-256 hash-chain/HMAC audit verification.
- Role and ownership checks enforced by FastAPI. A second claim and invalid status changes are rejected.
- Filtered, paginated Citizen and Command lists. Hero lists are not paginated by the current API.

The Hero map shows the selected mission tab; the Command map shows only the current filtered page. New incident markers indicate an **approximate neighborhood center**, not the exact incident location, and markers can overlap. Map tiles require internet access. Command does not automatically monitor system health or reassign incidents.

## Technology

React, Vite, Leaflet/OpenStreetMap, Python, FastAPI, SQLAlchemy, SQLite, JWT, Argon2 password hashing, and pytest. The frontend uses a Vite development proxy for `/api` requests to FastAPI.

## Run locally

Prerequisites: Python 3.10+ and Node.js 20.19+ or 22.12+ (as required by Vite 8). Commands below are for macOS/Linux, from the repository root.

### 1. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Set **both** environment variables before running the application:

```bash
export SPIDER_SENSE_JWT_SECRET='YOUR_PRIVATE_JWT_SECRET'
export SPIDER_SENSE_AUDIT_SECRET='YOUR_PRIVATE_AUDIT_SECRET'
```

Use long, random, different values and keep them private. If you already have a database, use your existing audit secret: changing it prevents previously recorded audit events from verifying. Changing the JWT secret invalidates previously issued tokens. Do not commit secrets or database files.

Create tables if necessary, then start the server:

```bash
python -c 'from app.database import Base, engine; import app.models; Base.metadata.create_all(bind=engine)'
python -m uvicorn app.main:app --reload
```

Health check: http://127.0.0.1:8000/health  
API documentation: http://127.0.0.1:8000/docs

### 2. Frontend

In a second terminal, from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open the **Local** URL shown by Vite, normally http://localhost:5173. If that port is occupied, Vite may choose another port such as 5174. Keep both servers running. For more detail see [frontend/README.md](frontend/README.md).

### 3. Accounts

Register a Citizen through the website. Public signup cannot create Hero or Command accounts. For local demonstration only, `python seed_heroes.py` creates Hero accounts with publicly known credentials in the script—**do not use these credentials in a public deployment**. To create a Command account privately, run `python seed_command.py` with the virtual environment active and the required environment variables set. Enter credentials when prompted; do not share real passwords.

## Test

Install test dependencies in the backend virtual environment:

```bash
python -m pip install pytest httpx
python -m pytest -q
```

Both secrets must be set before running the tests. In the frontend directory:

```bash
npm run build
npm run lint
```

An isolated test run of the current branch passed 11 backend tests; lint reported warnings but no errors. Run tests in your own environment to verify the current state. Browser flows tested in an isolated environment included Citizen registration and reporting, Hero claim and status updates, and Command audit verification.

## API overview

| Purpose | Method and route | Access |
| --- | --- | --- |
| Health | `GET /health` | Public |
| Register, login, current user | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` | Signup/login public; `/me` authenticated |
| Report and list | `POST /incidents`, `GET /incidents` | Citizen; list restricted to own incidents |
| Incident and history | `GET /incidents/{id}`, `GET /incidents/{id}/history` | Reporting Citizen |
| Available and own missions | `GET /hero/incidents`, `GET /hero/my-incidents` | Hero |
| Claim and update status | `POST /hero/incidents/{id}/claim`, `PATCH /hero/incidents/{id}/status` | Hero; status update restricted to claiming Hero |
| History | `GET /hero/incidents/{id}/history` | Claiming Hero |
| Oversight and audit | `GET /command/incidents`, `GET /command/incidents/{id}/history`, `GET /command/incidents/{id}/verify` | Command |

The API documentation is the source of truth for current request and response schemas. The ER diagram is in [er-diagram.mmd](er-diagram.mmd).

## Limitations and security

This is a local learning/demo application, not a production emergency response system. The backend uses a local SQLite file, and deployment to an ephemeral filesystem can lose data. The current Vite proxy is for development and does not automatically configure a production host. Browser tokens in sessionStorage are vulnerable to XSS; a production release needs security review, appropriate session management, stronger operational protections, and persistent storage. Do not enter sensitive or real emergency information.

The audit uses a hash chain and HMAC, not ECDSA or a blockchain. Successful verification checks integrity against the configured secret; it does not prove that a reported incident is true. The landing imagery is adapted from an AI-generated concept and the project used AI assistance during development.

## Free demo deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for the Render + Neon free-tier setup, limitations, and private Hero/Command provisioning. The deployment uses a new empty cloud database; local SQLite data is not migrated automatically.
