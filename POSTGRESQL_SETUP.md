# PostgreSQL Setup Instructions

This branch uses PostgreSQL for data storage instead of SQLite.

## Prerequisites

1. Install PostgreSQL on your system:
   - **Windows**: Download from [postgresql.org](https://www.postgresql.org/download/windows/)
   - **Mac**: `brew install postgresql`
   - **Linux**: `sudo apt-get install postgresql postgresql-contrib`

## Database Setup

1. Start PostgreSQL service:
   ```bash
   # Windows (if installed as service, it starts automatically)
   # Mac
   brew services start postgresql
   
   # Linux
   sudo service postgresql start
   ```

2. Create the database:
   ```bash
   # Access PostgreSQL
   psql -U postgres
   
   # Create database
   CREATE DATABASE ai_game;
   
   # Exit
   \q
   ```

3. Update the `.env` file in the `backend` folder with your PostgreSQL credentials:
   ```env
   DATABASE_URL=postgresql://USERNAME:PASSWORD@localhost:5432/ai_game
   ```
   
   Default credentials (if you didn't change them):
   - Username: `postgres`
   - Password: `postgres` (or the password you set during installation)

## Running the Application

1. **Backend** (in `backend` folder):
   ```bash
   pip install -r requirements.txt
   python main.py
   ```

2. **Frontend** (in `frontend` folder):
   ```bash
   npm install
   npm run dev
   ```

## Features Added

- ✅ PostgreSQL database support
- ✅ Theme field added to stories
- ✅ Story list sidebar showing all created stories
- ✅ Click on any story to view it
- ✅ Create new stories from the sidebar
- ✅ Stories ordered by most recent first

## API Endpoints

- `GET /api/stories` - List all stories
- `POST /api/stories/create` - Create a new story
- `GET /api/stories/{id}/complete` - Get complete story details

## Reverting to SQLite

If you want to use SQLite instead of PostgreSQL, update the `.env` file:

```env
# Comment out PostgreSQL
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_game

# Uncomment SQLite
DATABASE_URL=sqlite:///./databse.db
```
