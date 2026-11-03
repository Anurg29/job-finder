# Backend Deployment Setup

## Project Ready for Deployment ✅

This backend is now clean and ready to deploy. All unnecessary files have been removed.

## Quick Start (After Deploying)

### Step 1: Install Dependencies
```bash
cd /path/to/job
pip install -e .
```

Or with uv (faster):
```bash
uv sync
```

### Step 2: Set Environment Variables
```bash
# Copy and edit
cp .env.example .env

# Add your GROQ_API_KEY (optional)
echo "GROQ_API_KEY=your_key_here" >> .env
```

### Step 3: Run the Backend Server
```bash
uvicorn job_search.api:app --reload --port 8002
```

Then open: **http://localhost:8002**

## Project Structure

```
job/
├── job_search/              # Main backend package
│   ├── api.py              # FastAPI application (core)
│   ├── groq_formatter.py   # AI job formatting
│   ├── unified_scraper.py  # Multi-source scraper
│   ├── mcp_server.py       # Claude MCP integration
│   ├── frontend/           # Web UI
│   │   └── index.html
│   └── scrapers/           # Job source scrapers
│       ├── job_scraper.py      (Indeed, LinkedIn)
│       ├── naukri_scraper.py   (Naukri - Selenium)
│       └── internshala_scraper.py (Internshala - Selenium)
├── pyproject.toml          # Dependencies & config
├── .env.example            # Environment template
├── DEPLOYMENT_GUIDE.md     # Detailed deployment guide
└── README.md               # Project info
```

## API Endpoints

### GET `/` 
Web interface (HTML UI)

### GET `/api/health`
Health check endpoint

### POST `/api/search`
Main search endpoint

**Example Request:**
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

## Key Features

✅ **FastAPI** - Modern Python web framework  
✅ **Multiple Job Sources** - Indeed, LinkedIn, Naukri, Internshala  
✅ **Web UI** - Interactive job search interface  
✅ **AI Formatting** - Groq-powered job summaries (optional)  
✅ **MCP Integration** - Claude AI integration support  
✅ **CORS Enabled** - Easy integration with frontends  

## Configuration

### Disable Slow Scrapers (Recommended for faster results)
In `unified_scraper.py`, set to `False`:
```python
def search_all_portals(
    roles: list[str],
    cities: list[str],
    include_naukri: bool = False,        # ← Change to False
    include_internshala: bool = False,   # ← Change to False
    ...
```

### Adjust Search Results
In `unified_scraper.py`:
```python
source_jobs = fetch_jobs(
    role=role,
    locations=[location],
    site_names=["indeed", "linkedin"],
    results_wanted=20,  # ← Change this
    hours_old=72,
)
```

## Performance Notes

- **Without Naukri/Internshala**: 10-30 seconds
- **With Naukri/Internshala**: 2-5 minutes
- **With Groq formatting**: +5-10 seconds

## Environment Variables

### Required (Optional)
```
GROQ_API_KEY=your_groq_api_key
```

Get one free from: https://console.groq.com/keys

### No Key Needed?
The app works fine without it - just returns JSON instead of formatted text.

## Troubleshooting

### Port 8002 Already in Use
```bash
# Kill existing process
lsof -i :8002 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Or use different port
uvicorn job_search.api:app --port 8003
```

### Missing Dependencies
```bash
pip install --upgrade -e .
```

### Check Server Status
```bash
curl http://localhost:8002/api/health
```

## Production Deployment Tips

1. **Disable reload in production:**
   ```bash
   uvicorn job_search.api:app --host 0.0.0.0 --port 8002
   ```

2. **Use a production server (Gunicorn):**
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker job_search.api:app
   ```

3. **Restrict CORS for security:**
   Edit `api.py` and change:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Specific domain
       ...
   )
   ```

4. **Use environment variables:**
   ```bash
   export GROQ_API_KEY="your_key"
   uvicorn job_search.api:app --host 0.0.0.0 --port 8002
   ```

## File Checklist Before Deployment

- ✅ `job_search/api.py` - Main app
- ✅ `job_search/scrapers/` - Job scrapers
- ✅ `job_search/frontend/` - Web UI
- ✅ `pyproject.toml` - Dependencies
- ✅ `.env.example` - Config template
- ✅ All Python source files

## Next Steps

1. Copy the entire `job` folder to your deployment server
2. Run: `pip install -e .`
3. Set up `.env` file with your API keys
4. Run: `uvicorn job_search.api:app --reload --port 8002`
5. Access at: http://your-server:8002

---

**Version:** 1.0.0  
**Updated:** May 25, 2026  
**Python:** 3.11+
