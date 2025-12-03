# Deployment Guide

## Frontend Deployment

✅ **Already Deployed**: https://84750e99-41c2-4f8b-a95d-a59c0c0a8681.e1-eu-west-cdp.choreoapps.dev/

### To update the frontend:
1. Update the backend URL in your deployment platform's environment variables:
   ```
   VITE_API_BASE_URL=https://your-backend-url.com/api
   ```
2. Rebuild and redeploy

## Backend Deployment

### Prerequisites
- PostgreSQL database (✅ Already configured with Supabase)
- GitHub Token for AI models

### Environment Variables for Backend Deployment

Set these in your deployment platform (Railway, Render, etc.):

```env
DATABASE_URL=postgresql://postgres:sBCpwl3wPmkR7IBY@db.jutfmnflrtbyhmtmvzic.supabase.co:5432/postgres
API_PREFIX=/api
DEBUG=False
ALLOWED_ORIGINS=https://84750e99-41c2-4f8b-a95d-a59c0c0a8681.e1-eu-west-cdp.choreoapps.dev
GITHUB_TOKEN=your_github_token_here
```

### Deployment Options

#### Option 1: Railway (Recommended - Easy)
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Set root directory to `backend`
5. Add environment variables (see above)
6. Railway will auto-detect Python and deploy
7. Copy the deployed URL

#### Option 2: Render
1. Go to [render.com](https://render.com)
2. Create "New Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables
6. Deploy

#### Option 3: Heroku
1. Install Heroku CLI
2. Create `Procfile` in backend folder:
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
3. Deploy:
   ```bash
   cd backend
   heroku create your-app-name
   heroku config:set DATABASE_URL=your_supabase_url
   heroku config:set GITHUB_TOKEN=your_token
   heroku config:set ALLOWED_ORIGINS=https://84750e99-41c2-4f8b-a95d-a59c0c0a8681.e1-eu-west-cdp.choreoapps.dev
   git push heroku feature/postgresql-story-list:main
   ```

### After Backend Deployment

1. Get your backend URL (e.g., `https://your-app.railway.app`)
2. Update frontend environment variable:
   - In your Choreo deployment settings
   - Set: `VITE_API_BASE_URL=https://your-app.railway.app/api`
3. Redeploy frontend

### Testing

Once both are deployed:
1. Visit your frontend URL
2. Try creating a new story
3. Story should be saved to Supabase and appear in the sidebar
4. Refresh the page - stories should persist

## Important Notes

⚠️ **Security**:
- Never commit `.env` files with real credentials
- Use environment variables in deployment platforms
- Set `DEBUG=False` in production

✅ **CORS**: The backend is already configured to accept requests from your deployed frontend URL
