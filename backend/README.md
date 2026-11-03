# Job Search Platform

Multi-source job search project with:
- MCP server (for Claude/any MCP client)
- Standalone web app (no Claude dependency)

## Clean File Structure

```text
job/
  .env
  pyproject.toml
  uv.lock
  README.md
  docs/
    PROJECT_DOCUMENTATION.md
  job_search/
    __init__.py
    api.py
    mcp_server.py
    groq_formatter.py
    unified_scraper.py
    frontend/
      index.html
    scrapers/
      __init__.py
      job_scraper.py
      naukri_scraper.py
      internshala_scraper.py
```

## Setup

```bash
cd /Users/anuragdineshrokade/Documents/job
uv sync
```

Python policy for this project:
- `.python-version` is `3.11`
- `pyproject.toml` enforces `>=3.11,<3.12`
- Always run with `uv run ...` (do not use system `python`/`uvicorn`)

Create or update `.env` in project root:

```env
GROQ_API_KEY="your_groq_api_key"
```

## Run MCP Server

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
