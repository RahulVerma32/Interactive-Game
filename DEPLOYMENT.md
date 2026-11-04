# Deploy TaleCraft

The frontend is a Vite static site. The FastAPI backend is packaged in Docker and uses the existing Neon database and Neon Auth. GitHub Actions checks both applications and builds the backend image on pull requests and pushes to `main`.

## Local Docker check

Start Docker Desktop, then from PowerShell:

```powershell
cd F:\Ai-game\backend
docker build -t talecraft-backend .
docker run --rm -p 8000:8000 --env-file .env --env-file ..\.env.local talecraft-backend
```

Stop any backend already listening on port 8000 first. This uses the configured Neon database and Gemini key; any story created through it is real. Open http://localhost:8000/docs to check the API. Do not commit either env file. Run the frontend separately with `cd F:\Ai-game\frontend` and `npm run dev`.

## GitHub Actions

Commit and push `.github/workflows/ci.yml`, `backend/Dockerfile`, `backend/.dockerignore`, `frontend/vercel.json`, and this document. The workflow runs on pull requests targeting `main` and pushes to `main`. It installs the locked Python dependencies, runs backend tests with SQLite, lints and builds the frontend, tests option shuffling, and builds the Docker image. It does not use real Neon credentials or send Gemini requests. CI does not deploy by itself.

## Render backend

1. Connect the GitHub repository to Render and create a **Web Service**. Select the `main` branch, `backend` as the root directory, Docker as the runtime, and the Free instance. The Dockerfile and build context should resolve to `backend/Dockerfile` and `backend` respectively.
2. In Render's environment settings, add the following without committing their values:
   - `DEBUG=False`
   - `DATABASE_URL`: your pooled Neon connection string.
   - `DATABASE_URL_UNPOOLED`: your direct Neon connection string, used by the existing startup table creation.
   - `NEON_AUTH_BASE_URL` and `NEON_AUTH_JWKS_URL`: the same Neon Auth branch used by the frontend.
   - `GEMINI_API_KEY` and `GEMINI_MODEL`: the Google API key and model configured for this app.
   - `ALLOWED_ORIGINS`: the exact Vercel origin, e.g. `https://your-app.vercel.app`, with no path or trailing slash. If there are multiple origins, separate them with commas.
3. Deploy and verify `/docs` on the resulting HTTPS URL. Set **Auto-Deploy** to **After CI Checks Pass** once the GitHub Actions workflow exists on the linked branch. Confirm the service is connected to GitHub: Render must see the check results for the same commit.

## Vercel frontend

1. Import the same GitHub repository into Vercel. Set its root directory to `frontend` and use the Vite defaults (`npm run build`, output directory `dist`).
2. Add the public build-time environment variables `VITE_API_BASE_URL=https://your-render-service.onrender.com/api` and `VITE_NEON_AUTH_URL=<Neon Auth base URL>`. Never put the database URL, Gemini key, or other secrets in a `VITE_` variable.
3. Deploy. Add the resulting exact Vercel origin to `ALLOWED_ORIGINS` on Render and to the Neon Auth trusted domains. Configure your own Google OAuth credentials in Neon for a public deployment; the shared provider is for development. Redeploy after changing frontend build-time variables.
4. Open the deployed app, sign in, create a story, make a choice, refresh, and verify History. Vercel auto-deploys independently of Render's CI gate; use branch protection to require the GitHub checks before merging to `main`.

## Operational notes

- Render's free web service can sleep and restart; its local filesystem is ephemeral. Neon holds the persistent data. Story generation currently runs as an in-process background task and can be interrupted on a restart; it is not a durable job queue.
- The existing backend calls `create_all` on startup. That creates missing tables but does not migrate existing ones. Introduce versioned migrations and test them on a Neon branch before changing the production schema.
- Monitor Render, Vercel, Neon, and Gemini usage; each has separate free-tier limits. The services can pause, reject requests, or incur charges depending on your plan and settings.
