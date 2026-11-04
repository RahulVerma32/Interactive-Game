
# Hosted PostgreSQL storage

The backend uses SQLAlchemy for stories, story nodes, and generation jobs. Local development can use SQLite. For a hosted deployment, set `DEBUG=False` and provide a persistent PostgreSQL `DATABASE_URL`; startup fails if it is missing.

This workspace is linked to Neon project `spring-credit-05510815`, branch `production`. From the project root, `neon deploy` refreshes `.env.local`; the backend reads that file directly. Run `npm run build` at the project root for the React production build. To verify the API against Neon, start FastAPI from `backend/` with `uv run main.py`, then run `uv run python -m scripts.smoke_neon` in another terminal.

Story generation uses Google's `google-genai` Python SDK and the Interactions API. Create a key at [Google AI Studio](https://aistudio.google.com/apikey), add `GEMINI_API_KEY=...` to `backend/.env`, and restart FastAPI. The default model is `gemini-3.5-flash-lite`; change it with `GEMINI_MODEL` if needed. OpenRouter remains an optional fallback when `GEMINI_API_KEY` is empty. A missing key produces HTTP 503 before a generation job is created.

## Google sign-in

Neon Auth is enabled on the linked branch. Copy `NEON_AUTH_BASE_URL` from the root `.env.local` into `frontend/.env.local` as `VITE_NEON_AUTH_URL`, then restart Vite. Open `/login` and choose **Continue with Google**. Neon stores the user's name and email in `neon_auth.user`. The shared Google provider is for development; configure your own Google OAuth credentials and trusted production origin in Neon before deploying. Sign-in is required for stories and jobs; the API verifies Neon Auth bearer tokens and associates new stories with the authenticated user. Stories created before sign-in was required remain in the database but are not linked to accounts.

The generator asks for a flat eight-scene plan and builds the story links in Python. If the selected Gemini model times out, is busy, or returns invalid JSON, it retries with Flash-Lite. The free model can still be rate limited or temporarily unavailable.

From `backend/`, run `uv run python -m scripts.check_gemini` to make a short request and confirm the key works before generating a full story.

## Create a free Neon database

1. Create a free account and project at [Neon](https://console.neon.tech/). Choose the region closest to the backend server.
2. In the project dashboard, copy the **pooled** PostgreSQL connection string. Keep it private. The URL should include `sslmode=require`; the app adds it automatically for Neon hosts if missing.
3. The linked Neon project writes `DATABASE_URL` and `DATABASE_URL_UNPOOLED` into the project root `.env.local` when `neon deploy` completes. The backend reads those values automatically, with `backend/.env` still providing the AI token and local settings. For a manual setup, put the Neon URLs in `backend/.env`. Do not commit either file. The PostgreSQL driver is already in `pyproject.toml` and `requirements.txt`.
4. Set `ALLOWED_ORIGINS` to the exact frontend origin, such as `https://your-game.vercel.app`. Wildcard entries such as `https://*.vercel.app` do not authorize credentialed browser requests. If the frontend and API are on different sites, set `SESSION_COOKIE_SAMESITE=none` and `SESSION_COOKIE_SECURE=True`; serve the API over HTTPS.
5. Set `VITE_API_BASE_URL` in `frontend/.env` or the frontend host's environment settings to your public backend URL ending in `/api`. The browser never connects directly to Neon; only the FastAPI server uses the database URL. `DATABASE_URL` is pooled for app traffic; `DATABASE_URL_UNPOOLED` is direct for schema setup and migration.

From `backend/`, run `uv sync` and `uv run main.py`. The app creates the current tables on startup. For later schema changes, add migrations rather than relying on `create_all`.

## Move existing SQLite data

The local `database.db` contains any stories and jobs created before the switch. Keep a backup. With `DATABASE_URL` pointing to a **new, empty** Neon database, run from `backend/`:

```powershell
uv run python -m scripts.migrate_sqlite_to_postgres
```

Use `--source path/to/database.db` if the SQLite file is elsewhere. The script copies stories, nodes, and jobs with their original IDs, resets PostgreSQL ID sequences, and refuses to run if a target table already contains records. It does not delete the SQLite source.

To confirm the active database without displaying its credentials:

```powershell
uv run python -c "from db.database import engine; from sqlalchemy import text; print(engine.dialect.name); print(engine.connect().execute(text('SELECT 1')).scalar())"
```

Expect `postgresql` and `1`. Then create a story through the app, restart the API, and verify the story still loads in the same browser session.
