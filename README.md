# Interactive Story Generator

An AI-powered choose-your-own-adventure game that generates unique, branching narratives using GitHub Models API (GPT-4o-mini). Players can explore dynamic storylines with multiple paths and endings, where every choice shapes the outcome.

See [ROADMAP.md](ROADMAP.md) for the planned player-state, scene-generation, replay, sharing, and launch work.

## 🎮 Features

- **AI-Generated Stories**: Dynamically created narratives with 8-10 levels of depth
- **Multiple Endings**: Both winning and losing paths with varied outcomes
- **Branching Narratives**: 2-3 choices at each decision point
- **Persistent Storage**: SQLite database stores all generated stories
- **Session Management**: Track your story progress with session cookies
- **Async Generation**: Background job processing for smooth user experience

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangChain** - AI orchestration and prompt management
- **SQLAlchemy** - ORM for database operations
- **GitHub Models API** - Free GPT-4o-mini access via Azure
- **SQLite** - Lightweight local database (PostgreSQL supported for production)

### Frontend
- **React 19** - UI library
- **React Router** - Client-side routing
- **Vite** - Fast build tool and dev server
- **Axios** - HTTP client for API requests

## 📋 Prerequisites

- **Python 3.13+** (or use `uv` for automatic version management)
- **Node.js 18+** and npm
- **GitHub Personal Access Token** (for GitHub Models API)

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/RahulVerma32/Interactive-Game.git
cd Interactive-Game
```

### 2. Backend Setup

#### Install Dependencies

Using `uv` (recommended):
```bash
cd backend
uv sync
```

Or using pip:
```bash
cd backend
pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the `backend/` directory (or edit the existing one):

```env
# Database (SQLite for local development)
DATABASE_URL=sqlite:///./database.db

# API Configuration
API_PREFIX=/api
DEBUG=True

# CORS Origins (add your frontend URLs)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:5175

# GitHub Models API Token
GITHUB_TOKEN=your_github_token_here
```

**Get your GitHub Token:**
1. Go to https://github.com/settings/tokens
2. Generate a new token (classic) with appropriate scopes
3. Copy and paste into the `.env` file

#### Run the Backend Server

Using `uv`:
```bash
uv run main.py
```

Or using Python directly:
```bash
python main.py
```

The backend will start at **http://localhost:8000**

API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. Frontend Setup

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Configure Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_DEBUG=true
VITE_API_BASE_URL=http://localhost:8000/api
```

#### Run the Frontend Dev Server

```bash
npm run dev
```

The frontend will start at **http://localhost:5173** (or next available port)

## 🎯 How to Use

1. **Open the App**: Navigate to http://localhost:5173 in your browser

2. **Enter a Theme**: Type a theme for your story (e.g., "pirates", "space exploration", "medieval fantasy")

3. **Generate Story**: Click "Generate Story" and wait for the AI to create your adventure

4. **Make Choices**: Read the story content and select from 2-3 options at each step

5. **Reach an Ending**: Continue making choices until you reach a winning or losing ending

6. **Start Over**: Click "Restart Story" to try different paths or "New Story" to generate a completely new adventure

## 📁 Project Structure

```
Interactive-Game/
├── backend/
│   ├── core/
│   │   ├── config.py          # App configuration
│   │   ├── models.py          # LLM response models
│   │   ├── prompts.py         # AI prompts
│   │   └── story_generator.py # Story generation logic
│   ├── db/
│   │   └── database.py        # Database setup
│   ├── models/
│   │   ├── job.py             # Job model
│   │   └── story.py           # Story & StoryNode models
│   ├── routers/
│   │   ├── job.py             # Job status endpoints
│   │   └── story.py           # Story creation endpoints
│   ├── schemas/
│   │   ├── job.py             # Job schemas
│   │   └── story.py           # Story schemas
│   ├── main.py                # FastAPI app entry point
│   └── requirements.txt       # Python dependencies
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── LoadingStatus.jsx    # Loading animation
    │   │   ├── StoryGame.jsx        # Story gameplay component
    │   │   ├── StoryGenerator.jsx   # Story creation form
    │   │   ├── StoryLoader.jsx      # Story fetching wrapper
    │   │   └── ThemeInput.jsx       # Theme input form
    │   ├── App.jsx                  # Main app component
    │   ├── util.js                  # API configuration
    │   └── main.jsx                 # React entry point
    ├── package.json                 # Node dependencies
    └── vite.config.js               # Vite configuration
```

## 🔌 API Endpoints

### Stories
- `POST /api/stories/create` - Create a new story generation job
- `GET /api/stories/{story_id}/complete` - Get complete story with all nodes

### Jobs
- `GET /api/jobs/{job_id}` - Check story generation job status
