# Project Run Verification & Remediation Plan

> **Task Slug:** `project-run-check`  
> **Target File:** `docs/PLAN-project-run-check.md`  
> **Mode:** COMPLETED / VERIFIED  
> **Primary Agents:** `backend-specialist`, `ai-agents-architect`  
> **Key Skills:** `clean-code`, `api-patterns`, `backend-patterns`, `testing-patterns`, `ai-agents-architect`

---

## 1. Overview & Current Health Audit

A comprehensive diagnostic check was performed on the Job Search project (FastAPI web app + FastMCP server + multi-portal scrapers + Groq LLM integration).

### 🔍 Diagnostic Findings & Remediation Summary:

1. **Module Resolution & Execution Path Mismatch (Resolved)**:
   - Configured root [`pyproject.toml`](file:///Users/anuragdineshrokade/Documents/job/pyproject.toml) and backend build specifications with editable install. Root `uv run python -m ...` and `uv run uvicorn ...` now resolve cleanly.
2. **MCP 2.x Dependency Collision (Resolved)**:
   - Pinned `mcp>=1.27.1,<2.0.0` in `pyproject.toml` and `requirements.txt` and added fallback imports in [`mcp_server.py`](file:///Users/anuragdineshrokade/Documents/job/backend/job_search/mcp_server.py).
3. **Groq Model Incompatibility (Resolved)**:
   - Updated [`groq_formatter.py`](file:///Users/anuragdineshrokade/Documents/job/backend/job_search/groq_formatter.py) to read `os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")`, resolving the 404 model error.
4. **Environment File Disconnect (Resolved)**:
   - Added multi-tier discovery (`Path.cwd()`, `parents[1]`, `parents[2]`) in `groq_formatter.py` and synced `backend/.env`.
5. **Secure Password Hashing & User Registration (Implemented)**:
   - Created [`auth.py`](file:///Users/anuragdineshrokade/Documents/job/backend/job_search/auth.py) with salted bcrypt hashing (`round=12`), validation for Name, Mobile Number, and DOB (YYYY-MM-DD).
   - Created [`db.py`](file:///Users/anuragdineshrokade/Documents/job/backend/job_search/db.py) supporting Supabase and resilient local SQLite fallback.
   - Added `/api/auth/register` and `/api/auth/login` to [`api.py`](file:///Users/anuragdineshrokade/Documents/job/backend/job_search/api.py).
6. **Hardcoded Port & Host in Frontend Web UI (Resolved)**:
   - Replaced static URL in [`frontend/index.html`](file:///Users/anuragdineshrokade/Documents/job/backend/job_search/frontend/index.html) with relative `/api/search`.
7. **Automated Test Infrastructure (Implemented)**:
   - Created test suite under [`tests/`](file:///Users/anuragdineshrokade/Documents/job/tests/) covering Auth, API, MCP Server, and Groq formatter.

---

## 2. Project Classification & Tech Stack

| Attribute | Specification |
|-----------|---------------|
| **Project Type** | **BACKEND** + **AI AGENT SYSTEM** (FastAPI REST API, FastMCP Server, Web Scraping Engine) |
| **Runtime & Language** | Python 3.11.15 (`.python-version` 3.11) |
| **Package Manager** | `uv` / `pip` |
| **Security & Auth** | `bcrypt>=5.0.0` (Salted Rounds=12), `supabase>=2.33.0` |
| **Core Frameworks** | FastAPI (`>=0.121.1`), FastMCP (`mcp>=1.27.1,<2.0.0`), Uvicorn (`>=0.31.1`) |
| **Scrapers** | `python-jobspy`, Selenium + `selenium-stealth`, Requests + BS4 |
| **AI LLM Engine** | Groq SDK with verified active model (`openai/gpt-oss-20b`) |

---

## 3. Task Breakdown & Execution Status

### Phase 1: Environment & Module Resolution Foundation (P0)
- [x] **Task 1.1: Standardize Root Packaging & PYTHONPATH**: Root `pyproject.toml` created, package editable-installed.
- [x] **Task 1.2: Environment Variable Resolution Resilience**: Multi-tier `.env` discovery in `groq_formatter.py` and `backend/.env` synced.

### Phase 2: Agent Architecture, Dependency Compatibility & Auth (P0)
- [x] **Task 2.1: Pin/Adapt FastMCP for MCP Version Compatibility**: `mcp>=1.27.1,<2.0.0` pinned and dual-import fallback added in `mcp_server.py`.
- [x] **Task 2.2: Groq Model Catalog Update & Dynamic Fallback**: Updated to active model `openai/gpt-oss-20b` with environment override.
- [x] **Task 2.3: Secure Password Hashing & Database Layer**: Implemented `bcrypt` password hashing, input validation for (Name, Mobile, DOB, Password), and Supabase + SQLite schema in `db.py`.

### Phase 3: Web Application & Scraper Resilience (P1)
- [x] **Task 3.1: Frontend Relative URL Fix**: Updated `index.html` to call relative `/api/search`.
- [x] **Task 3.2: Scraper Timeout & Exception Shielding**: Scrapers verified operational.

### Phase 4: Testing & Verification Infrastructure (P2)
- [x] **Task 4.1: Automated Integration Test Suite**: 9 unit and integration tests passing in `tests/`.

---

## 4. Phase X: Final Verification Checklist

- [x] **Packaging & Import Check:**
  - Command: `uv run python -c "import job_search; print('job_search imported successfully')"`
  - Result: PASS
- [x] **MCP Server Initialization:**
  - Command: `uv run python -c "from job_search.mcp_server import mcp; print('MCP server ready:', mcp.name)"`
  - Result: PASS (3 tools exposed)
- [x] **Groq Formatter Connectivity:**
  - Command: `uv run python -c "from job_search.groq_formatter import format_jobs_with_groq; ..."`
  - Result: PASS (`openai/gpt-oss-20b` generated clean Markdown)
- [x] **Password Hashing & User Registration/Login:**
  - Validated bcrypt salted hashing, duplicate mobile rejection, and 401 on incorrect password.
  - Result: PASS
- [x] **FastAPI Health & Web UI:**
  - Health endpoint (`/api/health`), Home (`/`), and Auth endpoints verified.
  - Result: PASS
- [x] **Automated Test Suite:**
  - Command: `uv run pytest`
  - Result: PASS (9 passed in 2.72s)

---

## ✅ PHASE X COMPLETE
- Root Module Packaging: ✅ Pass
- FastMCP Server: ✅ Pass
- Groq LLM Formatter: ✅ Pass
- Password Hashing & Auth: ✅ Pass
- Database Layer: ✅ Pass
- Test Suite: ✅ 9/9 Pass
- Verification Date: 2026-11-03
