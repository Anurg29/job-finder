from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from job_search.groq_formatter import format_jobs_with_groq
from job_search.unified_scraper import search_all_portals
from job_search.auth import (
    hash_password,
    verify_password,
    validate_registration_input,
)
from job_search.db import create_user, get_user_by_mobile

PACKAGE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = PACKAGE_DIR / "frontend"


class SearchRequest(BaseModel):
    query: str = "Python fresher jobs in Hyderabad"
    roles: list[str] = Field(
        default_factory=lambda: ["Python Developer", "AI ML Engineer"]
    )
    cities: list[str] = Field(
        default_factory=lambda: ["Hyderabad", "Pune", "Mumbai", "Bangalore"]
    )
    include_naukri: bool = True
    include_internshala: bool = True
    naukri_pages: int = Field(default=1, ge=1, le=5)
    internshala_pages: int = Field(default=1, ge=1, le=5)
    max_results: int = Field(default=120, ge=10, le=500)


class SearchResponse(BaseModel):
    query: str
    total_jobs: int
    jobs: list[dict[str, Any]]
    summary: str


class RegisterRequest(BaseModel):
    full_name: str
    mobile_no: str
    dob: str  # Format: YYYY-MM-DD
    password: str


class LoginRequest(BaseModel):
    mobile_no: str
    password: str


class AuthResponse(BaseModel):
    status: str
    message: str
    user: dict[str, Any] | None = None


app = FastAPI(
    title="Job Search Web API",
    description="Standalone web API for fresher job search across multiple portals with secure authentication.",
    version="1.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.get("/")
def home() -> FileResponse:
    return FileResponse(str(FRONTEND_DIR / "index.html"), media_type="text/html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/register", response_model=AuthResponse)
def register(payload: RegisterRequest) -> AuthResponse:
    is_valid, error_msg = validate_registration_input(
        full_name=payload.full_name,
        mobile_no=payload.mobile_no,
        dob=payload.dob,
        password=payload.password,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg or "Invalid input.",
        )

    existing_user = get_user_by_mobile(payload.mobile_no)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this mobile number already exists.",
        )

    # Securely hash password with bcrypt
    hashed = hash_password(payload.password)

    user = create_user(
        full_name=payload.full_name,
        mobile_no=payload.mobile_no,
        dob=payload.dob,
        password_hash=hashed,
    )

    return AuthResponse(
        status="success",
        message="User registered successfully.",
        user={
            "id": user["id"],
            "full_name": user["full_name"],
            "mobile_no": user["mobile_no"],
            "dob": user["dob"],
        },
    )


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    user = get_user_by_mobile(payload.mobile_no)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mobile number or password.",
        )

    if not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mobile number or password.",
        )

    return AuthResponse(
        status="success",
        message="Login successful.",
        user={
            "id": user["id"],
            "full_name": user["full_name"],
            "mobile_no": user["mobile_no"],
            "dob": user.get("dob", ""),
        },
    )


@app.post("/api/search", response_model=SearchResponse)
def search_jobs(payload: SearchRequest) -> SearchResponse:
    roles = [role.strip() for role in payload.roles if role.strip()]
    cities = [city.strip() for city in payload.cities if city.strip()]

    if not roles:
        raise HTTPException(status_code=400, detail="At least one role is required.")
    if not cities:
        raise HTTPException(status_code=400, detail="At least one city is required.")

    try:
        print(f"[API] Starting search for roles={roles}, cities={cities}")
        all_jobs = search_all_portals(
            roles=roles,
            cities=cities,
            include_naukri=payload.include_naukri,
            include_internshala=payload.include_internshala,
            naukri_pages=payload.naukri_pages,
            internshala_pages=payload.internshala_pages,
        )
        print(f"[API] Search completed. Found {len(all_jobs)} jobs")
    except Exception as exc:
        print(f"[API] Search failed with error: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc

    try:
        limited_jobs = all_jobs[: payload.max_results]
        print(f"[API] Formatting {len(limited_jobs)} jobs with Groq")
        summary = format_jobs_with_groq(limited_jobs, payload.query)
        print(f"[API] Formatting complete")
    except Exception as exc:
        print(f"[API] Formatting failed with error: {exc}")
        import traceback
        traceback.print_exc()
        summary = f"Error formatting results: {exc}"

    return SearchResponse(
        query=payload.query,
        total_jobs=len(limited_jobs),
        jobs=limited_jobs,
        summary=summary,
    )
