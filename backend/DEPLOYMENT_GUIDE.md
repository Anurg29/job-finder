# Job Search Backend - Deployment Guide

## Overview
This is a FastAPI-based job search backend that scrapes jobs from multiple sources (Indeed, LinkedIn, Naukri, Internshala) and provides both REST API and web interface.

## Project Structure

```
job/
├── job_search/
│   ├── __init__.py
│   ├── api.py                    # Main FastAPI application
│   ├── groq_formatter.py         # Job formatting with Groq AI
│   ├── unified_scraper.py        # Unified job scraper
│   ├── mcp_server.py             # MCP server for Claude integration
│   ├── frontend/
│   │   └── index.html            # Web UI
│   └── scrapers/
│       ├── __init__.py
│       ├── job_scraper.py        # JobSpy scraper (Indeed, LinkedIn)
│       ├── naukri_scraper.py     # Naukri scraper (Selenium-based)
│       └── internshala_scraper.py # Internshala scraper (Selenium-based)
├── pyproject.toml                # Project dependencies
├── .env.example                  # Environment variables template
├── README.md                      # Project documentation
└── DEPLOYMENT_GUIDE.md          # This file
```

## Prerequisites

- Python 3.11+
- pip or uv package manager
- Chrome/Chromium browser (for Naukri/Internshala scraping)

## Installation

### 1. Clone/Copy the Project
```bash
cd /path/to/project/job
```

### 2. Install Dependencies
```bash
# Option A: Using pip
pip install -e .

# Option B: Using uv (faster)
uv sync
```

### 3. Set Environment Variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

**Required environment variables:**
- `GROQ_API_KEY` - For AI-powered job formatting (optional, will fallback to JSON)

### 4. Verify Installation
```bash
python -c "from job_search import api; print('✓ Installation successful')"
```

## Running the Backend

### Option 1: Development Mode (with auto-reload)
```bash
cd /Users/anuragdineshrokade/Documents/job
uvicorn job_search.api:app --reload --port 8002
```

### Option 2: Production Mode
```bash
cd /Users/anuragdineshrokade/Documents/job
uvicorn job_search.api:app --host 0.0.0.0 --port 8002
```

### Option 3: Using MCP Server (for Claude Integration)
```bash
python -m job_search.mcp_server
```

## API Endpoints

### 1. Web Interface
- **URL:** `http://localhost:8002/`
- **Method:** GET
- **Returns:** HTML web interface

### 2. Health Check
- **URL:** `http://localhost:8002/api/health`
- **Method:** GET
- **Returns:** `{"status": "ok"}`

### 3. Job Search
- **URL:** `http://localhost:8002/api/search`
- **Method:** POST
- **Content-Type:** application/json

**Request Body:**
```json
{
  "query": "Python fresher jobs in Hyderabad",
  "roles": ["Python Developer", "AI ML Engineer"],
  "cities": ["Hyderabad", "Pune", "Mumbai", "Bangalore"],
  "include_naukri": false,
  "include_internshala": false,
  "naukri_pages": 1,
  "internshala_pages": 1,
  "max_results": 120
}
```

**Response:**
```json
{
  "query": "Python fresher jobs in Hyderabad",
  "total_jobs": 120,
  "jobs": [
    {
      "title": "Python Developer",
      "company": "Example Corp",
      "location": "Hyderabad, India",
      "date_posted": "2026-05-25",
      "job_url": "https://...",
      "source": "indeed",
      "description": "...",
      "min_exp": "Fresher"
    }
  ],
  "summary": "Formatted job summary..."
}
```

## Configuration

### Job Sources
- **JobSpy** (Default, fastest)
  - Indeed ✅
  - LinkedIn ✅
  - Zip Recruiter (optional)
  
- **Naukri** (Slow, requires Chrome automation)
  - Selenium-based scraping
  - Disabled by default in web UI
  
- **Internshala** (Slow, requires Chrome automation)
  - Selenium-based scraping
  - Disabled by default in web UI

### Performance Tips
1. **Disable Naukri/Internshala** for faster searches (they use browser automation)
2. **Reduce results_wanted** in job_scraper.py if searches are slow
3. **Use caching** for frequently searched queries

## Deployment Options

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

CMD ["uvicorn", "job_search.api:app", "--host", "0.0.0.0", "--port", "8002"]
```

### Heroku
```bash
# Create Procfile
echo "web: uvicorn job_search.api:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
git push heroku main
```

### AWS/Azure/GCP
Use any standard Python app deployment. Just ensure:
- Port 8002 is exposed
- Environment variables are set
- Dependencies are installed via `pip install -e .`

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process on port 8002
lsof -i :8002
kill -9 <PID>

# Or use a different port
uvicorn job_search.api:app --port 8003
```

### Missing Dependencies
```bash
# Reinstall dependencies
pip install --upgrade -e .
```

### Naukri/Internshala Not Working
- Ensure Chrome/Chromium is installed
- Check WebDriver installation: `python -m webdriver_manager chrome`
- Chrome automation might be blocked in some environments

### Groq API Key Issues
- If not set, the app will return JSON instead of formatted text
- Get a free key from https://console.groq.com/keys

## Monitoring & Logs

### View Live Logs
```bash
# Terminal output shows real-time logs
# Look for [API] and [Scraper] prefixes
```

### Common Log Messages
```
[API] Starting search for roles=[...], cities=[...]
[Scraper] Found X jobs from JobSpy
[API] Formatting X jobs with Groq
[API] Search completed
```

## API Rate Limiting
- JobSpy: No official limits, but ~20-50 results per query recommended
- Naukri: Implement delays between requests (auto-handled)
- Internshala: Implement delays between requests (auto-handled)

## Security Notes
- ⚠️ CORS is enabled for all origins (for development)
- For production, restrict CORS to specific domains in `api.py`
- Keep `.env` file secret (don't commit to git)
- Use environment variables for sensitive data

## Performance Metrics

**Typical Response Times:**
- Without Naukri/Internshala: 10-30 seconds
- With Naukri/Internshala: 2-5 minutes
- With Groq formatting: +5-10 seconds

## Support & Issues

### Check if Server is Running
```bash
curl http://localhost:8002/api/health
```

### Test Search Endpoint
```bash
curl -X POST http://localhost:8002/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python jobs",
    "roles": ["Python Developer"],
    "cities": ["Hyderabad"],
    "include_naukri": false,
    "include_internshala": false,
    "max_results": 10
  }'
```

## Next Steps

1. ✅ Install dependencies: `pip install -e .`
2. ✅ Set up `.env` file
3. ✅ Run server: `uvicorn job_search.api:app --reload --port 8002`
4. ✅ Access web UI: `http://localhost:8002`
5. ✅ Deploy to your platform

---

**Last Updated:** May 25, 2026
**Maintainer:** Your Name
