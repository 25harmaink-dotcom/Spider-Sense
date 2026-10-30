# Free demo deployment: Render + Neon

This is a student demo, not a production emergency service. Do not use real personal or emergency data. The setup below uses a free Render web service plus a free Neon PostgreSQL database. Free-tier terms, limits, and availability can change; confirm them before creating resources. Render's free service may sleep and take time to wake. Neon free databases have compute and storage limits. Do not choose a paid plan if you want $0.

## What changed

- `DATABASE_URL` selects PostgreSQL for hosting; local runs still use SQLite when the variable is absent.
- `app.hosted` serves the existing FastAPI app at `/api` and the compiled React app at `/` from the same host. It creates missing tables at startup, but does not migrate or copy data.
- The Dockerfile builds the frontend and runs both parts together.
- This creates a **separate empty cloud database**. Existing local SQLite users, reports, and audit history are not copied.

## 1. Create the Neon database

1. Sign in at https://console.neon.tech/ and create a project on the **Free** plan.
2. In the Neon project dashboard, choose **Connect** and locate the PostgreSQL connection string. Keep it private: it contains credentials. Do not post it in chats, GitHub issues, screenshots, or the repository.
3. Keep that tab available for the Render step.

## 2. Deploy to Render

1. Sign in at https://dashboard.render.com/ and authorize access to the GitHub repository.
2. Create a **Web Service**, choose the `Spidysense` repository and the branch containing this deployment update (`feature/cinematic-frontend`, unless you merge it later).
3. Choose **Docker** as the runtime and the **Free** instance type. The Dockerfile is in the repository root; leave the root directory at the repository root. Check the price before continuing. Render supplies `PORT` automatically.
4. Add these environment variables in Render's dashboard (do not commit them):
   - `DATABASE_URL`: your full Neon connection string, including TLS parameters provided by Neon.
   - `SPIDER_SENSE_JWT_SECRET`: a new long, random, unique secret.
   - `SPIDER_SENSE_AUDIT_SECRET`: a different long, random, unique secret.
5. Use the optional health-check path `/health`, create the service, and wait for the build/deployment logs. The first database connection creates tables. Open the Render URL and check `/api/health`.

Store both secrets securely and keep them stable. Changing the JWT secret invalidates existing logins; changing the audit secret makes existing audit histories fail verification. Never paste either secret into chat or a public file. When making a new database, generate fresh independent secrets; do not reuse real local data.

## 3. Provision Hero and Command accounts privately

After the first deployment creates database tables, create accounts from your own computer. Do not run `seed_heroes.py` against the public database: that script contains known demo passwords. In a terminal from the project root:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Set `DATABASE_URL` in your terminal to the Neon connection string **without sharing it**. A Mac zsh option that does not echo the pasted value is:

```bash
read -rs DATABASE_URL
export DATABASE_URL
```

Paste the connection string and press Return; the cursor won't show it. Ensure `SPIDER_SENSE_JWT_SECRET` is set in this terminal (it is required by the imported security module; this account-creation script does not sign a token). Then run:

```bash
python seed_private.py
```

Choose `hero` or `command` and enter a unique email and strong private password when prompted. The password is hidden as you type. Run it again for the other role. It refuses to overwrite an existing account. Afterward:

```bash
unset DATABASE_URL
```

Don't share private account passwords with recruiters. You may create separate limited demo accounts with fictional data, and revoke or remove them afterward; there is no account-management UI yet.

## 4. Verify

- Visit the public URL; register a Citizen with fictional data.
- Submit a test incident; log in as Hero and verify it appears on the map, can be claimed, and proceeds through valid statuses.
- Log in as Command and check history and audit verification.
- Check Citizen and Hero cannot access Command data. Restart/redeploy and confirm the test report remains. Do not expose any real personal information.
- Monitor free-tier limits and back up any data you need. Never treat this demo as production-ready.

Local test results for this update: the existing 11 SQLite tests passed; an isolated local PostgreSQL test exercised the hosted frontend/API, registration, reporting, Hero claim and status updates, role restriction, Command audit verification, and persistence across application restarts. The Docker image and actual Render/Neon account deployment were not tested in this environment.
