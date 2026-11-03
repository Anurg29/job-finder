import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Multi-tier .env discovery
_CANDIDATE_ENVS = [
    Path.cwd() / ".env",
    Path(__file__).resolve().parents[1] / ".env",
    Path(__file__).resolve().parents[2] / ".env",
]
for _env_file in _CANDIDATE_ENVS:
    if _env_file.exists():
        load_dotenv(dotenv_path=_env_file)
        break

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# SQLite fallback path
DB_PATH = Path(__file__).resolve().parents[1] / "job_search.db"


def _init_sqlite_db() -> None:
    """Initialize local SQLite schema matching Supabase PostgreSQL tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # User profiles table with hashed password
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            mobile_no TEXT UNIQUE NOT NULL,
            dob TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Jobs catalog table (caching scraped jobs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            job_url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            date_posted TEXT,
            min_exp TEXT DEFAULT 'Fresher',
            source TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # User saved jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_jobs (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            job_id TEXT NOT NULL,
            status TEXT DEFAULT 'saved',
            saved_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            UNIQUE (user_id, job_id)
        )
    """)

    conn.commit()
    conn.close()


# Ensure SQLite schema is prepared for instant local execution
_init_sqlite_db()


def get_supabase_client() -> Any | None:
    """Return Supabase client if configured, else None."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as exc:
        print(f"[DB Warning] Could not initialize Supabase client: {exc}")
        return None


def create_user(
    full_name: str,
    mobile_no: str,
    dob: str,
    password_hash: str
) -> dict[str, Any]:
    """Create a new user with hashed password."""
    supabase = get_supabase_client()
    user_id = str(uuid.uuid4())
    now_iso = datetime.utcnow().isoformat()

    if supabase:
        try:
            res = supabase.table("users").insert({
                "id": user_id,
                "full_name": full_name.strip(),
                "mobile_no": mobile_no.strip(),
                "dob": dob.strip(),
                "password_hash": password_hash,
                "created_at": now_iso
            }).execute()
            if res.data:
                return {
                    "id": user_id,
                    "full_name": full_name.strip(),
                    "mobile_no": mobile_no.strip(),
                    "dob": dob.strip(),
                    "created_at": now_iso,
                    "storage": "supabase"
                }
        except Exception as exc:
            print(f"[Supabase Insert Failed, falling back to SQLite]: {exc}")

    # SQLite fallback
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (id, full_name, mobile_no, dob, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, full_name.strip(), mobile_no.strip(), dob.strip(), password_hash, now_iso)
    )
    conn.commit()
    conn.close()

    return {
        "id": user_id,
        "full_name": full_name.strip(),
        "mobile_no": mobile_no.strip(),
        "dob": dob.strip(),
        "created_at": now_iso,
        "storage": "sqlite"
    }


def get_user_by_mobile(mobile_no: str) -> dict[str, Any] | None:
    """Retrieve user and password hash by mobile number."""
    supabase = get_supabase_client()
    clean_mobile = mobile_no.strip()

    if supabase:
        try:
            res = supabase.table("users").select("*").eq("mobile_no", clean_mobile).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as exc:
            print(f"[Supabase Query Failed, falling back to SQLite]: {exc}")

    # SQLite fallback
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE mobile_no = ?", (clean_mobile,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None
