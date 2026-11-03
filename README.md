# Job Search Application

A FastAPI-based job search backend that scrapes jobs from multiple sources (Indeed, LinkedIn, Naukri, Internshala) and provides both REST API and web interface.

## 📁 Project Structure

```
job/
├── backend/                          [ALL BACKEND FILES HERE]
│   ├── job_search/                   [Main backend package]
│   │   ├── api.py                    [FastAPI application]
│   │   ├── groq_formatter.py         [AI job formatting]
│   │   ├── unified_scraper.py        [Multi-source scraper]
│   │   ├── mcp_server.py             [Claude MCP integration]
│   │   ├── frontend/                 [Web UI]
│   │   │   └── index.html
│   │   └── scrapers/                 [Job scrapers]
│   ├── pyproject.toml                [Dependencies]
│   ├── requirements.txt              [Python packages]
│   ├── .env.example                  [Environment template]
│   ├── setup.sh                      [Auto setup (Linux/Mac)]
│   ├── setup.bat                     [Auto setup (Windows)]
│   ├── DEPLOYMENT_READY.md           [Quick start]
│   └── DEPLOYMENT_GUIDE.md           [Detailed guide]
│
└── docs/                             [Documentation]
    └── PROJECT_DOCUMENTATION.md
```

## 🚀 Quick Start

### Automatic Setup (Recommended)

**Linux/Mac:**
```bash
cd backend
bash setup.sh
```

**Windows:**
```bash
cd backend
setup.bat
```

### Manual Setup

```bash
cd backend
pip install -e .
cp .env.example .env
uvicorn job_search.api:app --reload --port 8002
```

Then open: **http://localhost:8002**

## ✨ Features

- ✅ FastAPI REST API
- ✅ Web UI for interactive search
- ✅ Multi-source scraping (Indeed, LinkedIn, Naukri, Internshala)
- ✅ AI-powered formatting with Groq
- ✅ Claude MCP integration
- ✅ CORS enabled
- ✅ Production-ready

## 📚 Documentation

All setup and deployment instructions are in the `backend/` folder:
- **DEPLOYMENT_READY.md** - Quick start guide
- **DEPLOYMENT_GUIDE.md** - Detailed deployment guide

## 🔧 Requirements

- Python 3.11+
- pip or uv
- Chrome/Chromium (for Naukri/Internshala)

## 📝 Environment Variables

In `backend/.env`:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free key from: https://console.groq.com/keys

## 📖 API Endpoints

```bash
cd /Users/anuragdineshrokade/Documents/job
uv run python -m job_search.mcp_server
```

## Run Standalone Web App (No Claude)

```bash
cd /Users/anuragdineshrokade/Documents/job
uv run uvicorn job_search.api:app --reload --host 127.0.0.1 --port 8000
```

Open:
- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

## Claude Desktop MCP Config

File:
- `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "job-search": {
      "command": "/Users/anuragdineshrokade/Documents/job/.venv/bin/python",
      "args": ["-m", "job_search.mcp_server"],
      "env": {
        "GROQ_API_KEY": "your_real_groq_key"
      }
    }
  }
}
```

Restart Claude Desktop after config changes.

## Documentation

Detailed architecture and line-by-line flow:
- `docs/PROJECT_DOCUMENTATION.md`
