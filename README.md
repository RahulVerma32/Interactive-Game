# Interactive Story Generator

An AI-powered choose-your-own-adventure game that generates branching narratives through the Gemini API. Players can explore multiple paths and endings, where each choice shapes the outcome.


## 🎮 Features

- **AI-Generated Stories**: Three chapters with ten nodes each
- **Branching Adventures**: Choices lead through different scenes before paths rejoin
- **Branching Narratives**: Three choices at each non-ending node
- **Persistent Storage**: SQLite database stores all generated stories
- **Saved Progress**: Signed-in users can resume their story on another device
- **Async Generation**: Background job processing for smooth user experience

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangChain** - AI orchestration and prompt management
- **SQLAlchemy** - ORM for database operations
- **Google Gemini API** - AI story generation through Google AI Studio (OpenRouter remains an optional fallback)
- **SQLite** - Lightweight local database (PostgreSQL supported for production)

### Frontend
- **React 19** - UI library
- **React Router** - Client-side routing
- **Vite** - Fast build tool and dev server
- **Axios** - HTTP client for API requests

## 📋 Prerequisites

- **Python 3.13+** (or use `uv` for automatic version management)
- **Node.js 18+** and npm
- **Google AI Studio API key** (for story generation)

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

# Google AI Studio API key
GEMINI_API_KEY=your_google_ai_studio_api_key
GEMINI_MODEL=gemini-3.5-flash-lite
```

**Get your Google AI Studio key:**
1. Open https://aistudio.google.com/apikey and create a Gemini API key.
2. Put the key in `backend/.env` as `GEMINI_API_KEY`. Keep it private and restart the backend.
3. `gemini-3.5-flash-lite` has a free tier, subject to your project's limits in AI Studio. If you prefer OpenRouter, leave `GEMINI_API_KEY` empty and set `OPENROUTER_API_KEY` instead.

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

4. **Make Choices**: Read the story content and select from two options at each step

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


### Chapter storage

New stories contain three chapters of ten nodes each. Branches rejoin at certain points, so a single playthrough visits a subset of the 30 nodes. Choices and the current node are saved to the signed-in user's playthrough. Existing stories remain playable. The backend creates the new additive tables at startup; it does not alter existing story tables. For production, test the schema change against a database branch before restarting the backend with the new code.
