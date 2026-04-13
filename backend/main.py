from __future__ import annotations

import os
import re
import sys
import json
import ssl
import time
import hmac
import math
import hashlib
import uuid
import shutil
import socket
import base64
import random
import secrets
import smtplib
import asyncio
import threading
import importlib.util
from collections import deque
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from enum import Enum
from io import BytesIO
from queue import Empty, Full, Queue
from types import SimpleNamespace
from typing import Annotated, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request as UrlRequest, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import qrcode
import requests
from dotenv import load_dotenv
from fastapi import (
    Body,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    WebSocket,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from html import escape
from jose import jwt
from pydantic import BaseModel, ConfigDict, field_validator
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy import inspect, or_, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.websockets import WebSocketDisconnect

try:
    from .app.core.database import Base, IS_SQLITE, SessionLocal, engine
    from .app.models.admin_user import AdminUser
    from .app.models.device import Device
    from .app.models.issue import Issue
    from .app.models.sensor_reading import SensorReading
    from .app.models.user import User
    from .app.models.worker import Worker
    from .app.models.worker_reset_request import WorkerResetRequest
except ImportError:
    from app.core.database import Base, IS_SQLITE, SessionLocal, engine
    from app.models.admin_user import AdminUser
    from app.models.device import Device
    from app.models.issue import Issue
    from app.models.sensor_reading import SensorReading
    from app.models.user import User
    from app.models.worker import Worker
    from app.models.worker_reset_request import WorkerResetRequest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

@app.on_event("startup")
async def startup_event():
    print("Server started successfully", file=sys.stderr)

# User login endpoint (JSON)
@app.post("/login")
async def user_login(payload: dict = Body(...)):
    try:
        email = payload.get("email", "").strip()
        password = payload.get("password", "").strip()
        print("USER LOGIN EMAIL:", email)
        print("USER LOGIN PASSWORD:", password)
        # Replace with real user check
        if email == "user@example.com" and password == "userpass":
            return JSONResponse({"status": "success", "message": "User logged in"})
        return JSONResponse({"status": "error", "message": "Invalid credentials"}, status_code=401)
    except Exception as e:
        print(f"User login error: {e}", file=sys.stderr)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# Admin login endpoint (FormData)
@app.post("/admin/session-login")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        print("ADMIN LOGIN USERNAME:", username)
        print("ADMIN LOGIN PASSWORD:", password)
        if username.strip() == "admin" and password.strip() == "1234":
            request.session["admin"] = True
            return RedirectResponse("/admin/setup", status_code=302)
        return HTMLResponse("Invalid admin credentials", status_code=401)
    except Exception as e:
        print(f"Admin login error: {e}", file=sys.stderr)
        return HTMLResponse(f"Internal server error: {e}", status_code=500)

# Admin protected page
@app.get("/admin/setup")
async def admin_setup(request: Request):
    try:
        if not request.session.get("admin"):
            return RedirectResponse("/admin", status_code=302)
        return HTMLResponse("""
            <h2>Admin Setup Page (Protected)</h2>
            <form method=\"post\" action=\"/admin/logout\">
                <button type=\"submit\">Logout</button>
            </form>
        """)
    except Exception as e:
        print(f"Admin setup error: {e}", file=sys.stderr)
        return HTMLResponse(f"Internal server error: {e}", status_code=500)

# Admin login page
@app.get("/admin")
async def admin_login_page():
    return HTMLResponse("""
        <form method=\"post\" action=\"/admin/session-login\">
            <input name=\"username\" placeholder=\"Username\" required>
            <input name=\"password\" type=\"password\" placeholder=\"Password\" required>
            <button type=\"submit\">Login</button>
        </form>
    """)

# Admin logout
@app.post("/admin/logout")
async def admin_logout(request: Request):
    try:
        request.session.clear()
        return RedirectResponse("/admin", status_code=302)
    except Exception as e:
        print(f"Admin logout error: {e}", file=sys.stderr)
        return HTMLResponse(f"Internal server error: {e}", status_code=500)
    if db.query(AdminUser).filter(AdminUser.username == username).first():
        return HTMLResponse("<h3>Admin already exists.</h3>", status_code=400)
    from main import hash_password  # Use your existing hash_password function
    new_admin = AdminUser(username=username, password_hash=hash_password(password))
    db.add(new_admin)
    db.commit()
    print(f"DEBUG: Created new admin username={username}")
    return HTMLResponse("<h3>Admin created successfully!</h3>")

@app.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    print("DEBUG: Session cleared, logged out")
    return RedirectResponse("/admin", status_code=303)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import qrcode
from reportlab.lib.utils import ImageReader
from io import BytesIO
from html import escape
from sqlalchemy import inspect, text, or_
from sqlalchemy.exc import OperationalError
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
from typing import Annotated
from fastapi import UploadFile, File
from pydantic import BaseModel, ConfigDict, field_validator
try:
    from .smart_monitoring import (
        DEFAULT_LOCATION_CATALOG,
        STATUS_TO_PRIORITY,
        apply_admin_action,
        apply_realism,
        build_alert_events,
        build_history_rows,
        build_live_payload,
        build_location_collection,
        build_location_key as smart_build_location_key,
        enrich_snapshot,
        force_reset_snapshot,
        iso_now,
        safe_float as smart_safe_float,
    )
    from .sensor_engine import CentralSensorEngine, REPORT_RANGE_ALIASES
except ImportError:
    from smart_monitoring import (
        DEFAULT_LOCATION_CATALOG,
        STATUS_TO_PRIORITY,
        apply_admin_action,
        apply_realism,
        build_alert_events,
        build_history_rows,
        build_live_payload,
        build_location_collection,
        build_location_key as smart_build_location_key,
        enrich_snapshot,
        force_reset_snapshot,
        iso_now,
        safe_float as smart_safe_float,
    )
    from sensor_engine import CentralSensorEngine, REPORT_RANGE_ALIASES

class IssueStatus(str, Enum):
    Pending = "Pending"
    InProgress = "In Progress"
    Resolved = "Resolved"
    Rejected = "Rejected"
# Create DB tables
Base.metadata.create_all(bind=engine)


def ensure_schema_updates():
    inspector = inspect(engine)
    dialect_name = engine.dialect.name.lower()

    def ddl_type(kind: str) -> str:
        if dialect_name == "oracle":
            mapping = {
                "string": "VARCHAR2(255)",
                "text": "CLOB",
                "float": "FLOAT",
                "integer": "NUMBER",
                "datetime": "TIMESTAMP",
            }
            return mapping[kind]
        mapping = {
            "string": "VARCHAR",
            "text": "TEXT",
            "float": "FLOAT",
            "integer": "INTEGER",
            "datetime": "DATETIME",
        }
        return mapping[kind]

    def add_column_ddl(table_name: str, column_name: str, kind: str) -> str:
        column_type = ddl_type(kind)
        if dialect_name == "oracle":
            return f"ALTER TABLE {table_name} ADD {column_name} {column_type}"
        return f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"

    issue_columns = {col["name"] for col in inspector.get_columns("issues")} if inspector.has_table("issues") else set()
    worker_columns = {col["name"] for col in inspector.get_columns("workers")} if inspector.has_table("workers") else set()
    user_columns = {col["name"] for col in inspector.get_columns("users")} if inspector.has_table("users") else set()
    if "user_id" not in issue_columns and inspector.has_table("issues"):
        with engine.begin() as connection:
            connection.execute(text(add_column_ddl("issues", "user_id", "integer")))
    assignment_columns = {
        "assigned_department": add_column_ddl("issues", "assigned_department", "string"),
        "assigned_worker_id": add_column_ddl("issues", "assigned_worker_id", "string"),
        "assignment_deadline": add_column_ddl("issues", "assignment_deadline", "datetime"),
        "assignment_duration_label": add_column_ddl("issues", "assignment_duration_label", "string"),
        "assigned_by_admin_id": add_column_ddl("issues", "assigned_by_admin_id", "integer"),
        "worker_status": add_column_ddl("issues", "worker_status", "string"),
        "worker_resolution_requested_at": add_column_ddl("issues", "worker_resolution_requested_at", "datetime"),
        "admin_deleted": add_column_ddl("issues", "admin_deleted", "integer"),
        "admin_deleted_at": add_column_ddl("issues", "admin_deleted_at", "datetime"),
        "updated_at": add_column_ddl("issues", "updated_at", "datetime"),
        "assigned_at": add_column_ddl("issues", "assigned_at", "datetime"),
    }
    with engine.begin() as connection:
        for column_name, ddl in assignment_columns.items():
            if inspector.has_table("issues") and column_name not in issue_columns:
                connection.execute(text(ddl))
        if inspector.has_table("issues"):
            connection.execute(text("UPDATE issues SET updated_at = COALESCE(updated_at, created_at)"))
            if "admin_deleted" in {**assignment_columns}:
                connection.execute(text("UPDATE issues SET admin_deleted = COALESCE(admin_deleted, 0)"))
        if inspector.has_table("workers") and "password_plaintext" not in worker_columns:
            connection.execute(text(add_column_ddl("workers", "password_plaintext", "string")))

        user_column_ddls = {
            "first_name": add_column_ddl("users", "first_name", "string"),
            "last_name": add_column_ddl("users", "last_name", "string"),
            "registration_source": add_column_ddl("users", "registration_source", "string"),
            "registered_device_identifier": add_column_ddl("users", "registered_device_identifier", "string"),
            "registered_device_name": add_column_ddl("users", "registered_device_name", "string"),
            "registered_device_type": add_column_ddl("users", "registered_device_type", "string"),
            "registered_device_model": add_column_ddl("users", "registered_device_model", "string"),
            "registered_device_platform": add_column_ddl("users", "registered_device_platform", "string"),
            "registered_device_os_version": add_column_ddl("users", "registered_device_os_version", "string"),
            "registered_app_version": add_column_ddl("users", "registered_app_version", "string"),
            "registered_ip_address": add_column_ddl("users", "registered_ip_address", "string"),
            "email_verified": add_column_ddl("users", "email_verified", "integer"),
            "email_verification_code_hash": add_column_ddl("users", "email_verification_code_hash", "string"),
            "email_verification_expires_at": add_column_ddl("users", "email_verification_expires_at", "datetime"),
        }
        for column_name, ddl in user_column_ddls.items():
            if inspector.has_table("users") and column_name not in user_columns:
                connection.execute(text(ddl))

        if inspector.has_table("users"):
            connection.execute(
                text(
                    "UPDATE users "
                    "SET first_name = COALESCE(first_name, TRIM(SUBSTR(full_name, 1, INSTR(full_name || ' ', ' ') - 1)))"
                )
            )
            connection.execute(
                text(
                    "UPDATE users "
                    "SET last_name = COALESCE(last_name, NULLIF(TRIM(SUBSTR(full_name, INSTR(full_name || ' ', ' ') + 1)), ''))"
                )
            )
            connection.execute(
                text(
                    "UPDATE users "
                    "SET registration_source = COALESCE(registration_source, 'user_portal')"
                )
            )
            connection.execute(
                text(
                    "UPDATE users "
                    "SET email_verified = COALESCE(email_verified, 0)"
                )
            )

    existing_indexes_by_table: dict[str, set[str]] = {}
    for table_name in ("issues", "workers", "admin_users", "users"):
        if not inspector.has_table(table_name):
            continue
        try:
            existing_indexes_by_table[table_name] = {
                item.get("name")
                for item in inspector.get_indexes(table_name)
                if item.get("name")
            }
        except Exception:
            existing_indexes_by_table[table_name] = set()

    index_ddls: list[tuple[str, str, str]] = [
        ("issues", "ix_issues_admin_deleted_status", "CREATE INDEX ix_issues_admin_deleted_status ON issues (admin_deleted, status)"),
        ("issues", "ix_issues_assigned_department", "CREATE INDEX ix_issues_assigned_department ON issues (assigned_department)"),
        ("issues", "ix_issues_assigned_worker_id", "CREATE INDEX ix_issues_assigned_worker_id ON issues (assigned_worker_id)"),
        ("issues", "ix_issues_worker_status", "CREATE INDEX ix_issues_worker_status ON issues (worker_status)"),
        ("issues", "ix_issues_user_created_at", "CREATE INDEX ix_issues_user_created_at ON issues (user_id, created_at)"),
        ("issues", "ix_issues_updated_at", "CREATE INDEX ix_issues_updated_at ON issues (updated_at)"),
        ("workers", "ix_workers_worker_id", "CREATE INDEX ix_workers_worker_id ON workers (worker_id)"),
        ("workers", "ix_workers_department_worker_id", "CREATE INDEX ix_workers_department_worker_id ON workers (department, worker_id)"),
        ("admin_users", "ix_admin_users_username", "CREATE INDEX ix_admin_users_username ON admin_users (username)"),
        ("users", "ix_users_email_is_active", "CREATE INDEX ix_users_email_is_active ON users (email, is_active)"),
    ]

    with engine.begin() as connection:
        for table_name, index_name, ddl in index_ddls:
            if not inspector.has_table(table_name):
                continue
            if index_name in existing_indexes_by_table.get(table_name, set()):
                continue
            statement = ddl
            if dialect_name == "sqlite":
                statement = ddl.replace("CREATE INDEX ", "CREATE INDEX IF NOT EXISTS ", 1)
            connection.execute(text(statement))


ensure_schema_updates()

app = FastAPI()

panel_event_subscribers: set[Queue] = set()
panel_event_lock = threading.Lock()
sqlite_write_lock = threading.Lock()
cache_lock = threading.Lock()
response_cache_store: dict[str, dict] = {}

try:
    import redis  # type: ignore
except Exception:
    redis = None

CACHE_REDIS_URL = os.getenv("CACHE_REDIS_URL", "").strip()
CACHE_DEFAULT_TTL_SECONDS = max(1, int(os.getenv("CACHE_DEFAULT_TTL_SECONDS", "5")))
_cache_client = None


def get_cache_client():
    global _cache_client
    if _cache_client is not None:
        return _cache_client
    if not CACHE_REDIS_URL or redis is None:
        _cache_client = False
        return None
    try:
        _cache_client = redis.Redis.from_url(CACHE_REDIS_URL, decode_responses=True)
        _cache_client.ping()
        return _cache_client
    except Exception:
        _cache_client = False
        return None


def cache_get_json(key: str):
    client = get_cache_client()
    if client is not None:
        try:
            payload = client.get(key)
            return json.loads(payload) if payload else None
        except Exception:
            return None

    now = time.time()
    with cache_lock:
        item = response_cache_store.get(key)
        if not item:
            return None
        if item["expires_at"] <= now:
            response_cache_store.pop(key, None)
            return None
        return item["value"]


def cache_set_json(key: str, value, ttl_seconds: int = CACHE_DEFAULT_TTL_SECONDS):
    client = get_cache_client()
    if client is not None:
        try:
            client.setex(key, max(1, ttl_seconds), json.dumps(value, ensure_ascii=True, default=str))
            return
        except Exception:
            pass

    with cache_lock:
        response_cache_store[key] = {
            "value": value,
            "expires_at": time.time() + max(1, ttl_seconds),
        }


def cache_delete_prefix(prefix: str):
    client = get_cache_client()
    if client is not None:
        try:
            keys = list(client.scan_iter(match=f"{prefix}*"))
            if keys:
                client.delete(*keys)
            return
        except Exception:
            pass

    with cache_lock:
        stale_keys = [key for key in response_cache_store if key.startswith(prefix)]
        for key in stale_keys:
            response_cache_store.pop(key, None)


def get_or_compute_cached_json(key: str, ttl_seconds: int, builder):
    cached = cache_get_json(key)
    if cached is not None:
        return cached
    value = builder()
    cache_set_json(key, value, ttl_seconds)
    return value


def sqlite_write_guard():
    return sqlite_write_lock if IS_SQLITE else nullcontext()


def extract_rate_limit_subject(request: Request) -> str:
    authorization = request.headers.get("authorization", "").strip()
    token = ""
    if authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif request.cookies.get("user_token"):
        token = request.cookies.get("user_token", "").strip()
    elif request.cookies.get("worker_token"):
        token = request.cookies.get("worker_token", "").strip()
    if token:
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            token_type = data.get("type") or "user"
            subject = data.get("sub")
            if subject:
                return f"{token_type}:{subject}"
        except Exception:
            pass
    forwarded_for = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    client_host = forwarded_for or (request.client.host if request.client else "unknown")
    return f"ip:{client_host}"


def get_rate_limit_for_request(request: Request) -> Optional[int]:
    path = request.url.path
    if path.startswith(("/docs", "/openapi", "/redoc", "/uploads", "/receipt", "/qr", "/favicon")):
        return None
    if request.method == "OPTIONS":
        return None
    if request.method == "GET" and (
        path == "/panel/events"
        or path.startswith("/iot/")
        or path in {"/api/sensors/live", "/api/sensors/history", "/api/location-data", "/api/incidents", "/reports"}
    ):
        return None
    if path == "/issues" and request.method == "POST":
        return MAX_ISSUE_SUBMISSIONS_PER_MINUTE
    if path.startswith(("/admin", "/worker")):
        return None

    is_local_request = request_is_localhost(request)
    if path in {"/iot/data", "/iot/log", "/iot/logs", "/iot/logs/", "/iot/latest", "/iot/live"}:
        return None if is_local_request else MAX_AUTHENTICATED_REQUESTS_PER_MINUTE
    if request.method == "GET" and path in {"/issues", "/api/sensors/live", "/api/incidents", "/api/alerts"}:
        return None if is_local_request else MAX_AUTHENTICATED_REQUESTS_PER_MINUTE
    if path in {
        "/auth/login",
        "/login",
        "/auth/register",
        "/send-otp",
        "/verify-otp",
        "/reset-password",
        "/auth/forgot-password/request",
        "/auth/forgot-password/verify",
        "/auth/forgot-password/reset",
    }:
        return MAX_AUTH_REQUESTS_PER_MINUTE
    if request.headers.get("authorization") or request.cookies.get("user_token") or request.cookies.get("worker_token"):
        return MAX_AUTHENTICATED_REQUESTS_PER_MINUTE
    return MAX_PUBLIC_REQUESTS_PER_MINUTE


def build_rate_limited_response(retry_after_seconds: int) -> Response:
    payload = {
        "detail": "Too many requests. Please wait a moment and try again.",
        "retry_after_seconds": retry_after_seconds,
    }
    response = JSONResponse(status_code=429, content=payload)
    response.headers["Retry-After"] = str(retry_after_seconds)
    return response


@app.middleware("http")
async def rate_limit_public_requests(request: Request, call_next):
    limit = get_rate_limit_for_request(request)
    if not limit:
        return await call_next(request)

    key = (request.url.path, extract_rate_limit_subject(request))
    now = time.time()
    with _rate_limit_lock:
        bucket = [stamp for stamp in _rate_limit_bucket.get(key, []) if now - stamp < 60]
        if len(bucket) >= limit:
            retry_after = max(1, int(60 - (now - bucket[0])))
            _rate_limit_bucket[key] = bucket
            return build_rate_limited_response(retry_after)
        bucket.append(now)
        _rate_limit_bucket[key] = bucket

    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(_: Request, exc: RequestValidationError):
    messages = []
    for error in exc.errors():
        message = str(error.get("msg") or "Invalid request")
        if message not in messages:
            messages.append(message)
    return JSONResponse(
        status_code=400,
        content={"detail": messages[0] if messages else "Invalid request payload"},
    )


def publish_panel_event(event_type: str, payload: Optional[dict] = None) -> None:
    for prefix in (
        "user-dashboard:",
        "user-stats:",
        "user-issues:",
        "admin-panel:",
        "worker-panel:",
    ):
        cache_delete_prefix(prefix)

    event = {
        "type": event_type,
        "payload": payload or {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    stale_subscribers = []
    with panel_event_lock:
        subscribers = list(panel_event_subscribers)
    for subscriber in subscribers:
        try:
            subscriber.put_nowait(event)
        except Full:
            try:
                subscriber.get_nowait()
            except Empty:
                pass
            try:
                subscriber.put_nowait(event)
            except Exception:
                stale_subscribers.append(subscriber)
        except Exception:
            stale_subscribers.append(subscriber)
    if stale_subscribers:
        with panel_event_lock:
            for subscriber in stale_subscribers:
                panel_event_subscribers.discard(subscriber)


def panel_event_stream():
    subscriber = Queue(maxsize=32)
    with panel_event_lock:
        panel_event_subscribers.add(subscriber)
    try:
        while True:
            try:
                event = subscriber.get(timeout=15)
                yield f"data: {json.dumps(event, ensure_ascii=True)}\n\n"
            except Empty:
                yield ": keep-alive\n\n"
    finally:
        with panel_event_lock:
            panel_event_subscribers.discard(subscriber)


async def websocket_panel_event_stream(websocket: WebSocket):
    subscriber = Queue(maxsize=64)
    with panel_event_lock:
        panel_event_subscribers.add(subscriber)
    try:
        while True:
            try:
                event = await asyncio.to_thread(subscriber.get, True, 15)
                await websocket.send_json(event)
            except Empty:
                await websocket.send_json({"type": "keep-alive", "payload": {}, "timestamp": datetime.utcnow().isoformat()})
    finally:
        with panel_event_lock:
            panel_event_subscribers.discard(subscriber)


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


IOT_AUTO_START = env_flag("IOT_AUTO_START", True)
IOT_SOURCE = os.getenv("IOT_SOURCE", "serial").strip().lower()
IOT_SERIAL_PORT = os.getenv("SERIAL_PORT", "rfc2217://127.0.0.1:4000")
IOT_SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", "115200"))
IOT_PUSH_INTERVAL = int(os.getenv("IOT_PUSH_INTERVAL", "10"))
SENSOR_SIMULATION_ENABLED = env_flag("SENSOR_SIMULATION_ENABLED", True)
SENSOR_SIM_INTERVAL_SECONDS = max(2, int(os.getenv("SENSOR_SIM_INTERVAL_SECONDS", "3")))
IOT_TCP_ENDPOINT = os.getenv("IOT_TCP", "127.0.0.1:9010")
IOT_LISTEN_ENDPOINT = os.getenv("IOT_LISTEN", "0.0.0.0:9010")
IOT_API_URL = os.getenv("IOT_API_URL", "http://127.0.0.1:8000/iot/data")
IOT_LOG_URL = os.getenv("IOT_LOG_URL", "http://127.0.0.1:8000/iot/log")
OPENWEATHERMAP_API_KEY = (
    os.getenv("OPENWEATHER_API_KEY", "").strip()
    or os.getenv("OPENWEATHERMAP_API_KEY", "").strip()
)
print(f"[OPENWEATHER] API KEY loaded: {bool(OPENWEATHERMAP_API_KEY)}")

_iot_bridge_thread = None
_sensor_simulation_thread = None

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip()
APP_TIMEZONE_NAME = os.getenv("APP_TIMEZONE", "Asia/Kolkata").strip() or "Asia/Kolkata"
PDF_FONT_REGULAR = "Helvetica"
PDF_FONT_BOLD = "Helvetica-Bold"
PDF_FONT_ITALIC = "Helvetica-Oblique"


def resolve_app_timezone():
    try:
        return ZoneInfo(APP_TIMEZONE_NAME)
    except ZoneInfoNotFoundError:
        # Fallback for Windows/Python installs without tzdata.
        if APP_TIMEZONE_NAME.lower() in {"asia/kolkata", "asia/calcutta", "ist"}:
            return timezone(timedelta(hours=5, minutes=30))
        return timezone.utc


APP_TIMEZONE = resolve_app_timezone()


def setup_pdf_fonts():
    global PDF_FONT_REGULAR, PDF_FONT_BOLD, PDF_FONT_ITALIC

    if PDF_FONT_REGULAR != "Helvetica":
        return

    candidates = [
        (
            "SegoeUI",
            "SegoeUI-Bold",
            "SegoeUI-Italic",
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\segoeuii.ttf",
        ),
        (
            "ArialUnicode",
            "ArialUnicode-Bold",
            "ArialUnicode-Italic",
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\ariali.ttf",
        ),
    ]

    for regular_name, bold_name, italic_name, regular_path, bold_path, italic_path in candidates:
        if not os.path.exists(regular_path):
            continue
        try:
            pdfmetrics.registerFont(TTFont(regular_name, regular_path))
            if os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
            else:
                bold_name = regular_name
            if os.path.exists(italic_path):
                pdfmetrics.registerFont(TTFont(italic_name, italic_path))
            else:
                italic_name = regular_name
            PDF_FONT_REGULAR = regular_name
            PDF_FONT_BOLD = bold_name
            PDF_FONT_ITALIC = italic_name
            return
        except Exception:
            continue


def to_app_timezone(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(APP_TIMEZONE)


def format_app_datetime(value: Optional[datetime], fmt: str = "%d-%m-%Y %I:%M %p") -> str:
    localized = to_app_timezone(value)
    return localized.strftime(fmt) if localized else "N/A"


def isoformat_app_datetime(value: Optional[datetime]) -> Optional[str]:
    localized = to_app_timezone(value)
    return localized.isoformat() if localized else None


def wrap_pdf_text(pdf, text: str, font_name: str, font_size: int, max_width: float) -> list[str]:
    if text is None:
        return [""]

    normalized = str(text).replace("\r\n", "\n").replace("\r", "\n")
    lines = []

    for paragraph in normalized.split("\n"):
        if not paragraph:
            lines.append("")
            continue

        words = paragraph.split(" ")
        current = ""

        for word in words:
            trial = f"{current} {word}".strip()
            if current and pdf.stringWidth(trial, font_name, font_size) <= max_width:
                current = trial
                continue
            if not current and pdf.stringWidth(word, font_name, font_size) <= max_width:
                current = word
                continue
            if current:
                lines.append(current)
                current = ""
            if pdf.stringWidth(word, font_name, font_size) <= max_width:
                current = word
                continue

            chunk = ""
            for char in word:
                chunk_trial = f"{chunk}{char}"
                if chunk and pdf.stringWidth(chunk_trial, font_name, font_size) > max_width:
                    lines.append(chunk)
                    chunk = char
                else:
                    chunk = chunk_trial
            current = chunk

        if current:
            lines.append(current)

    return lines or [""]


def detect_lan_ip() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        try:
            fallback_ip = socket.gethostbyname(socket.gethostname())
            if fallback_ip and not fallback_ip.startswith("127."):
                return fallback_ip
        except Exception:
            pass
    return ""


def resolve_api_base_url(request: Request = None) -> str:
    if request is not None:
        return str(request.base_url).rstrip("/")
    return "http://127.0.0.1:8000"


def resolve_public_scan_base_url(request: Request = None) -> str:
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL.rstrip("/")
    if request is not None:
        parsed = urlparse(str(request.base_url))
        host = parsed.hostname or ""
        if host in {"127.0.0.1", "localhost", "0.0.0.0"}:
            lan_ip = detect_lan_ip()
            if lan_ip:
                return f"{parsed.scheme}://{lan_ip}:{parsed.port or 8000}"
        return str(request.base_url).rstrip("/")
    return "http://127.0.0.1:8000"


def build_scan_url(complaint_number: str, request: Request = None, public_base_url: str = None) -> str:
    base_url = (public_base_url or "").strip().rstrip("/")
    if not base_url:
        base_url = resolve_public_scan_base_url(request)
    return f"{base_url}/scan/{complaint_number}"


def start_iot_bridge_if_enabled():
    global _iot_bridge_thread

    if not IOT_AUTO_START:
        print("[IOT BRIDGE] Auto-start disabled (IOT_AUTO_START=false).")
        return

    if _iot_bridge_thread and _iot_bridge_thread.is_alive():
        return

    try:
        from iot import serial_reader
    except Exception as exc:
        serial_reader_path = os.path.join(BASE_DIR, "iot", "serial_reader.py")
        try:
            spec = importlib.util.spec_from_file_location("serial_reader_local", serial_reader_path)
            if not spec or not spec.loader:
                print(f"[IOT BRIDGE] Unable to load serial reader module from {serial_reader_path}")
                return
            serial_reader = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(serial_reader)
        except Exception as load_exc:
            print(f"[IOT BRIDGE] Unable to import serial reader: {exc}; fallback failed: {load_exc}")
            return

    if serial_reader.requests is None:
        print("[IOT BRIDGE] requests package missing. Install backend requirements.")
        return

    if IOT_SOURCE == "stdin":
        print("[IOT BRIDGE] Auto-start skipped for stdin mode. Use serial/tcp/tcp-server mode.")
        return

    def _runner():
        print(
            f"[IOT BRIDGE] Starting source={IOT_SOURCE} api={IOT_API_URL} "
            f"log={IOT_LOG_URL} interval={IOT_PUSH_INTERVAL}s"
        )
        try:
            if IOT_SOURCE == "tcp":
                serial_reader.run_tcp_mode(IOT_API_URL, IOT_LOG_URL, IOT_TCP_ENDPOINT, IOT_PUSH_INTERVAL)
            elif IOT_SOURCE == "tcp-server":
                serial_reader.run_tcp_server_mode(
                    IOT_API_URL, IOT_LOG_URL, IOT_LISTEN_ENDPOINT, IOT_PUSH_INTERVAL
                )
            else:
                serial_reader.run_serial_mode(
                    IOT_API_URL,
                    IOT_LOG_URL,
                    IOT_SERIAL_BAUD,
                    IOT_SERIAL_PORT,
                    IOT_PUSH_INTERVAL,
                )
        except Exception as exc:
            print(f"[IOT BRIDGE] Stopped with error: {exc}")

    _iot_bridge_thread = threading.Thread(target=_runner, daemon=True, name="iot-bridge")
    _iot_bridge_thread.start()


def classify_traffic_status(value) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "Data unavailable"
    if numeric >= 24:
        return "CRITICAL - Severe gridlock"
    if numeric >= 16:
        return "WARNING - Heavy congestion"
    if numeric >= 8:
        return "MODERATE - Slow moving traffic"
    return "Safe"


def classify_parking_status(available, parking_a: Optional[str] = None, parking_b: Optional[str] = None) -> str:
    if "ILLEGAL" in str(parking_a or "").upper() or "ILLEGAL" in str(parking_b or "").upper():
        return "CRITICAL - Illegal parking detected"
    numeric = _safe_float(available)
    if numeric is None:
        return "Data unavailable"
    if numeric <= 0:
        return "CRITICAL - Parking full"
    if numeric <= 1:
        return "WARNING - One slot left"
    return "Safe"


def start_sensor_simulation_if_enabled():
    global _sensor_simulation_thread

    if not SENSOR_SIMULATION_ENABLED:
        print("[SENSOR SIM] Disabled (SENSOR_SIMULATION_ENABLED=false).")
        return

    if _sensor_simulation_thread and _sensor_simulation_thread.is_alive():
        return

    central_sensor_engine.start()
    sync_globals_from_central_sensor_engine()
    rebuild_incident_records_from_sensor_history()
    print(f"[SENSOR SIM] Central sensor engine running interval={SENSOR_SIM_INTERVAL_SECONDS}s")


def generate_qr_png_bytes(
    complaint_number: str,
    request: Request = None,
    public_base_url: str = None,
) -> bytes:
    scan_url = build_scan_url(complaint_number, request, public_base_url)
    qr_image = qrcode.make(scan_url)
    buffer = BytesIO()
    qr_image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def write_qr_png_file(
    complaint_number: str,
    request: Request = None,
    public_base_url: str = None,
) -> bytes:
    png_bytes = generate_qr_png_bytes(
        complaint_number,
        request=request,
        public_base_url=public_base_url,
    )
    with open(qr_file_path(complaint_number), "wb") as handle:
        handle.write(png_bytes)
    return png_bytes


def submission_status_file_path(complaint_number: str) -> str:
    safe_number = re.sub(r"[^A-Za-z0-9._-]+", "_", str(complaint_number or "").strip()) or "unknown"
    return os.path.join(SUBMISSION_STATUS_FOLDER, f"{safe_number}.json")


def receipt_file_path(complaint_number: str) -> str:
    safe_number = re.sub(r"[^A-Za-z0-9._-]+", "_", str(complaint_number or "").strip()) or "unknown"
    return os.path.join(RECEIPT_FOLDER, f"receipt_{safe_number}.pdf")


def qr_file_path(complaint_number: str) -> str:
    safe_number = re.sub(r"[^A-Za-z0-9._-]+", "_", str(complaint_number or "").strip()) or "unknown"
    return os.path.join(QR_FOLDER, f"qr_{safe_number}.png")


def load_submission_status(complaint_number: str) -> dict:
    path = submission_status_file_path(complaint_number)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_submission_status(complaint_number: str, payload: dict) -> dict:
    current = load_submission_status(complaint_number)
    next_payload = {**current, **(payload or {})}
    next_payload["updated_at"] = datetime.utcnow().isoformat()
    path = submission_status_file_path(complaint_number)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(next_payload, handle, ensure_ascii=True)
    return next_payload


def initialize_submission_status(issue: Issue, *, has_uploads: bool) -> dict:
    return save_submission_status(
        issue.complaint_number,
        {
            "issue_id": issue.id,
            "complaint_number": issue.complaint_number,
            "submitted_at": isoformat_app_datetime(issue.created_at),
            "media_expected": bool(has_uploads),
            "media_ready": not has_uploads,
            "qr_ready": False,
            "receipt_ready": False,
            "notification_ready": False,
            "status": "processing",
            "error": None,
        },
    )


def serialize_submission_status(issue: Issue) -> dict:
    raw_status = load_submission_status(issue.complaint_number)
    media_expected = bool(raw_status.get("media_expected"))
    media_ready = bool(raw_status.get("media_ready", not media_expected))
    qr_ready = bool(raw_status.get("qr_ready")) or os.path.exists(qr_file_path(issue.complaint_number))
    receipt_ready = bool(raw_status.get("receipt_ready")) or os.path.exists(receipt_file_path(issue.complaint_number))
    notification_ready = bool(raw_status.get("notification_ready"))
    error = raw_status.get("error")
    status = raw_status.get("status") or ("ready" if media_ready and qr_ready and receipt_ready else "processing")
    qr_url = f"/qr/{issue.complaint_number}" if qr_ready else None
    receipt_url = f"/receipt/{issue.complaint_number}" if receipt_ready else None
    return {
        "issue_id": issue.id,
        "complaint_number": issue.complaint_number,
        "status": status,
        "media_expected": media_expected,
        "media_ready": media_ready,
        "qr_ready": qr_ready,
        "receipt_ready": receipt_ready,
        "notification_ready": notification_ready,
        "qr_code_url": qr_url,
        "receipt_url": receipt_url,
        "error": error,
        "submitted_at": raw_status.get("submitted_at") or isoformat_app_datetime(issue.created_at),
        "updated_at": raw_status.get("updated_at"),
    }


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Force Swagger UI to render a real multi-file picker for /issues.
    try:
        req_schema = openapi_schema["paths"]["/issues"]["post"]["requestBody"]["content"]["multipart/form-data"]["schema"]
        if "$ref" in req_schema:
            schema_name = req_schema["$ref"].split("/")[-1]
            files_field = openapi_schema["components"]["schemas"][schema_name]["properties"]["files"]
            files_field.clear()
            files_field.update(
                {
                    "title": "Files",
                    "description": "Choose one or more files of any format (you can multi-select in file picker).",
                    "type": "array",
                    "items": {"type": "string", "format": "binary"},
                }
            )
            openapi_schema["paths"]["/issues"]["post"]["requestBody"]["content"]["multipart/form-data"]["encoding"] = {
                "files": {"style": "form", "explode": True}
            }
    except KeyError:
        pass

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/openapi.json", include_in_schema=False)
def openapi_json():
    return app.openapi()


@app.get("/auth/config-status")
def auth_config_status():
    def masked(value: str):
        if not value:
            return ""
        if len(value) <= 6:
            return "***"
        return f"{value[:3]}***{value[-3:]}"

    return {
        "sms_provider": SMS_PROVIDER,
        "twilio_account_sid_configured": bool(TWILIO_ACCOUNT_SID) and not is_placeholder_value(TWILIO_ACCOUNT_SID),
        "twilio_auth_token_configured": bool(TWILIO_AUTH_TOKEN) and not is_placeholder_value(TWILIO_AUTH_TOKEN),
        "twilio_from_number_configured": bool(TWILIO_FROM_NUMBER) and not is_placeholder_value(TWILIO_FROM_NUMBER),
        "twilio_account_sid_preview": masked(TWILIO_ACCOUNT_SID),
        "twilio_from_number_preview": masked(TWILIO_FROM_NUMBER),
        "otp_debug_mode": OTP_DEBUG_MODE,
    }

@app.get("/")
def home():
    return {"message": "Urban Sentinel API is running"}


@app.get("/panel/events", include_in_schema=False)
def panel_events():
    return StreamingResponse(panel_event_stream(), media_type="text/event-stream")


@app.websocket("/ws/admin")
async def admin_panel_websocket(websocket: WebSocket):
    token = websocket.cookies.get("admin_token") or websocket.query_params.get("token") or ""
    db = SessionLocal()
    try:
        decode_admin_token(token, db)
    except HTTPException:
        db.close()
        await websocket.close(code=1008)
        return
    finally:
        if db:
            db.close()

    await websocket.accept()
    try:
        await websocket_panel_event_stream(websocket)
    except WebSocketDisconnect:
        return


@app.websocket("/ws/worker/{worker_id}")
async def worker_panel_websocket(worker_id: str, websocket: WebSocket):
    token = websocket.cookies.get("worker_token") or websocket.query_params.get("token") or ""
    db = SessionLocal()
    try:
        worker = decode_worker_token(token, db)
        if str(worker.worker_id or "").strip().lower() != str(worker_id or "").strip().lower():
            raise HTTPException(status_code=403, detail="Worker access denied")
    except HTTPException:
        db.close()
        await websocket.close(code=1008)
        return
    finally:
        if db:
            db.close()

    await websocket.accept()
    try:
        await websocket_panel_event_stream(websocket)
    except WebSocketDisconnect:
        return


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    favicon_path = os.path.join(BASE_DIR, "assets", "logo.png")
    if not os.path.exists(favicon_path):
        raise HTTPException(status_code=404, detail="Favicon not found")
    return FileResponse(favicon_path, media_type="image/png")


@app.on_event("startup")
def on_startup():
    sync_existing_users_to_devices()
    start_iot_bridge_if_enabled()
    start_sensor_simulation_if_enabled()


@app.get("/iot/bridge-status")
def iot_bridge_status():
    running = bool(_iot_bridge_thread and _iot_bridge_thread.is_alive())
    return {
        "auto_start": IOT_AUTO_START,
        "source": IOT_SOURCE,
        "running": running,
        "serial_port": IOT_SERIAL_PORT,
        "serial_baud": IOT_SERIAL_BAUD,
        "tcp_endpoint": IOT_TCP_ENDPOINT,
        "listen_endpoint": IOT_LISTEN_ENDPOINT,
        "api_url": IOT_API_URL,
        "log_url": IOT_LOG_URL,
    }
# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://urban-sentinel-ls4w.onrender.com",
        "https://churn-squishy-bless.ngrok-free.dev",
    ],
    allow_origin_regex=r"https://.*\.ngrok-free\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Static Upload Folder
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
GENERATED_ASSETS_FOLDER = os.path.join(BASE_DIR, "generated_assets")
RECEIPT_FOLDER = os.path.join(GENERATED_ASSETS_FOLDER, "receipts")
QR_FOLDER = os.path.join(GENERATED_ASSETS_FOLDER, "qr_codes")
SUBMISSION_STATUS_FOLDER = os.path.join(GENERATED_ASSETS_FOLDER, "submission_status")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RECEIPT_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs(SUBMISSION_STATUS_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")
# -----------------------------
# Database Dependency
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def admin_visible_issue_filter():
    return or_(Issue.admin_deleted == 0, Issue.admin_deleted.is_(None))


def split_full_name(full_name: str) -> tuple[str | None, str | None]:
    parts = [part for part in str(full_name or "").strip().split() if part]
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], " ".join(parts[1:])


def normalize_device_identifier(raw_value: Optional[str], fallback_seed: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._:-]+", "-", str(raw_value or "").strip()).strip("-")
    if cleaned:
        return cleaned[:120]
    return f"user-{re.sub(r'[^a-zA-Z0-9]+', '-', fallback_seed).strip('-').lower() or 'unknown'}"


def upsert_registered_device(
    db: Session,
    *,
    user: Optional[User],
    device_identifier: str,
    device_name: Optional[str] = None,
    device_type: Optional[str] = None,
    device_model: Optional[str] = None,
    platform: Optional[str] = None,
    os_version: Optional[str] = None,
    firmware_version: Optional[str] = None,
    app_version: Optional[str] = None,
    login_email: Optional[str] = None,
    login_phone: Optional[str] = None,
    ip_address: Optional[str] = None,
    mac_address: Optional[str] = None,
    location_name: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> Device:
    device = db.query(Device).filter(Device.device_identifier == device_identifier).first()
    now = utc_now_naive()
    if device is None:
        device = Device(device_identifier=device_identifier)
        db.add(device)

    device.user_id = user.id if user else device.user_id
    device.device_name = device_name or device.device_name
    device.device_type = device_type or device.device_type or "UNKNOWN"
    device.device_model = device_model or device.device_model
    device.platform = platform or device.platform
    device.os_version = os_version or device.os_version
    device.firmware_version = firmware_version or device.firmware_version
    device.app_version = app_version or device.app_version
    device.login_email = login_email or device.login_email
    device.login_phone = login_phone or device.login_phone
    device.ip_address = ip_address or device.ip_address
    device.mac_address = mac_address or device.mac_address
    device.location_name = location_name or device.location_name
    device.latitude = latitude if latitude is not None else device.latitude
    device.longitude = longitude if longitude is not None else device.longitude
    device.is_active = True
    device.last_seen_at = now
    device.updated_at = now
    if device.created_at is None:
        device.created_at = now
    return device


def sync_user_registration_details(db: Session, user: User, payload: RegisterPayload, device_identifier: str):
    first_name, last_name = split_full_name(payload.full_name)
    user.first_name = first_name or user.first_name
    user.last_name = last_name or user.last_name
    user.registration_source = user.registration_source or "user_portal"
    user.registered_device_identifier = device_identifier
    user.registered_device_name = payload.device_name or user.registered_device_name
    user.registered_device_type = payload.device_type or user.registered_device_type
    user.registered_device_model = payload.device_model or user.registered_device_model
    user.registered_device_platform = payload.device_platform or user.registered_device_platform
    user.registered_device_os_version = payload.device_os_version or user.registered_device_os_version
    user.registered_app_version = payload.app_version or user.registered_app_version
    user.registered_ip_address = payload.ip_address or user.registered_ip_address


SENSOR_READING_DEFINITIONS = {
    "temperature": {"label": "Temperature", "unit": "C"},
    "humidity": {"label": "Humidity", "unit": "%"},
    "air_smoke": {"label": "Air Quality Smoke", "unit": "ppm"},
    "flood_distance": {"label": "Flood Distance", "unit": "cm"},
    "flood_level": {"label": "Flood Level", "unit": "%"},
    "traffic_lane1": {"label": "Traffic Lane 1", "unit": "count"},
    "traffic_lane2": {"label": "Traffic Lane 2", "unit": "count"},
    "traffic_total": {"label": "Traffic Total", "unit": "count"},
    "noise_level": {"label": "Noise Level", "unit": "dB"},
    "light_percent": {"label": "Light Intensity", "unit": "%"},
    "bin_distance": {"label": "Waste Bin Distance", "unit": "cm"},
    "bin_fill": {"label": "Waste Bin Fill", "unit": "%"},
    "rain_percent": {"label": "Rain Intensity", "unit": "%"},
    "fire_smoke": {"label": "Fire Smoke", "unit": "ppm"},
    "parking_available": {"label": "Parking Availability", "unit": "slots"},
}

SENSOR_STATUS_FIELDS = {
    "temperature": "temp_status",
    "humidity": "temp_status",
    "air_smoke": "air_status",
    "flood_distance": "flood_status",
    "flood_level": "flood_status",
    "traffic_lane1": "traffic_status",
    "traffic_lane2": "traffic_status",
    "traffic_total": "traffic_status",
    "noise_level": "noise_status",
    "light_percent": "light_status",
    "bin_distance": "bin_status",
    "bin_fill": "bin_status",
    "rain_percent": "rain_status",
    "fire_smoke": "fire_status",
    "parking_available": "parking_status",
}


def persist_sensor_rows(payload: dict):
    device_identifier = normalize_device_identifier(
        payload.get("device_identifier"),
        payload.get("location") or payload.get("ip_address") or "sensor-gateway",
    )
    recorded_at = utc_now_naive()
    timestamp_value = payload.get("timestamp")
    if timestamp_value:
        try:
            recorded_at = datetime.fromisoformat(str(timestamp_value).replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            recorded_at = utc_now_naive()

    with sqlite_write_guard():
        db = SessionLocal()
        try:
            linked_user = None
            login_email = normalize_identifier(payload.get("login_email") or payload.get("email") or "")
            if login_email:
                linked_user = db.query(User).filter(User.email == login_email).first()

            device = upsert_registered_device(
                db,
                user=linked_user,
                device_identifier=device_identifier,
                device_name=payload.get("device_name"),
                device_type=payload.get("device_type") or "IOT_SENSOR_DEVICE",
                device_model=payload.get("device_model"),
                platform=payload.get("device_platform"),
                os_version=payload.get("device_os_version"),
                firmware_version=payload.get("firmware_version"),
                app_version=payload.get("app_version"),
                login_email=login_email or None,
                login_phone=payload.get("phone"),
                ip_address=payload.get("ip_address"),
                mac_address=payload.get("mac_address"),
                location_name=payload.get("location"),
                latitude=smart_safe_float(payload.get("latitude")),
                longitude=smart_safe_float(payload.get("longitude")),
            )
            db.flush()

            for sensor_name, meta in SENSOR_READING_DEFINITIONS.items():
                raw_value = payload.get(sensor_name)
                if raw_value is None:
                    continue
                reading = (
                    db.query(SensorReading)
                    .filter(
                        SensorReading.device_identifier == device_identifier,
                        SensorReading.sensor_name == sensor_name,
                    )
                    .first()
                )
                if reading is None:
                    reading = SensorReading(
                        device_id=device.id,
                        device_identifier=device_identifier,
                        sensor_name=sensor_name,
                    )
                    db.add(reading)

                numeric_value = smart_safe_float(raw_value)
                reading.device_id = device.id
                reading.sensor_label = meta["label"]
                reading.current_reading = numeric_value
                reading.reading_text = str(raw_value)
                reading.unit = meta["unit"]
                reading.status = payload.get(SENSOR_STATUS_FIELDS.get(sensor_name))
                reading.location_name = payload.get("location")
                reading.latitude = smart_safe_float(payload.get("latitude"))
                reading.longitude = smart_safe_float(payload.get("longitude"))
                reading.recorded_at = recorded_at
                reading.updated_at = utc_now_naive()

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


def sync_existing_users_to_devices():
    with sqlite_write_guard():
        db = SessionLocal()
        try:
            users_to_sync = db.query(User).all()
            for user in users_to_sync:
                identifier = normalize_device_identifier(
                    user.registered_device_identifier,
                    user.email or user.phone or f"user-{user.id}",
                )
                upsert_registered_device(
                    db,
                    user=user,
                    device_identifier=identifier,
                    device_name=user.registered_device_name or f"{user.full_name}'s account",
                    device_type=user.registered_device_type or "REGISTERED_USER",
                    device_model=user.registered_device_model,
                    platform=user.registered_device_platform,
                    os_version=user.registered_device_os_version,
                    app_version=user.registered_app_version,
                    login_email=user.email,
                    login_phone=user.phone,
                    ip_address=user.registered_ip_address,
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

# -----------------------------
# JWT Config
# -----------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "").strip() or secrets.token_urlsafe(48)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
RESET_TOKEN_EXPIRE_MINUTES = 15
PASSWORD_SALT = os.getenv("PASSWORD_SALT", "").strip() or SECRET_KEY
OTP_DEBUG_MODE = os.getenv("OTP_DEBUG_MODE", "false").lower() == "true"
OTP_DELIVERY_CHANNEL = os.getenv("OTP_DELIVERY_CHANNEL", "auto").strip().lower()
SMS_PROVIDER = os.getenv("SMS_PROVIDER", "none").strip().lower()

MAIL_SERVER = os.getenv("MAIL_SERVER", "").strip()
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "").strip()
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "").strip()
MAIL_FROM = os.getenv("MAIL_FROM", MAIL_USERNAME).strip()
MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "true").strip().lower() == "true"
MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "false").strip().lower() == "true"
MAIL_TIMEOUT_SECONDS = float(os.getenv("MAIL_TIMEOUT_SECONDS", "5").strip() or "5")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "").strip()

FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY", "").strip()

MSG91_AUTH_KEY = os.getenv("MSG91_AUTH_KEY", "").strip()
MSG91_TEMPLATE_ID = os.getenv("MSG91_TEMPLATE_ID", "").strip()
MSG91_SENDER_ID = os.getenv("MSG91_SENDER_ID", "").strip()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

auth_bearer = HTTPBearer(auto_error=False)
MAX_PUBLIC_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_PUBLIC_PER_MINUTE", "60"))
MAX_AUTH_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_AUTH_PER_MINUTE", "12"))
MAX_ISSUE_SUBMISSIONS_PER_MINUTE = int(os.getenv("RATE_LIMIT_ISSUE_SUBMISSIONS_PER_MINUTE", "6"))
MAX_AUTHENTICATED_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_AUTHENTICATED_PER_MINUTE", "180"))
MAX_UPLOAD_FILES = int(os.getenv("MAX_UPLOAD_FILES", "6"))
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(8 * 1024 * 1024)))
ALLOWED_UPLOAD_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".pdf",
}
ALLOWED_UPLOAD_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "application/pdf",
}
_rate_limit_bucket: dict[tuple[str, str], list[float]] = {}
_rate_limit_lock = threading.Lock()


def is_placeholder_value(value: str) -> bool:
    if not value:
        return True
    lowered = value.lower()
    return (
        "xxxxxxxx" in lowered
        or "your_" in lowered
        or "replace" in lowered
        or lowered in {"none", "null"}
    )


def sanitize_text_input(value: Optional[str]) -> str:
    cleaned = " ".join(str(value or "").replace("\x00", " ").split())
    return cleaned.strip()


def validate_text_field(
    value: Optional[str],
    *,
    field_name: str,
    min_length: int = 1,
    max_length: int = 255,
) -> str:
    cleaned = sanitize_text_input(value)
    if not cleaned:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")
    if len(cleaned) < min_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be at least {min_length} characters",
        )
    if len(cleaned) > max_length:
        raise HTTPException(status_code=400, detail=f"{field_name} must be at most {max_length} characters")
    return cleaned


def validate_password_input(value: Optional[str], *, field_name: str = "Password", min_length: int = 8) -> str:
    password = str(value or "")
    if len(password) < min_length:
        raise HTTPException(status_code=400, detail=f"{field_name} must be at least {min_length} characters")
    if len(password) > 128:
        raise HTTPException(status_code=400, detail=f"{field_name} must be at most 128 characters")
    return password


def validate_email_input(value: Optional[str]) -> str:
    normalized = normalize_identifier(value or "")
    if not is_valid_email(normalized):
        raise HTTPException(status_code=400, detail="Enter a valid email")
    if len(normalized) > 255:
        raise HTTPException(status_code=400, detail="Email must be at most 255 characters")
    return normalized


def validate_phone_input(value: Optional[str], *, required: bool = True) -> Optional[str]:
    normalized = normalize_phone(value or "")
    if not normalized and not required:
        return None
    if not is_valid_phone(normalized):
        raise HTTPException(status_code=400, detail="Enter a valid phone number")
    return normalized


def validate_optional_text(value: Optional[str], *, max_length: int = 255) -> Optional[str]:
    cleaned = sanitize_text_input(value)
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise HTTPException(status_code=400, detail=f"Field must be at most {max_length} characters")
    return cleaned


def validate_issue_category(value: Optional[str]) -> str:
    cleaned = validate_text_field(value, field_name="Category", max_length=80)
    if cleaned not in ISSUE_CATEGORY_OPTIONS:
        raise HTTPException(status_code=400, detail="Choose a valid category")
    return cleaned


def validate_uploads(files: Optional[list[UploadFile]]) -> list[UploadFile]:
    upload_list = [item for item in (files or []) if item is not None]
    if len(upload_list) > MAX_UPLOAD_FILES:
        raise HTTPException(status_code=400, detail=f"You can upload up to {MAX_UPLOAD_FILES} files")

    for file in upload_list:
        filename = sanitize_text_input(file.filename or "")
        _, extension = os.path.splitext(filename.lower())
        if not filename or extension not in ALLOWED_UPLOAD_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Only JPG, PNG, WEBP, GIF, and PDF files are allowed")
        content_type = (file.content_type or "").strip().lower()
        if content_type and content_type not in ALLOWED_UPLOAD_CONTENT_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported file type uploaded")
    return upload_list


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

LEGACY_ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
LEGACY_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


AUTH_CACHE_TTL_SECONDS = max(60, ACCESS_TOKEN_EXPIRE_MINUTES * 60)


def build_user_identity(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "is_active": bool(user.is_active),
    }


def build_admin_identity(admin: AdminUser) -> dict:
    return {
        "id": admin.id,
        "username": admin.username,
        "full_name": admin.full_name,
    }


def build_worker_identity(worker: Worker) -> dict:
    return {
        "id": worker.id,
        "worker_id": worker.worker_id,
        "department": worker.department,
        "is_active": bool(worker.is_active),
        "created_at": isoformat_app_datetime(worker.created_at),
        "last_login_at": isoformat_app_datetime(worker.last_login_at),
    }


def build_identity_token_payload(identity_type: str, identity: dict) -> dict:
    return {
        "sub": str(identity["id"]),
        "type": identity_type,
        "identity": {
            key: value
            for key, value in identity.items()
            if key != "id"
        },
    }


def create_reset_token(identifier: str):
    expire = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": identifier, "type": "reset", "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def hash_password(password: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        PASSWORD_SALT.encode("utf-8"),
        100_000
    )
    return digest.hex()


def verify_scrypt_password(password: str, password_hash: str) -> bool:
    if not password_hash or not password_hash.startswith("scrypt$"):
        return False

    parts = password_hash.split("$")
    salt = None
    expected = None
    n = 2**14
    r = 8
    p = 1

    if len(parts) == 6:
        _, n_value, r_value, p_value, encoded_salt, encoded_hash = parts
        try:
            n = int(n_value)
            r = int(r_value)
            p = int(p_value)
        except ValueError:
            return False
    elif len(parts) == 3:
        _, encoded_salt, encoded_hash = parts
    else:
        return False

    try:
        salt = bytes.fromhex(encoded_salt)
    except ValueError:
        try:
            salt = base64.urlsafe_b64decode(encoded_salt.encode("utf-8"))
        except Exception:
            return False

    try:
        expected = bytes.fromhex(encoded_hash)
    except ValueError:
        try:
            expected = base64.urlsafe_b64decode(encoded_hash.encode("utf-8"))
        except Exception:
            return False

    try:
        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=len(expected),
        )
    except Exception:
        return False

    return hmac.compare_digest(derived, expected)


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False

    if hmac.compare_digest(hash_password(password), password_hash):
        return True

    if verify_scrypt_password(password, password_hash):
        return True

    return False


def hash_reset_code(code: str) -> str:
    digest = hashlib.sha256(f"{code}:{PASSWORD_SALT}".encode("utf-8")).hexdigest()
    return digest


def normalize_identifier(value: str) -> str:
    return (value or "").strip().lower()


def normalize_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone or "")


def phones_match(left: str, right: str) -> bool:
    normalized_left = normalize_phone(left)
    normalized_right = normalize_phone(right)

    if not normalized_left or not normalized_right:
        return False
    if normalized_left == normalized_right:
        return True
    return normalized_left.endswith(normalized_right) or normalized_right.endswith(normalized_left)


def is_valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value or ""))


def is_valid_phone(value: str) -> bool:
    return bool(re.fullmatch(r"\d{10,15}", value or ""))


def find_user_by_identifier(db: Session, identifier: str):
    normalized = normalize_identifier(identifier)
    normalized_phone = normalize_phone(identifier)

    user = db.query(User).filter(User.email == normalized).first()
    if user:
        return user

    if not normalized_phone:
        return None

    users = db.query(User).all()
    for existing_user in users:
        if phones_match(existing_user.phone, normalized_phone):
            return existing_user
    return None


def find_admin_by_username(db: Session, username: str):
    normalized = (username or "").strip().lower()
    if not normalized:
        return None
    return db.query(AdminUser).filter(AdminUser.username == normalized).first()


def find_worker_by_worker_id(db: Session, worker_id: str):
    raw_value = (worker_id or "").strip()
    if not raw_value:
        return None
    return db.query(Worker).filter(Worker.worker_id.ilike(raw_value)).first()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(auth_bearer),
):
    token = credentials.credentials if credentials else request.cookies.get("user_token")
    if not token:
        raise HTTPException(status_code=401, detail="User authentication required")
    cached_identity = cache_get_json(f"auth-user:{token}")
    if cached_identity:
        return SimpleNamespace(**cached_identity)
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid user token")

    if data.get("type") != "user":
        raise HTTPException(status_code=403, detail="User token type required")

    user_id = data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token payload")

    token_identity = data.get("identity") or {}
    if token_identity:
        identity = {"id": int(user_id), **token_identity}
        cache_set_json(f"auth-user:{token}", identity, AUTH_CACHE_TTL_SECONDS)
        return SimpleNamespace(**identity)

    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=403, detail="User access denied")
    identity = build_user_identity(user)
    cache_set_json(f"auth-user:{token}", identity, AUTH_CACHE_TTL_SECONDS)
    return SimpleNamespace(**identity)


def decode_admin_token(token: str, db: Session):
    if token.strip().lower() in {"", "nothing", "null", "undefined"}:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    cached_identity = cache_get_json(f"auth-admin:{token}")
    if cached_identity:
        return cached_identity
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid admin token")

    token_type = data.get("type")
    if token_type != "admin":
        raise HTTPException(status_code=403, detail="Admin token type required")
    admin_id = data.get("sub")
    if not admin_id:
        raise HTTPException(status_code=401, detail="Invalid admin token payload")
    token_identity = data.get("identity") or {}
    if token_identity:
        identity = {"id": int(admin_id), **token_identity}
        cache_set_json(f"auth-admin:{token}", identity, AUTH_CACHE_TTL_SECONDS)
        return identity

    admin = db.query(AdminUser).filter(AdminUser.id == int(admin_id), AdminUser.is_active == True).first()
    if not admin:
        raise HTTPException(status_code=403, detail="Admin access denied")

    identity = build_admin_identity(admin)
    cache_set_json(f"auth-admin:{token}", identity, AUTH_CACHE_TTL_SECONDS)
    return identity


def get_current_admin(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(auth_bearer),
):
    token = credentials.credentials if credentials else request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    return decode_admin_token(token, db)


def decode_worker_token(token: str, db: Session):
    if token.strip().lower() in {"", "nothing", "null", "undefined"}:
        raise HTTPException(status_code=401, detail="Worker authentication required")
    cached_identity = cache_get_json(f"auth-worker:{token}")
    if cached_identity:
        return SimpleNamespace(**cached_identity)
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid worker token")

    if data.get("type") != "worker":
        raise HTTPException(status_code=403, detail="Worker token type required")

    worker_pk = data.get("sub")
    if not worker_pk:
        raise HTTPException(status_code=401, detail="Invalid worker token payload")

    token_identity = data.get("identity") or {}
    if token_identity:
        identity = {"id": int(worker_pk), **token_identity}
        cache_set_json(f"auth-worker:{token}", identity, AUTH_CACHE_TTL_SECONDS)
        return SimpleNamespace(**identity)

    worker = db.query(Worker).filter(Worker.id == int(worker_pk), Worker.is_active == True).first()
    if not worker:
        raise HTTPException(status_code=403, detail="Worker access denied")
    identity = build_worker_identity(worker)
    cache_set_json(f"auth-worker:{token}", identity, AUTH_CACHE_TTL_SECONDS)
    return SimpleNamespace(**identity)


def get_current_worker(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(auth_bearer),
):
    token = credentials.credentials if credentials else request.cookies.get("worker_token")
    if not token:
        raise HTTPException(status_code=401, detail="Worker authentication required")
    return decode_worker_token(token, db)


def send_otp_email(to_email: str, code: str) -> tuple[bool, str]:
    if not (MAIL_SERVER and MAIL_PORT and MAIL_USERNAME and MAIL_PASSWORD and MAIL_FROM):
        return False, "Email configuration is incomplete"

    subject = "Urban Sentinel Password Reset Code"
    body = (
        f"Your Urban Sentinel password reset code is: {code}\n\n"
        "This code expires in 10 minutes.\n"
        "If you did not request this, please ignore this email."
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = MAIL_FROM
    msg["To"] = to_email
    msg.set_content(body)

    try:
        if MAIL_SSL_TLS:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, context=context, timeout=MAIL_TIMEOUT_SECONDS) as smtp:
                smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=MAIL_TIMEOUT_SECONDS) as smtp:
                smtp.ehlo()
                if MAIL_STARTTLS:
                    smtp.starttls(context=ssl.create_default_context())
                    smtp.ehlo()
                smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
                smtp.send_message(msg)
        return True, "OTP sent via email"
    except Exception as exc:
        return False, f"Email delivery failed: {exc}"


def build_closure_receipt_pdf_bytes(issue: Issue, user: Optional[User] = None) -> bytes:
    """Generate closure receipt PDF bytes for resolved/rejected updates."""
    setup_pdf_fonts()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 42
    y = height - 72

    status_value = (issue.status or "Pending").strip()
    is_resolved = status_value == "Resolved"
    status_color = colors.green if is_resolved else colors.red if status_value == "Rejected" else colors.darkorange

    # Header block
    pdf.setFillColorRGB(0.08, 0.19, 0.33)
    pdf.rect(0, height - 110, width, 110, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont(PDF_FONT_BOLD, 20)
    pdf.drawString(margin, height - 52, "URBAN SENTINEL")
    pdf.setFont(PDF_FONT_REGULAR, 12)
    pdf.drawString(margin, height - 72, "Issue Closure Receipt")
    pdf.drawRightString(width - margin, height - 72, format_app_datetime(datetime.utcnow(), "%d %b %Y %I:%M %p"))

    y = height - 142
    pdf.setStrokeColorRGB(0.82, 0.86, 0.91)
    pdf.setLineWidth(1)
    pdf.rect(margin, 70, width - 2 * margin, y - 56, stroke=1, fill=0)

    # Status highlight
    pdf.setFillColor(status_color)
    pdf.roundRect(margin, y - 28, width - 2 * margin, 30, 8, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont(PDF_FONT_BOLD, 12)
    pdf.drawString(margin + 10, y - 18, f"Final Status: {status_value}")
    y -= 50

    # Details
    pdf.setFillColor(colors.black)
    rows = [
        ("Complaint Number", issue.complaint_number or "N/A"),
        ("Title", issue.title or "N/A"),
        ("Category", issue.category or "General"),
        ("Location", issue.location or "N/A"),
        ("User", user.full_name if user else "N/A"),
        ("Email", user.email if user else "N/A"),
        ("Created At", format_app_datetime(issue.created_at)),
    ]

    for label, value in rows:
        pdf.setFont(PDF_FONT_BOLD, 11)
        pdf.drawString(margin + 10, y, f"{label}:")
        pdf.setFont(PDF_FONT_REGULAR, 11)
        max_width = width - (margin + 120) - margin
        x_val = margin + 120
        wrapped_lines = wrap_pdf_text(pdf, str(value), PDF_FONT_REGULAR, 11, max_width)
        for line in wrapped_lines:
            pdf.drawString(x_val, y, line)
            y -= 16
        y -= 20
        if y < 130:
            pdf.showPage()
            y = height - 80
            pdf.setFont(PDF_FONT_REGULAR, 11)

    # Concluding message
    pdf.setFillColorRGB(0.15, 0.2, 0.3)
    pdf.setFont(PDF_FONT_ITALIC, 11)
    conclusion = (
        "Thank you for using Urban Sentinel. This confirms that your complaint has reached its final decision "
        f"state as '{status_value}'. Please keep this receipt for your records."
    )
    wrapped = wrap_pdf_text(pdf, conclusion, PDF_FONT_ITALIC, 11, width - 2 * margin - 20)
    for line in wrapped:
        pdf.drawString(margin + 10, y, line)
        y -= 16

    pdf.setFont(PDF_FONT_REGULAR, 9)
    pdf.setFillColor(colors.grey)
    pdf.drawCentredString(width / 2, 50, "System generated closure receipt - no signature required.")
    pdf.save()
    return buffer.getvalue()


def send_status_update_email(user: User, issue: Issue, request: Optional[Request] = None) -> tuple[bool, str]:
    """Send resolved/rejected email with closure receipt attachment."""
    if not user or not user.email:
        return False, "User email missing"
    if not (MAIL_SERVER and MAIL_PORT and MAIL_USERNAME and MAIL_PASSWORD and MAIL_FROM):
        return False, "Email configuration is incomplete"

    status_value = (issue.status or "").strip()
    if status_value not in {"Resolved", "Rejected"}:
        return False, "Status notification only sent for final states"

    verdict_text = "resolved successfully" if status_value == "Resolved" else "marked as rejected after review"
    receipt_url = f"{resolve_api_base_url(request)}/receipt/closure/{issue.complaint_number}"
    scan_url = build_scan_url(issue.complaint_number, request)
    body = (
        f"Dear {user.full_name},\n\n"
        f"Your complaint {issue.complaint_number} has been {verdict_text}.\n"
        f"Final Status: {status_value}\n"
        f"Title: {issue.title}\n"
        f"Location: {issue.location}\n\n"
        "Please find the closure receipt attached.\n"
        f"You can also download it here: {receipt_url}\n"
        f"Track complaint status: {scan_url}\n\n"
        "Thank you for reporting through Urban Sentinel."
    )

    msg = EmailMessage()
    msg["Subject"] = f"Urban Sentinel Complaint Update - {issue.complaint_number} ({status_value})"
    msg["From"] = MAIL_FROM
    msg["To"] = user.email
    msg.set_content(body)
    pdf_bytes = build_closure_receipt_pdf_bytes(issue, user)
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=f"closure_receipt_{issue.complaint_number}.pdf",
    )

    try:
        if MAIL_SSL_TLS:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, context=context) as smtp:
                smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as smtp:
                smtp.ehlo()
                if MAIL_STARTTLS:
                    smtp.starttls(context=ssl.create_default_context())
                    smtp.ehlo()
                smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
                smtp.send_message(msg)
        return True, "Status email sent"
    except Exception as exc:
        return False, f"Status email failed: {exc}"


def send_otp_sms_twilio(phone: str, code: str) -> tuple[bool, str]:
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER):
        return False, "Twilio configuration is incomplete"
    if (
        is_placeholder_value(TWILIO_ACCOUNT_SID)
        or is_placeholder_value(TWILIO_AUTH_TOKEN)
        or is_placeholder_value(TWILIO_FROM_NUMBER)
    ):
        return False, "Twilio credentials are placeholders. Update SID, Auth Token, and From Number in backend/.env."

    payload = urlencode(
        {
            "From": TWILIO_FROM_NUMBER,
            "To": f"+{phone}",
            "Body": f"Urban Sentinel OTP: {code}. Valid for 10 minutes.",
        }
    ).encode("utf-8")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    auth_str = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode("utf-8")
    auth_header = base64.b64encode(auth_str).decode("ascii")

    request = UrlRequest(url=url, data=payload, method="POST")
    request.add_header("Authorization", f"Basic {auth_header}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urlopen(request, timeout=12) as response:
            _ = response.read()
        return True, "OTP sent via Twilio SMS"
    except HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="ignore")
        try:
            parsed = json.loads(error_text)
            twilio_code = parsed.get("code")
            twilio_message = parsed.get("message")
            if twilio_code == 20003:
                return False, "Twilio authentication failed. Check SID/Auth Token."
            if twilio_message:
                return False, f"Twilio error: {twilio_message}"
        except Exception:
            pass
        if exc.code == 401:
            return False, "SMS provider authentication failed. Check Twilio SID/Auth Token."
        return False, f"Twilio SMS failed ({exc.code})"
    except URLError as exc:
        return False, f"Twilio network error: {exc}"
    except Exception as exc:
        return False, f"Twilio SMS failed: {exc}"


def send_otp_sms_fast2sms(phone: str, code: str) -> tuple[bool, str]:
    if not FAST2SMS_API_KEY:
        return False, "Fast2SMS configuration is incomplete"

    payload = json.dumps(
        {
            "route": "q",
            "message": f"Urban Sentinel OTP is {code}. It expires in 10 minutes.",
            "language": "english",
            "numbers": phone,
        }
    ).encode("utf-8")

    request = UrlRequest(url="https://www.fast2sms.com/dev/bulkV2", data=payload, method="POST")
    request.add_header("authorization", FAST2SMS_API_KEY)
    request.add_header("Content-Type", "application/json")

    try:
        with urlopen(request, timeout=12) as response:
            _ = response.read()
        return True, "OTP sent via Fast2SMS"
    except HTTPError as exc:
        return False, f"Fast2SMS error: {exc.read().decode('utf-8', errors='ignore')}"
    except URLError as exc:
        return False, f"Fast2SMS network error: {exc}"
    except Exception as exc:
        return False, f"Fast2SMS failed: {exc}"


def send_otp_sms_msg91(phone: str, code: str) -> tuple[bool, str]:
    if not MSG91_AUTH_KEY:
        return False, "MSG91 configuration is incomplete"

    payload_data = {"mobile": f"91{phone}" if len(phone) == 10 else phone, "otp": code}
    if MSG91_TEMPLATE_ID:
        payload_data["template_id"] = MSG91_TEMPLATE_ID
    if MSG91_SENDER_ID:
        payload_data["sender"] = MSG91_SENDER_ID

    payload = json.dumps(payload_data).encode("utf-8")

    request = UrlRequest(url="https://control.msg91.com/api/v5/otp", data=payload, method="POST")
    request.add_header("authkey", MSG91_AUTH_KEY)
    request.add_header("Content-Type", "application/json")

    try:
        with urlopen(request, timeout=12) as response:
            _ = response.read()
        return True, "OTP sent via MSG91"
    except HTTPError as exc:
        return False, f"MSG91 error: {exc.read().decode('utf-8', errors='ignore')}"
    except URLError as exc:
        return False, f"MSG91 network error: {exc}"
    except Exception as exc:
        return False, f"MSG91 failed: {exc}"


def send_otp_sms(phone: str, code: str) -> tuple[bool, str]:
    if SMS_PROVIDER == "twilio":
        return send_otp_sms_twilio(phone, code)
    if SMS_PROVIDER == "fast2sms":
        return send_otp_sms_fast2sms(phone, code)
    if SMS_PROVIDER == "msg91":
        return send_otp_sms_msg91(phone, code)
    return False, "No SMS provider configured"


FALLBACK_LOGIN_EMAIL = "grandrakshith@gmail.com"
FALLBACK_LOGIN_PASSWORD = "123456"
users = [
    {
        "email": FALLBACK_LOGIN_EMAIL,
        "password": FALLBACK_LOGIN_PASSWORD,
        "name": "Rakshith",
    }
]
otp_store: dict[str, str] = {}


def build_fallback_login_response(user: User):
    token = create_access_token(build_identity_token_payload("user", build_user_identity(user)))
    return {
        "status": "success",
        "message": "Login successful",
        "token": token,
        "access_token": token,
        "user": {
            "id": user.id,
            "name": user.full_name,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
        },
    }


def ensure_public_user(db: Session) -> User:
    user = db.query(User).filter(User.email == FALLBACK_LOGIN_EMAIL).first()
    if user:
        return user

    user = User(
        full_name="Rakshith",
        email=FALLBACK_LOGIN_EMAIL,
        phone="8904723329",
        password_hash=hash_password(FALLBACK_LOGIN_PASSWORD),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def find_memory_user(email: Optional[str], password: Optional[str]) -> Optional[dict]:
    for account in users:
        if account.get("email") == (email or "") and account.get("password") == (password or ""):
            return account
    return None


def find_user_for_login_identifier(db: Session, identifier: str) -> Optional[User]:
    normalized_identifier = sanitize_text_input(identifier)
    if not normalized_identifier:
        return None

    if "@" in normalized_identifier:
        normalized_email = normalize_identifier(normalized_identifier)
        return (
            db.query(User)
            .filter(User.email == normalized_email, User.is_active == True)
            .first()
        )

    normalized_phone = normalize_phone(normalized_identifier)
    if not normalized_phone:
        return None

    for user in db.query(User).filter(User.is_active == True).all():
        if phones_match(user.phone, normalized_phone):
            return user
    return None


def find_user_for_password_reset_email(db: Session, email: str) -> Optional[User]:
    normalized_email = normalize_identifier(email)
    if not normalized_email:
        return None

    user = db.query(User).filter(User.email == normalized_email).first()
    if user:
        return user

    if normalized_email == FALLBACK_LOGIN_EMAIL:
        return ensure_public_user(db)

    return None


class RegisterPayload(StrictBaseModel):
    full_name: str
    email: str
    phone: str
    password: str
    device_identifier: Optional[str] = None
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    device_model: Optional[str] = None
    device_platform: Optional[str] = None
    device_os_version: Optional[str] = None
    app_version: Optional[str] = None
    ip_address: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        try:
            return validate_text_field(value, field_name="Full name", min_length=2, max_length=120)
        except HTTPException as exc:
            raise ValueError(exc.detail) from exc

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        try:
            return validate_email_input(value)
        except HTTPException as exc:
            raise ValueError(exc.detail) from exc

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        try:
            return validate_phone_input(value) or ""
        except HTTPException as exc:
            raise ValueError(exc.detail) from exc

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        try:
            return validate_password_input(value)
        except HTTPException as exc:
            raise ValueError(exc.detail) from exc


class LoginPayload(StrictBaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        identifier = sanitize_text_input(value)
        if "@" in identifier:
            try:
                return validate_email_input(identifier)
            except HTTPException as exc:
                raise ValueError(exc.detail) from exc
        try:
            return validate_phone_input(identifier) or ""
        except HTTPException as exc:
            raise ValueError("Enter a valid email or phone number") from exc

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        try:
            return validate_password_input(value, min_length=1)
        except HTTPException as exc:
            raise ValueError(exc.detail) from exc


class LegacyLoginPayload(StrictBaseModel):
    email: str
    password: str


class ForgotPasswordRequestPayload(StrictBaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        try:
            return validate_email_input(value)
        except HTTPException as exc:
            raise ValueError(exc.detail) from exc


class ForgotPasswordVerifyPayload(StrictBaseModel):
    email: str
    otp: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        try:
            return validate_email_input(value)
        except HTTPException as exc:
            raise ValueError(exc.detail) from exc

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value: str) -> str:
        otp = sanitize_text_input(value)
        if not re.fullmatch(r"\d{6}", otp):
            raise ValueError("Enter a valid 6-digit OTP")
        return otp


class ResetPasswordPayload(StrictBaseModel):
    email: str
    otp: str
    new_password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        try:
            return validate_email_input(value)
        except HTTPException as exc:
            raise ValueError(exc.detail) from exc

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value: str) -> str:
        otp = sanitize_text_input(value)
        if not re.fullmatch(r"\d{6}", otp):
            raise ValueError("Enter a valid 6-digit OTP")
        return otp

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        try:
            return validate_password_input(value, field_name="New password")
        except HTTPException as exc:
            raise ValueError(exc.detail) from exc


# -----------------------------
# ADMIN LOGIN
# -----------------------------
class AdminCreatePayload(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[str] = None


class WorkerCreatePayload(BaseModel):
    department: str
    password: str


class WorkerLoginPayload(BaseModel):
    worker_id: str
    password: str
    department: Optional[str] = None


class WorkerPasswordRequestPayload(BaseModel):
    worker_id: str
    department: Optional[str] = None


class WorkerPasswordResetPayload(BaseModel):
    new_password: str


class ComplaintAssignPayload(BaseModel):
    department: str
    worker_id: str
    duration_value: int
    duration_unit: str


class WorkerIssueStatusPayload(BaseModel):
    status: str


def admin_count(db: Session) -> int:
    return db.query(AdminUser).count()


def request_is_localhost(request: Request) -> bool:
    client_host = (request.client.host if request.client else "") or ""
    request_host = (request.url.hostname or "").strip().lower()
    forwarded_host = request.headers.get("host", "").split(":", 1)[0].strip().lower()
    return client_host in {"127.0.0.1", "::1", "localhost"} or request_host in {"127.0.0.1", "::1", "localhost"} or forwarded_host in {"127.0.0.1", "::1", "localhost"}


DEPARTMENT_CONFIGS = [
    {"name": "Road Damage", "code": "RD"},
    {"name": "Garbage", "code": "GB"},
    {"name": "Street Light Issue", "code": "SL"},
    {"name": "Water Leakage", "code": "WL"},
    {"name": "Emergency", "code": "EM"},
]
ISSUE_CATEGORY_OPTIONS = {
    "Road Damage",
    "Garbage",
    "Street Light Issue",
    "Water Leakage",
    "Drainage",
    "Public Safety",
    "General",
}

WORKER_DEPARTMENTS = [item["name"] for item in DEPARTMENT_CONFIGS]
DEPARTMENT_CODES = {item["name"]: item["code"] for item in DEPARTMENT_CONFIGS}
DEPARTMENT_CONFIG_BY_NAME = {item["name"].lower(): item for item in DEPARTMENT_CONFIGS}
DEPARTMENT_CONFIG_BY_SLUG = {
    re.sub(r"[^a-z0-9]+", "-", item["name"].strip().lower()).strip("-"): item
    for item in DEPARTMENT_CONFIGS
}


def get_department_config(value: str) -> dict:
    cleaned = " ".join(str(value or "").strip().split()).lower()
    if cleaned in DEPARTMENT_CONFIG_BY_NAME:
        return DEPARTMENT_CONFIG_BY_NAME[cleaned]
    raise HTTPException(status_code=400, detail="Choose a valid department")


def normalize_department(value: str) -> str:
    return get_department_config(value)["name"]


def department_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")


def find_department_by_slug(slug: str) -> str:
    normalized_slug = department_slug(slug)
    if normalized_slug in DEPARTMENT_CONFIG_BY_SLUG:
        return DEPARTMENT_CONFIG_BY_SLUG[normalized_slug]["name"]
    raise HTTPException(status_code=404, detail="Department login page not found")


def compute_assignment_deadline(duration_value: int, duration_unit: str) -> tuple[datetime, str]:
    safe_value = max(1, min(int(duration_value), 365))
    unit = (duration_unit or "").strip().lower()
    if unit not in {"day", "days", "month", "months"}:
        raise HTTPException(status_code=400, detail="Duration unit must be days or months")

    if unit.startswith("month"):
        deadline = datetime.utcnow() + timedelta(days=30 * safe_value)
        label = f"{safe_value} month" if safe_value == 1 else f"{safe_value} months"
        return deadline, label

    deadline = datetime.utcnow() + timedelta(days=safe_value)
    label = f"{safe_value} day" if safe_value == 1 else f"{safe_value} days"
    return deadline, label


WORKER_PROGRESS_STATUSES = {"Assigned", "In Progress", "Resolved", "Rejected"}


def serialize_worker(worker: Worker) -> dict:
    return {
        "id": worker.id,
        "worker_id": worker.worker_id,
        "department": worker.department,
        "department_slug": department_slug(worker.department),
        "is_active": worker.is_active,
        "created_at": serialize_app_timestamp(worker.created_at),
        "last_login_at": serialize_app_timestamp(worker.last_login_at),
    }


def compute_next_worker_ids(workers: list[Worker]) -> dict[str, str]:
    counters: dict[str, int] = {department: 1 for department in WORKER_DEPARTMENTS}
    for worker in workers or []:
        department = normalize_department(worker.department)
        code = DEPARTMENT_CODES.get(department, "WK")
        match = re.match(rf"^{re.escape(code)}(\d+)$", str(worker.worker_id or "").strip(), re.IGNORECASE)
        if not match:
            continue
        counters[department] = max(counters.get(department, 1), int(match.group(1)) + 1)
    return {
        department: f"{DEPARTMENT_CODES.get(department, 'WK')}{counters.get(department, 1):03d}"
        for department in WORKER_DEPARTMENTS
    }


def serialize_department_config(
    db: Optional[Session],
    department_name: str,
    next_worker_ids: Optional[dict[str, str]] = None,
) -> dict:
    normalized = normalize_department(department_name)
    config = get_department_config(normalized)
    next_worker_id = (next_worker_ids or {}).get(normalized)
    if not next_worker_id:
        next_worker_id = generate_worker_id(db, normalized) if db is not None else f"{config['code']}001"
    return {
        "name": normalized,
        "code": config["code"],
        "slug": department_slug(normalized),
        "next_worker_id": next_worker_id,
    }


def generate_worker_id(db: Session, department: str) -> str:
    code = DEPARTMENT_CODES.get(department, "WK")
    existing_ids = [
        row[0]
        for row in db.query(Worker.worker_id).filter(Worker.department == department).all()
        if row and row[0]
    ]
    next_number = 1
    pattern = re.compile(rf"^{re.escape(code)}(\d+)$", re.IGNORECASE)
    for existing_id in existing_ids:
        match = pattern.match(str(existing_id).strip())
        if match:
            next_number = max(next_number, int(match.group(1)) + 1)
    return f"{code}{next_number:03d}"


def create_admin_user_record(db: Session, payload: AdminCreatePayload) -> AdminUser:
    username = (payload.username or "").strip().lower()
    password = (payload.password or "").strip()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Admin username must be at least 3 characters")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Admin password must be at least 6 characters")
    if find_admin_by_username(db, username):
        raise HTTPException(status_code=409, detail="Admin username already exists")

    with sqlite_write_guard():
        admin = AdminUser(
            username=username,
            password_hash=hash_password(password),
            full_name=(payload.full_name or "").strip() or None,
            email=(payload.email or "").strip().lower() or None,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin


def credentials_match_legacy_admin(username: str, password: str) -> bool:
    normalized_username = (username or "").strip().lower()
    return bool(
        LEGACY_ADMIN_USERNAME
        and LEGACY_ADMIN_PASSWORD
        and normalized_username == LEGACY_ADMIN_USERNAME.strip().lower()
        and (password or "") == LEGACY_ADMIN_PASSWORD
    )


def resolve_admin_account_for_login(db: Session, username: str, password: str) -> Optional[AdminUser]:
    account = find_admin_by_username(db, username)
    if account and verify_password(password or "", account.password_hash):
        return account

    if credentials_match_legacy_admin(username, password):
        account, _ = upsert_admin_recovery_record(
            db,
            AdminCreatePayload(
                username=(username or "").strip().lower(),
                password=password,
                full_name="System Administrator",
            ),
        )
        return account

    return None


def upsert_admin_recovery_record(db: Session, payload: AdminCreatePayload) -> tuple[AdminUser, bool]:
    username = (payload.username or "").strip().lower()
    password = (payload.password or "").strip()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Admin username must be at least 3 characters")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Admin password must be at least 6 characters")

    with sqlite_write_guard():
        admin = find_admin_by_username(db, username)
        created = admin is None
        if admin is None:
            admin = AdminUser(username=username)
            db.add(admin)

        admin.password_hash = hash_password(password)
        admin.full_name = (payload.full_name or "").strip() or admin.full_name
        admin.email = (payload.email or "").strip().lower() or admin.email
        admin.is_active = True
        db.commit()
        db.refresh(admin)
        return admin, created


@app.post("/admin/bootstrap", include_in_schema=False)
def admin_bootstrap(payload: AdminCreatePayload, db: Session = Depends(get_db)):
    if admin_count(db) > 0:
        raise HTTPException(status_code=409, detail="Admin already configured. Use admin login.")
    admin = create_admin_user_record(db, payload)
    return {"message": "Admin created successfully", "admin": {"id": admin.id, "username": admin.username}}


@app.post("/admin/create", include_in_schema=False)
def admin_create(payload: AdminCreatePayload, _: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    admin = create_admin_user_record(db, payload)
    return {"message": "Admin created successfully", "admin": {"id": admin.id, "username": admin.username}}


@app.post("/admin/login", include_in_schema=False)
def admin_login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    account = resolve_admin_account_for_login(db, username, password)
    if not account:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    token = create_access_token(build_identity_token_payload("admin", build_admin_identity(account)))
    return {"access_token": token, "admin": {"id": account.id, "username": account.username}}


@app.post("/admin/session-login", include_in_schema=False)
def admin_session_login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if admin_count(db) == 0:
        return RedirectResponse(url="/admin/setup", status_code=303)
    account = resolve_admin_account_for_login(db, username, password)
    if not account:
        return HTMLResponse(
            content="<h3 style='font-family:Segoe UI;padding:24px;'>Invalid admin credentials.</h3>",
            status_code=401,
        )
    token = create_access_token(build_identity_token_payload("admin", build_admin_identity(account)))
    response = RedirectResponse(url="/admin/panel", status_code=303)
    response.set_cookie("admin_token", token, httponly=True, samesite="lax", max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return response


@app.get("/admin/logout", include_in_schema=False)
def admin_logout():
    response = RedirectResponse(url="/admin", status_code=303)
    response.delete_cookie("admin_token")
    return response


@app.get("/admin/departments", include_in_schema=False)
def get_departments(_: dict = Depends(get_current_admin)):
    return {"departments": WORKER_DEPARTMENTS, "department_configs": DEPARTMENT_CONFIGS}


@app.get("/admin/workers", include_in_schema=False)
def get_workers(_: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    workers = db.query(Worker).order_by(Worker.department.asc(), Worker.worker_id.asc()).all()
    reset_requests = db.query(WorkerResetRequest).order_by(WorkerResetRequest.requested_at.desc()).all()
    workers_by_pk = {worker.id: worker for worker in workers}
    return {
        "workers": [serialize_worker(worker) for worker in workers],
        "reset_requests": [
            {
                "id": item.id,
                "worker_db_id": item.worker_id,
                "worker_id": workers_by_pk[item.worker_id].worker_id if item.worker_id in workers_by_pk else f"worker-{item.worker_id}",
                "department": item.department,
                "status": item.status,
                "requested_at": isoformat_app_datetime(item.requested_at),
                "resolved_at": isoformat_app_datetime(item.resolved_at),
            }
            for item in reset_requests
        ],
    }


@app.post("/admin/workers", include_in_schema=False)
def create_worker(payload: WorkerCreatePayload, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    department = normalize_department(payload.department)
    password = (payload.password or "").strip()
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    worker_id = generate_worker_id(db, department)

    worker = Worker(
        worker_id=worker_id,
        department=department,
        password_hash=hash_password(password),
        password_plaintext=password,
        created_by_admin_id=admin["id"],
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    publish_panel_event("worker-created", {"worker": serialize_worker(worker)})
    return {"message": "Worker created successfully", "worker": serialize_worker(worker)}


@app.post("/admin/workers/{worker_db_id}/reset-password", include_in_schema=False)
def admin_reset_worker_password(
    worker_db_id: int,
    payload: WorkerPasswordResetPayload,
    _: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    worker = db.query(Worker).filter(Worker.id == worker_db_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    password = (payload.new_password or "").strip()
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    worker.password_hash = hash_password(password)
    worker.password_plaintext = password
    pending_requests = db.query(WorkerResetRequest).filter(
        WorkerResetRequest.worker_id == worker.id,
        WorkerResetRequest.status == "Pending",
    ).all()
    for item in pending_requests:
        item.status = "Resolved"
        item.resolved_at = datetime.utcnow()
    db.commit()
    return {"message": "Worker password updated successfully"}


@app.delete("/admin/worker-reset-requests/{request_id}", include_in_schema=False)
def delete_worker_reset_request(
    request_id: int,
    _: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    reset_request = db.query(WorkerResetRequest).filter(WorkerResetRequest.id == request_id).first()
    if not reset_request:
        raise HTTPException(status_code=404, detail="Password reset request not found")

    db.delete(reset_request)
    db.commit()
    return {"message": "Password reset request deleted successfully"}


@app.get("/admin/setup", response_class=HTMLResponse, include_in_schema=False)
def admin_setup_page(request: Request, db: Session = Depends(get_db)):
    existing_admins = db.query(AdminUser).order_by(AdminUser.username.asc()).all()
    if existing_admins:
        admin_list = "".join(
            f"<li><strong>{escape(item.username)}</strong></li>"
            for item in existing_admins
        )
        return HTMLResponse(
            content=f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Urban Sentinel Admin Recovery</title>
  <style>
    body {{ margin:0; font-family:Segoe UI,Arial,sans-serif; background:linear-gradient(145deg,#111827,#0f766e); min-height:100vh; display:grid; place-items:center; color:#f8fafc; }}
    .card {{ width:min(92vw,540px); background:rgba(15,23,42,0.88); border:1px solid rgba(148,163,184,0.25); border-radius:18px; padding:24px; box-shadow:0 18px 45px rgba(0,0,0,0.35); }}
    h1 {{ margin:0 0 8px; font-size:1.55rem; }}
    p, li, small {{ color:#cbd5e1; }}
    ul {{ padding-left:20px; margin:0 0 16px; }}
    label {{ display:block; margin:10px 0 6px; font-size:0.92rem; color:#e2e8f0; }}
    input {{ width:100%; padding:11px; border-radius:10px; border:1px solid #334155; background:#0b1220; color:#f8fafc; }}
    button {{ margin-top:14px; width:100%; padding:11px; border:none; border-radius:10px; background:#22d3ee; color:#082f49; font-weight:700; cursor:pointer; }}
    .secondary {{ display:block; margin-top:12px; color:#94a3b8; }}
  </style>
</head>
<body>
  <form class="card" method="post" action="/admin/setup/recover">
    <h1>Admin Recovery</h1>
    <p>An admin account already exists, so the one-time setup is complete. Use this page to recover access, reset the password for an existing admin, or create a new admin if needed.</p>
    <p>Existing admin usernames:</p>
    <ul>{admin_list}</ul>
    <label>Username</label>
    <input name="username" required />
    <label>New Password</label>
    <input name="password" type="password" required />
    <label>Full Name (optional)</label>
    <input name="full_name" />
    <label>Email (optional)</label>
    <input name="email" type="email" />
    <button type="submit">Create Or Reset Admin</button>
    <small class="secondary">If the username already exists, its password will be replaced. If it does not exist, a new admin will be created.</small>
  </form>
</body>
</html>
"""
        )

    return HTMLResponse(
        content="""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Urban Sentinel Admin Setup</title>
  <style>
    body { margin:0; font-family:Segoe UI,Arial,sans-serif; background:linear-gradient(145deg,#111827,#0f766e); min-height:100vh; display:grid; place-items:center; color:#f8fafc; }
    .card { width:min(92vw,460px); background:rgba(15,23,42,0.88); border:1px solid rgba(148,163,184,0.25); border-radius:18px; padding:24px; box-shadow:0 18px 45px rgba(0,0,0,0.35); }
    h1 { margin:0 0 8px; font-size:1.55rem; }
    p { margin:0 0 16px; color:#cbd5e1; }
    label { display:block; margin:10px 0 6px; font-size:0.92rem; color:#e2e8f0; }
    input { width:100%; padding:11px; border-radius:10px; border:1px solid #334155; background:#0b1220; color:#f8fafc; }
    button { margin-top:14px; width:100%; padding:11px; border:none; border-radius:10px; background:#22d3ee; color:#082f49; font-weight:700; cursor:pointer; }
  </style>
</head>
<body>
  <form class="card" method="post" action="/admin/setup">
    <h1>Create First Admin</h1>
    <p>Complete this one-time setup before admin login.</p>
    <label>Username</label>
    <input name="username" required />
    <label>Password</label>
    <input name="password" type="password" required />
    <label>Full Name (optional)</label>
    <input name="full_name" />
    <label>Email (optional)</label>
    <input name="email" type="email" />
    <button type="submit">Create Admin</button>
  </form>
</body>
</html>
"""
    )


@app.post("/admin/setup", include_in_schema=False)
def admin_setup_submit(
    username: str = Form(...),
    password: str = Form(...),
    full_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    if admin_count(db) > 0:
        return RedirectResponse(url="/admin", status_code=303)
    payload = AdminCreatePayload(username=username, password=password, full_name=full_name, email=email)
    create_admin_user_record(db, payload)
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/admin/setup/recover", include_in_schema=False)
def admin_setup_recover(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    full_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    payload = AdminCreatePayload(username=username, password=password, full_name=full_name, email=email)
    try:
        upsert_admin_recovery_record(db, payload)
    except OperationalError as exc:
        if "database is locked" in str(exc).lower():
            raise HTTPException(
                status_code=503,
                detail="Database is busy right now. Wait a few seconds and submit the recovery form again.",
            ) from exc
        raise
    return RedirectResponse(url="/admin", status_code=303)


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def admin_page(db: Session = Depends(get_db)):
    if admin_count(db) == 0:
        return RedirectResponse(url="/admin/setup", status_code=303)
    return HTMLResponse(
        content="""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Urban Sentinel Admin</title>
  <style>
    body { margin:0; font-family:Segoe UI,Arial,sans-serif; background:linear-gradient(145deg,#0f172a,#0f766e); min-height:100vh; display:grid; place-items:center; color:#f8fafc; }
    .card { width:min(92vw,430px); background:rgba(15,23,42,0.82); border:1px solid rgba(148,163,184,0.25); border-radius:18px; padding:24px; box-shadow:0 18px 45px rgba(0,0,0,0.35); }
    h1 { margin:0 0 8px; font-size:1.6rem; }
    p { margin:0 0 16px; color:#cbd5e1; }
    label { display:block; margin:10px 0 6px; font-size:0.92rem; color:#e2e8f0; }
    input { width:100%; padding:11px; border-radius:10px; border:1px solid #334155; background:#0b1220; color:#f8fafc; }
    button { margin-top:14px; width:100%; padding:11px; border:none; border-radius:10px; background:#22d3ee; color:#082f49; font-weight:700; cursor:pointer; }
    small { display:block; margin-top:12px; color:#94a3b8; }
  </style>
</head>
<body>
  <form class="card" method="post" action="/admin/session-login">
    <h1>Urban Sentinel Admin</h1>
    <p>Secure backend control panel</p>
    <label>Username</label>
    <input name="username" required />
    <label>Password</label>
    <input name="password" type="password" required />
    <button type="submit">Sign In</button>
    <small>This portal is backend-only and not visible in the user app. If login fails or you need to reset the admin password, open <a href="/admin/setup" style="color:#67e8f9;">/admin/setup</a>.</small>
  </form>
</body>
</html>
"""
    )


# -----------------------------
# USER AUTH
# -----------------------------
@app.post("/auth/register")
def user_register(payload: RegisterPayload, db: Session = Depends(get_db)):
    full_name = (payload.full_name or "").strip()
    email = normalize_identifier(payload.email)
    phone = normalize_phone(payload.phone)
    password = payload.password or ""
    device_identifier = normalize_device_identifier(payload.device_identifier, email or phone or full_name)

    if len(full_name) < 2:
        raise HTTPException(status_code=400, detail="Full name is required")
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Enter a valid email")
    if not is_valid_phone(phone):
        raise HTTPException(status_code=400, detail="Enter a valid phone number")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(status_code=409, detail="User already registered")

    existing_phone = next((user for user in db.query(User).all() if phones_match(user.phone, phone)), None)
    if existing_phone:
        raise HTTPException(status_code=409, detail="User already registered")

    user = User(
        full_name=full_name,
        email=email,
        phone=phone,
        password_hash=hash_password(password),
    )
    sync_user_registration_details(db, user, payload, device_identifier)
    db.add(user)
    db.flush()
    upsert_registered_device(
        db,
        user=user,
        device_identifier=device_identifier,
        device_name=payload.device_name or f"{full_name}'s device",
        device_type=payload.device_type or "USER_APP",
        device_model=payload.device_model,
        platform=payload.device_platform,
        os_version=payload.device_os_version,
        app_version=payload.app_version,
        login_email=email,
        login_phone=phone,
        ip_address=payload.ip_address,
    )
    db.commit()
    db.refresh(user)

    return {
        "message": "Registration successful",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "device_identifier": user.registered_device_identifier,
        },
    }


@app.post("/auth/login")
def user_login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = find_user_for_login_identifier(db, payload.email)
    if not user or not verify_password(payload.password or "", user.password_hash):
        user_record = find_memory_user(payload.email, payload.password)
        if user_record:
            fallback_user = ensure_public_user(db)
            fallback_user.last_login_at = datetime.utcnow()
            db.commit()
            db.refresh(fallback_user)
            return build_fallback_login_response(fallback_user)
        return {
            "status": "error",
            "message": "Invalid email or password",
        }

    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    token = create_access_token(build_identity_token_payload("user", build_user_identity(user)))
    return {
        "status": "success",
        "message": "Login successful",
        "token": token,
        "access_token": token,
        "user": {
            "id": user.id,
            "name": user.full_name,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
        },
    }


@app.post("/login")
def legacy_login(payload: LegacyLoginPayload, db: Session = Depends(get_db)):
    email = payload.email
    password = payload.password

    if email == "grandrakshith@gmail.com" and password == "123456":
        fallback_user = ensure_public_user(db)
        fallback_user.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(fallback_user)
        return build_fallback_login_response(fallback_user)

    return {
        "status": "error",
        "message": "Invalid email or password",
    }


@app.get("/auth/login", include_in_schema=False)
def auth_login_get_hint():
    return {
        "message": "Use POST /auth/login with JSON body: {\"email\":\"grandrakshith@gmail.com\",\"password\":\"123456\"}"
    }


@app.post("/send-otp")
def send_otp(payload: ForgotPasswordRequestPayload, db: Session = Depends(get_db)):
    normalized_email = normalize_identifier(payload.email)
    user = find_user_for_password_reset_email(db, normalized_email)
    if not user:
        return {"status": "error", "message": "User not found"}

    otp = str(random.randint(100000, 999999))
    otp_store[normalized_email] = otp
    user.reset_code_hash = hash_reset_code(otp)
    user.reset_code_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.commit()

    mail_sent, mail_message = send_otp_email(user.email, otp)
    if not mail_sent:
        if OTP_DEBUG_MODE:
            print(f"[OTP DEBUG] Email delivery failed for {user.email}. OTP={otp}. Reason: {mail_message}")
            return {
                "status": "success",
                "message": "OTP generated in debug mode",
                "detail": f"Email delivery failed locally. Use OTP: {otp}",
                "otp": otp,
                "delivery": "debug",
            }
        return {
            "status": "error",
            "message": "OTP email delivery failed",
            "detail": mail_message,
        }

    response = {
        "status": "success",
        "message": "OTP sent successfully",
        "detail": "OTP sent to your email address.",
    }
    if OTP_DEBUG_MODE:
        response["otp"] = otp
    return response


@app.post("/verify-otp")
def verify_otp(payload: ForgotPasswordVerifyPayload, db: Session = Depends(get_db)):
    normalized_email = normalize_identifier(payload.email)
    user = find_user_for_password_reset_email(db, normalized_email)
    if not user or not user.reset_code_hash or not user.reset_code_expires_at:
        return {
            "status": "error",
            "message": "OTP verification failed",
        }

    if user.reset_code_expires_at < datetime.utcnow():
        return {
            "status": "error",
            "message": "OTP expired",
        }

    if hmac.compare_digest(user.reset_code_hash, hash_reset_code(payload.otp)):
        return {
            "status": "success",
            "message": "OTP verified",
        }

    return {
        "status": "error",
        "message": "OTP verification failed",
    }


@app.post("/reset-password")
def reset_password(payload: ResetPasswordPayload, db: Session = Depends(get_db)):
    normalized_email = normalize_identifier(payload.email)
    user = find_user_for_password_reset_email(db, normalized_email)
    if not user:
        return {
            "status": "error",
            "message": "User not found",
        }

    if not user.reset_code_hash or not user.reset_code_expires_at:
        return {
            "status": "error",
            "message": "OTP verification required",
        }

    if user.reset_code_expires_at < datetime.utcnow():
        return {
            "status": "error",
            "message": "OTP expired",
        }

    if not hmac.compare_digest(user.reset_code_hash, hash_reset_code(payload.otp)):
        return {
            "status": "error",
            "message": "OTP verification failed",
        }

    user.password_hash = hash_password(payload.new_password)
    user.reset_code_hash = None
    user.reset_code_expires_at = None
    otp_store.pop(normalized_email, None)
    db.commit()
    return {
        "status": "success",
        "message": "Password updated successfully",
    }


@app.post("/auth/forgot-password/request")
def forgot_password_request(payload: ForgotPasswordRequestPayload, db: Session = Depends(get_db)):
    return send_otp(payload, db)


@app.post("/auth/forgot-password/verify")
def forgot_password_verify(payload: ForgotPasswordVerifyPayload, db: Session = Depends(get_db)):
    return verify_otp(payload, db)


@app.post("/auth/forgot-password/reset")
def forgot_password_reset(payload: ResetPasswordPayload, db: Session = Depends(get_db)):
    return reset_password(payload, db)
@app.get("/auth/config")
def auth_config():
    """Return enabled auth features (used by frontend)."""
    return {
        "google_oauth_enabled": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
    }


@app.get("/auth/google")
def google_login():
    """Initiate Google OAuth login"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        "response_type=code&"
        f"client_id={GOOGLE_CLIENT_ID}&"
        "redirect_uri=http://localhost:8000/auth/google/callback&"
        "scope=openid email profile&"
        "access_type=offline&"
        "prompt=consent"
    )
    return RedirectResponse(google_auth_url)


@app.get("/auth/google/callback")
def google_oauth_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    try:
        # Exchange code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://localhost:8000/auth/google/callback"
        }
        
        import requests
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_info = token_response.json()
        
        # Get user info
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        user_response = requests.get(user_info_url, headers={
            "Authorization": f"Bearer {token_info['access_token']}"
        })
        user_response.raise_for_status()
        google_user = user_response.json()
        
        # Check if user exists
        user = db.query(User).filter(User.email == google_user["email"]).first()
        
        if not user:
            # Create new user
            user = User(
                full_name=google_user["name"],
                email=google_user["email"],
                phone=None,
                password_hash=hash_password(secrets.token_urlsafe(32)),
                created_at=datetime.utcnow(),
                last_login_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.last_login_at = datetime.utcnow()
            db.commit()

        app_token = create_access_token({"sub": str(user.id), "type": "user"})
        frontend_url = (
            "http://localhost:5174/login?"
            + urlencode(
                {
                    "user": json.dumps(
                        {"id": user.id, "email": user.email, "name": user.full_name}
                    ),
                    "access_token": app_token,
                }
            )
        )
        return RedirectResponse(frontend_url)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")


@app.post("/worker/auth/login", include_in_schema=False)
def worker_login(payload: WorkerLoginPayload, db: Session = Depends(get_db)):
    worker = find_worker_by_worker_id(db, payload.worker_id)
    if not worker or not verify_password(payload.password or "", worker.password_hash):
        raise HTTPException(status_code=401, detail="Invalid worker credentials")
    if payload.department:
        expected_department = normalize_department(payload.department)
        if worker.department != expected_department:
            raise HTTPException(status_code=403, detail="This worker does not belong to that department")

    worker.last_login_at = datetime.utcnow()
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        if "database is locked" not in str(exc).lower():
            raise

    token = create_access_token(build_identity_token_payload("worker", build_worker_identity(worker)))
    return {
        "message": "Worker login successful",
        "access_token": token,
        "worker": {
            "id": worker.id,
            "worker_id": worker.worker_id,
            "department": worker.department,
        },
    }


@app.post("/worker/session-login", include_in_schema=False)
def worker_session_login(
    worker_id: str = Form(...),
    password: str = Form(...),
    department: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    try:
        worker = find_worker_by_worker_id(db, worker_id)
        if not worker or not verify_password(password or "", worker.password_hash):
            return RedirectResponse(
                url=worker_login_redirect_target(
                    department=department,
                    error_code="invalid_credentials",
                    worker_id=worker_id,
                ),
                status_code=303,
            )
        if department:
            try:
                expected_department = normalize_department(department)
            except HTTPException:
                return RedirectResponse(
                    url=worker_login_redirect_target(
                        error_code="department_not_found",
                        worker_id=worker_id,
                    ),
                    status_code=303,
                )
            if worker.department != expected_department:
                return RedirectResponse(
                    url=worker_login_redirect_target(
                        department=department,
                        error_code="department_mismatch",
                        worker_id=worker_id,
                    ),
                    status_code=303,
                )

        worker.last_login_at = datetime.utcnow()
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            if "database is locked" not in str(exc).lower():
                raise

        token = create_access_token(build_identity_token_payload("worker", build_worker_identity(worker)))
        response = RedirectResponse(url="/worker/panel", status_code=303)
        response.set_cookie("worker_token", token, httponly=True, samesite="lax", max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        return response
    except Exception as exc:
        db.rollback()
        return HTMLResponse(
            status_code=500,
            content=(
                "<h3 style='font-family:Segoe UI;padding:24px;'>Worker login failed.</h3>"
                f"<p style='font-family:Segoe UI;padding:0 24px 24px;color:#475569;'>"
                f"{escape(str(exc))}</p>"
            ),
        )


@app.post("/worker/forgot-password-request", include_in_schema=False)
def worker_forgot_password_request(payload: WorkerPasswordRequestPayload, db: Session = Depends(get_db)):
    worker = find_worker_by_worker_id(db, payload.worker_id)
    if not worker:
        return {"message": "If the worker exists, the request has been sent to admin"}
    if payload.department:
        expected_department = normalize_department(payload.department)
        if worker.department != expected_department:
            return {"message": "Worker ID does not belong to this department"}

    existing_pending = db.query(WorkerResetRequest).filter(
        WorkerResetRequest.worker_id == worker.id,
        WorkerResetRequest.status == "Pending",
    ).first()
    if existing_pending:
        return {"message": "A password reset request is already waiting for admin approval"}

    reset_request = WorkerResetRequest(worker_id=worker.id, department=worker.department, status="Pending")
    db.add(reset_request)
    db.commit()
    return {"message": "Password reset request sent to admin"}


@app.get("/worker/logout", include_in_schema=False)
def worker_logout():
    response = RedirectResponse(url="/worker", status_code=303)
    response.delete_cookie("worker_token")
    return response


# -----------------------------
# CREATE ISSUE (PUBLIC)
# -----------------------------
from typing import List
from fastapi import UploadFile, File, Form, Depends


COMPLAINT_ID_PATTERN = re.compile(r"^US-(?:\d{4}-)?\d{4,}$", re.IGNORECASE)
TRACKING_STATUS_STEPS = ("Submitted", "Assigned", "In Progress", "Resolved")


def normalize_phone_lookup_value(phone: Optional[str]) -> str:
    return re.sub(r"\D", "", str(phone or ""))


def matches_verified_phone(input_phone: str, verified_phone: Optional[str]) -> bool:
    normalized_input = normalize_phone_lookup_value(input_phone)
    normalized_verified = normalize_phone_lookup_value(verified_phone)
    if not normalized_input or not normalized_verified:
        return False
    return (
        normalized_input == normalized_verified
        or normalized_verified.endswith(normalized_input)
        or normalized_input.endswith(normalized_verified)
    )


def normalize_complaint_lookup_id(complaint_number: str) -> str:
    normalized = " ".join(str(complaint_number or "").strip().upper().split())
    if not COMPLAINT_ID_PATTERN.match(normalized):
        raise HTTPException(status_code=400, detail="Invalid complaint ID format")
    return normalized


def public_status_for_issue(issue: Issue) -> str:
    status = " ".join(str(issue.status or "").strip().split()).title()
    if status == "Pending":
        return "Submitted"
    if status in {"In Progress", "Resolved", "Rejected"}:
        return status
    return "Submitted"


def derive_issue_priority(issue: Issue) -> str:
    searchable_text = " ".join(
        [
            str(issue.category or ""),
            str(issue.title or ""),
            str(issue.description or ""),
        ]
    ).lower()
    urgent_keywords = (
        "garbage",
        "waste",
        "overflow",
        "drain",
        "sewage",
        "water",
        "electric",
        "light",
        "road",
        "traffic",
        "fire",
        "safety",
    )
    if any(keyword in searchable_text for keyword in urgent_keywords):
        return "High"
    if issue.assigned_department:
        return "Medium"
    return "Standard"


def build_issue_timeline(issue: Issue) -> list[dict]:
    public_status = public_status_for_issue(issue)
    final_label = "Rejected" if public_status == "Rejected" else "Resolved"
    final_step_complete = public_status in {"Resolved", "Rejected"}
    assigned_complete = bool(issue.assigned_at or issue.assigned_department or issue.worker_status)
    in_progress_complete = public_status in {"In Progress", "Resolved", "Rejected"}
    updated_at = issue.updated_at or issue.created_at

    return [
        {
            "status": "Submitted",
            "timestamp": isoformat_app_datetime(issue.created_at),
            "complete": True,
        },
        {
            "status": "Assigned",
            "timestamp": isoformat_app_datetime(issue.assigned_at),
            "complete": assigned_complete,
        },
        {
            "status": "In Progress",
            "timestamp": isoformat_app_datetime(updated_at) if in_progress_complete else None,
            "complete": in_progress_complete,
        },
        {
            "status": final_label,
            "timestamp": isoformat_app_datetime(updated_at) if final_step_complete else None,
            "complete": final_step_complete,
        },
    ]


def build_complaint_tracking_payload(issue: Issue) -> dict:
    updated_at = issue.updated_at or issue.created_at
    return {
        "id": issue.complaint_number,
        "type": issue.category or "General",
        "status": public_status_for_issue(issue),
        "priority": derive_issue_priority(issue),
        "location": issue.location,
        "createdAt": isoformat_app_datetime(issue.created_at),
        "updatedAt": isoformat_app_datetime(updated_at),
        "description": issue.description,
        "title": issue.title,
        "timeline": build_issue_timeline(issue),
        "closureReceiptUrl": (
            f"/receipt/closure/{issue.complaint_number}"
            if issue.status in {"Resolved", "Rejected"}
            else None
        ),
    }


def build_mobile_tracking_summary(issue: Issue) -> dict:
    updated_at = issue.updated_at or issue.created_at
    return {
        "id": issue.complaint_number,
        "type": issue.category or "General",
        "status": public_status_for_issue(issue),
        "priority": derive_issue_priority(issue),
        "location": issue.location,
        "createdAt": isoformat_app_datetime(issue.created_at),
        "updatedAt": isoformat_app_datetime(updated_at),
        "title": issue.title,
    }


def serialize_admin_issue_card(issue: Issue, user_name: Optional[str] = None) -> dict:
    return {
        "id": issue.id,
        "complaint_number": issue.complaint_number,
        "title": issue.title,
        "description": issue.description,
        "status": issue.status,
        "location": issue.location,
        "category": issue.category,
        "user_id": issue.user_id,
        "user_name": user_name or (f"User #{issue.user_id}" if issue.user_id is not None else "Unknown User"),
        "created_at": isoformat_app_datetime(issue.created_at),
        "assigned_department": issue.assigned_department,
        "assigned_worker_id": issue.assigned_worker_id,
        "assignment_deadline": isoformat_app_datetime(issue.assignment_deadline),
        "assignment_duration_label": issue.assignment_duration_label,
        "worker_status": issue.worker_status or "Assigned",
        "worker_resolution_requested_at": isoformat_app_datetime(issue.worker_resolution_requested_at),
        "media_urls": [
            as_public_media_url(file_name)
            for file_name in normalize_media_items(issue.media_urls)
        ],
    }


def serialize_admin_recent_issue(issue: Issue) -> dict:
    return {
        "id": issue.id,
        "complaint_number": issue.complaint_number,
        "title": issue.title,
        "status": issue.status,
        "location": issue.location,
        "category": issue.category,
        "user_id": issue.user_id,
        "created_at": isoformat_app_datetime(issue.created_at),
        "assigned_department": issue.assigned_department,
        "assigned_worker_id": issue.assigned_worker_id,
        "assignment_deadline": isoformat_app_datetime(issue.assignment_deadline),
        "assignment_duration_label": issue.assignment_duration_label,
        "worker_status": issue.worker_status or "Assigned",
        "worker_resolution_requested_at": isoformat_app_datetime(issue.worker_resolution_requested_at),
        "worker_status_message": (
            f"Worker: {issue.assigned_worker_id}"
            if issue.worker_status in {"In Progress", "Resolved", "Rejected"}
            else (f"Assigned to {issue.assigned_worker_id}" if issue.assigned_worker_id else "")
        ),
    }


def serialize_worker_issue_card(issue: Issue) -> dict:
    return {
        "id": issue.id,
        "complaint_number": issue.complaint_number,
        "title": issue.title,
        "description": issue.description,
        "location": issue.location,
        "status": issue.status,
        "category": issue.category,
        "created_at": isoformat_app_datetime(issue.created_at),
        "assignment_deadline": isoformat_app_datetime(issue.assignment_deadline),
        "assignment_duration_label": issue.assignment_duration_label,
        "assigned_department": issue.assigned_department,
        "assigned_worker_id": issue.assigned_worker_id,
        "worker_status": issue.worker_status or "Assigned",
        "worker_resolution_requested_at": isoformat_app_datetime(issue.worker_resolution_requested_at),
        "media_urls": [
            as_public_media_url(file_name)
            for file_name in normalize_media_items(issue.media_urls)
        ],
    }


def serialize_user_issue(issue: Issue) -> dict:
    return {
        "id": issue.id,
        "complaint_number": issue.complaint_number,
        "title": issue.title,
        "description": issue.description,
        "location": issue.location,
        "status": issue.status,
        "media": issue.media_urls if issue.media_urls else [],
        "created_at": isoformat_app_datetime(issue.created_at),
    }


def build_user_dashboard_bootstrap_payload(current_user: User, db: Session) -> dict:
    issues = (
        db.query(Issue)
        .filter(Issue.user_id == current_user.id)
        .order_by(Issue.created_at.desc())
        .all()
    )
    visible_alerts = [
        item
        for item in get_visible_emergency_alerts()
        if (item.get("user") or {}).get("id") == current_user.id
    ]

    return {
        "stats": {
            "total_issues": len(issues),
            "pending": sum(1 for issue in issues if issue.status not in {"Resolved", "Rejected"}),
            "resolved": sum(1 for issue in issues if issue.status == "Resolved"),
        },
        "complaints": [serialize_user_issue(issue) for issue in issues],
        "alerts": visible_alerts[-20:][::-1],
        "monitoring_alerts": monitoring_alerts[-25:][::-1],
    }


def persist_issue_uploads_and_assets(
    issue_id: int,
    deferred_uploads: list[dict],
    public_scan_base_url: str = None,
) -> None:
    db = SessionLocal()
    try:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            return

        saved_media_names = []
        for item in deferred_uploads or []:
            original_name = sanitize_text_input(item.get("original_name") or "upload")
            filename = f"{uuid.uuid4()}_{original_name}"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, "wb") as buffer:
                buffer.write(item.get("content") or b"")
            saved_media_names.append(filename)

        issue.media_urls = ",".join(saved_media_names) if saved_media_names else issue.media_urls
        issue.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(issue)
        save_submission_status(issue.complaint_number, {"media_ready": True})

        write_qr_png_file(issue.complaint_number, public_base_url=public_scan_base_url)
        save_submission_status(issue.complaint_number, {"qr_ready": True})

        receipt_path = receipt_file_path(issue.complaint_number)
        build_issue_receipt_pdf(issue, receipt_path, public_base_url=public_scan_base_url)
        save_submission_status(
            issue.complaint_number,
            {
                "receipt_ready": True,
                "notification_ready": True,
                "status": "ready",
            },
        )
        publish_panel_event(
            "issue-assets-ready",
            {
                "issue_id": issue.id,
                "complaint_number": issue.complaint_number,
            },
        )
    except Exception as exc:
        if "issue" in locals() and issue is not None:
            save_submission_status(
                issue.complaint_number,
                {"status": "failed", "error": f"Artifact preparation failed: {exc}"},
            )
    finally:
        db.close()


@app.post("/issues", response_model=None)
async def create_issue(
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    files: Optional[List[UploadFile]] = File(
        default=None,
        description="Choose one or more files of any format (you can multi-select in file picker)."
    ),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    form = await request.form() if request is not None else None
    title = title if title is not None else (form.get("title") if form is not None else None)
    description = (
        description if description is not None else (form.get("description") if form is not None else None)
    )
    location = location if location is not None else (form.get("location") if form is not None else None)
    category = category if category is not None else (form.get("category") if form is not None else None)

    title = validate_text_field(title, field_name="Title", min_length=3, max_length=120)
    description = validate_text_field(description, field_name="Description", min_length=10, max_length=2000)
    location = validate_text_field(location, field_name="Location", min_length=3, max_length=255)
    category = validate_issue_category(category)
    deferred_uploads = []

    # Support clients that send multipart keys as both `files` and `files[]`.
    # Only re-read the multipart body when FastAPI did not already populate `files`.
    if form is not None and not files:
        fallback_files = []
        for key, value in form.multi_items():
            if key in {"files", "files[]"} and hasattr(value, "filename"):
                fallback_files.append(value)
        if fallback_files:
            files = fallback_files

    files = validate_uploads(files)

    if files:
        for file in files:
            original_name = sanitize_text_input(file.filename or "upload")
            file.file.seek(0, os.SEEK_END)
            file_size = file.file.tell()
            file.file.seek(0)
            if file_size > MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail=f"{original_name} is too large. Maximum size is {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB",
                )
            file.file.seek(0)
            deferred_uploads.append(
                {
                    "original_name": original_name,
                    "content_type": file.content_type,
                    "content": await file.read(),
                }
            )

    # Generate complaint number
    last_issue = db.query(Issue).order_by(Issue.id.desc()).first()

    if last_issue:
        new_number = last_issue.id + 1
    else:
        new_number = 1

    complaint_number = f"US-{new_number:04d}"
    created_at = datetime.utcnow()

    issue = Issue(
        user_id=current_user.id,
        complaint_number=complaint_number,
        title=title,
        description=description,
        location=location,
        category=category,
        media_urls=None,
        status="Pending",
        admin_deleted=0,
        created_at=created_at,
        updated_at=created_at,
    )

    db.add(issue)
    db.commit()
    db.refresh(issue)
    public_scan_base_url = resolve_public_scan_base_url(request)
    initialize_submission_status(issue, has_uploads=bool(deferred_uploads))
    write_qr_png_file(
        issue.complaint_number,
        request=request,
        public_base_url=public_scan_base_url,
    )
    save_submission_status(issue.complaint_number, {"qr_ready": True})
    submission_status = serialize_submission_status(issue)
    if background_tasks is not None:
        background_tasks.add_task(
            persist_issue_uploads_and_assets,
            issue.id,
            deferred_uploads,
            public_scan_base_url,
        )
    else:
        persist_issue_uploads_and_assets(issue.id, deferred_uploads, public_scan_base_url)
    publish_panel_event(
        "issue-created",
        {
            "issue": serialize_admin_issue_card(issue, current_user.full_name or current_user.email or "Citizen"),
            "recent_issue": serialize_admin_recent_issue(issue),
        },
    )

    return {
        "message": "Issue created successfully",
        "report_id": issue.id,
        "issue_id": issue.id,
        "complaint_number": complaint_number,
        "scan_url": build_scan_url(complaint_number, request, public_scan_base_url),
        "submission_status_url": f"{resolve_api_base_url(request)}/issues/{issue.id}/submission-status",
        "submission_status": submission_status,
    }


@app.get("/issues/{issue_id}/submission-status")
def get_issue_submission_status(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    issue = db.query(Issue).filter(Issue.id == issue_id, Issue.user_id == current_user.id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return serialize_submission_status(issue)

# -----------------------------
# GET ISSUES (PUBLIC)
# -----------------------------
@app.get("/issues")
def get_issues(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cache_key = f"user-issues:{current_user.id}"
    return get_or_compute_cached_json(
        cache_key,
        5,
        lambda: [
            serialize_user_issue(issue)
            for issue in db.query(Issue)
            .filter(Issue.user_id == current_user.id)
            .order_by(Issue.created_at.desc())
            .all()
        ],
    )


@app.get("/user/dashboard-bootstrap")
def get_user_dashboard_bootstrap(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cache_key = f"user-dashboard:{current_user.id}"
    return get_or_compute_cached_json(
        cache_key,
        5,
        lambda: build_user_dashboard_bootstrap_payload(current_user, db),
    )


@app.get("/api/complaints/mobile/{phone}")
def track_complaints_by_mobile(
    phone: str,
    db: Session = Depends(get_db),
):
    current_user = ensure_public_user(db)
    normalized_phone = normalize_phone_lookup_value(phone)
    if not normalized_phone:
        raise HTTPException(status_code=400, detail="Please enter mobile number")
    if len(normalized_phone) < 10:
        raise HTTPException(status_code=400, detail="Enter a valid mobile number")
    if not matches_verified_phone(normalized_phone, current_user.phone):
        return {"complaints": []}

    issues = (
        db.query(Issue)
        .filter(Issue.user_id == current_user.id)
        .order_by(Issue.created_at.desc())
        .all()
    )
    return {"complaints": [build_mobile_tracking_summary(issue) for issue in issues]}


@app.get("/api/complaints/{complaint_number}")
def get_complaint_tracking_details(
    complaint_number: str,
    db: Session = Depends(get_db),
):
    normalized_complaint_number = normalize_complaint_lookup_id(complaint_number)
    issue = (
        db.query(Issue)
        .filter(
            Issue.complaint_number == normalized_complaint_number,
        )
        .first()
    )

    if not issue:
        raise HTTPException(status_code=404, detail="No complaint found. Please check your ID.")

    return build_complaint_tracking_payload(issue)
# -----------------------------
# GET ISSUES (ADMIN)
# -----------------------------
@app.get("/admin/issue-ids", include_in_schema=False)
def get_issue_ids(_: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    issues = db.query(Issue).filter(admin_visible_issue_filter(), Issue.status == "Pending").all()

    return [
        {
            "id": issue.id,
            "complaint_number": issue.complaint_number
        }
        for issue in issues
    ]


# -----------------------------
# UPDATE STATUS (ADMIN)
# -----------------------------
@app.put("/admin/issues/{issue_id}", include_in_schema=False)
def update_status(
    issue_id: int,
    status: IssueStatus = Form(...),
    request: Request = None,
    background_tasks: BackgroundTasks = None,
    _: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    issue = db.query(Issue).filter(Issue.id == issue_id, admin_visible_issue_filter()).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    requested_status = status.value if hasattr(status, "value") else str(status)
    if requested_status in {"In Progress", "Resolved", "Rejected"} and (issue.worker_status or "Assigned") == "Assigned":
        raise HTTPException(status_code=400, detail="Status has not been updated by the worker yet")
    if requested_status == "Resolved" and issue.worker_status != "Resolved":
        raise HTTPException(status_code=400, detail="Worker has not updated the status as resolved yet")

    issue.status = requested_status
    issue.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(issue)
    publish_panel_event(
        "issue-status-updated",
        {
            "issue_id": issue.id,
            "status": issue.status,
            "worker_status": issue.worker_status,
            "recent_issue": serialize_admin_recent_issue(issue),
        },
    )

    mail_sent = None
    mail_message = "No notification needed"
    if issue.status in {"Resolved", "Rejected"} and issue.user_id:
        user = db.query(User).filter(User.id == issue.user_id).first()
        if user:
            if background_tasks is not None:
                background_tasks.add_task(send_status_update_email, user, issue, request)
                mail_sent = True
                mail_message = "User notification queued"
            else:
                mail_sent, mail_message = send_status_update_email(user, issue, request)
        else:
            mail_sent = False
            mail_message = "User not found for notification"

    return {
        "message": "Status updated successfully",
        "issue_id": issue.id,
        "new_status": issue.status,
        "mail_sent": mail_sent,
        "mail_status": mail_message,
    }


@app.post("/admin/issues/{issue_id}/assign", include_in_schema=False)
def assign_issue(
    issue_id: int,
    payload: ComplaintAssignPayload,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    issue = db.query(Issue).filter(Issue.id == issue_id, admin_visible_issue_filter()).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    department = normalize_department(payload.department)
    requested_worker_id = " ".join(str(payload.worker_id or "").strip().split()).upper()
    if not requested_worker_id:
        raise HTTPException(status_code=400, detail="Choose a worker from this department")
    assigned_worker = db.query(Worker).filter(
        Worker.worker_id.ilike(requested_worker_id),
        Worker.department == department,
        Worker.is_active == True,
    ).first()
    if not assigned_worker:
        raise HTTPException(status_code=400, detail="Choose a valid active worker from the selected department")
    deadline, duration_label = compute_assignment_deadline(payload.duration_value, payload.duration_unit)

    issue.assigned_department = department
    issue.assigned_worker_id = assigned_worker.worker_id
    issue.assignment_deadline = deadline
    issue.assignment_duration_label = duration_label
    issue.assigned_by_admin_id = admin["id"]
    issue.worker_status = "Assigned"
    issue.worker_resolution_requested_at = None
    issue.assigned_at = datetime.utcnow()
    if issue.status == "Pending":
        issue.status = "In Progress"
    issue.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(issue)
    publish_panel_event(
        "issue-assigned",
        {
            "issue_id": issue.id,
            "assigned_department": issue.assigned_department,
            "assigned_worker_id": issue.assigned_worker_id,
            "status": issue.status,
            "worker_status": issue.worker_status,
            "assignment_deadline": isoformat_app_datetime(issue.assignment_deadline),
            "assignment_duration_label": issue.assignment_duration_label,
            "issue": serialize_worker_issue_card(issue),
            "recent_issue": serialize_admin_recent_issue(issue),
        },
    )

    return {
        "message": "Complaint assigned successfully",
        "issue_id": issue.id,
        "assigned_department": issue.assigned_department,
        "assigned_worker_id": issue.assigned_worker_id,
        "assignment_deadline": isoformat_app_datetime(issue.assignment_deadline),
        "assignment_duration_label": issue.assignment_duration_label,
        "status": issue.status,
    }

# -----------------------------
# DELETE ISSUE (ADMIN)
# -----------------------------
@app.delete("/admin/issues/{issue_id}", include_in_schema=False)
def delete_issue(issue_id: int, _: dict = Depends(get_current_admin), db: Session = Depends(get_db)):

    issue = db.query(Issue).filter(Issue.id == issue_id, admin_visible_issue_filter()).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    issue.admin_deleted = 1
    issue.admin_deleted_at = datetime.utcnow()
    issue.updated_at = datetime.utcnow()
    db.commit()
    publish_panel_event(
        "issue-hidden-from-admin",
        {
            "issue_id": issue_id,
        },
    )

    return {
        "message": "Issue removed from admin panel successfully",
        "deleted_issue_id": issue_id
    }

    return {"message": "Issue deleted successfully"}

@app.get("/track/{complaint_number}")
def track_issue(
    complaint_number: str,
    db: Session = Depends(get_db)
):

    normalized_complaint_number = normalize_complaint_lookup_id(complaint_number)
    issue = db.query(Issue).filter(
        Issue.complaint_number == normalized_complaint_number
    ).first()

    if not issue:
        raise HTTPException(status_code=404, detail="No complaint found. Please check your ID.")

    return build_complaint_tracking_payload(issue)


@app.get("/qr/{complaint_number}")
def get_complaint_qr(
    complaint_number: str,
    request: Request,
    db: Session = Depends(get_db)
):
    issue = db.query(Issue).filter(Issue.complaint_number == complaint_number).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Complaint not found")

    status_payload = load_submission_status(issue.complaint_number)
    if status_payload and not status_payload.get("qr_ready"):
        return JSONResponse(
            status_code=202,
            content={"detail": "QR code is still being prepared", "status": "processing"},
        )

    png_bytes = generate_qr_png_bytes(issue.complaint_number, request)
    png_path = qr_file_path(issue.complaint_number)
    try:
        with open(png_path, "wb") as handle:
            handle.write(png_bytes)
    except Exception:
        pass

    return Response(
        content=png_bytes,
        media_type="image/png"
    )


@app.get("/scan/{complaint_number}", response_class=HTMLResponse)
def scan_complaint_status(
    complaint_number: str,
    db: Session = Depends(get_db)
):
    issue = db.query(Issue).filter(Issue.complaint_number == complaint_number).first()
    if not issue:
        return HTMLResponse(
            status_code=404,
            content="""
            <html><body style="font-family:Arial,sans-serif;padding:24px;background:#f8fafc;color:#0f172a;">
            <h2>Complaint not found</h2>
            <p>Please verify the complaint number and try again.</p>
            </body></html>
            """
        )

    status_color = "#f59e0b"
    if issue.status == "Resolved":
        status_color = "#16a34a"
    elif issue.status == "Rejected":
        status_color = "#dc2626"
    elif issue.status == "In Progress":
        status_color = "#2563eb"

    safe_number = escape(issue.complaint_number or "")
    safe_title = escape(issue.title or "")
    safe_description = escape(issue.description or "")
    safe_location = escape(issue.location or "")
    safe_category = escape(issue.category or "General")
    safe_status = escape(issue.status or "Pending")
    safe_created = format_app_datetime(issue.created_at, "%d %b %Y, %I:%M %p")

    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Complaint {safe_number}</title>
      <style>
        body {{
          margin: 0;
          min-height: 100vh;
          font-family: 'Segoe UI', Arial, sans-serif;
          background: linear-gradient(140deg, #f8fafc, #e2e8f0);
          color: #0f172a;
          display: grid;
          place-items: center;
          padding: 16px;
        }}
        .card {{
          width: min(95vw, 760px);
          background: rgba(255,255,255,0.92);
          border: 1px solid #cbd5e1;
          border-radius: 18px;
          padding: 20px;
          box-shadow: 0 16px 45px rgba(15,23,42,0.12);
        }}
        .meta {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
          margin-bottom: 12px;
        }}
        .pill {{
          background: {status_color};
          color: #fff;
          border-radius: 999px;
          padding: 6px 12px;
          font-size: 13px;
          font-weight: 700;
        }}
        .tag {{
          background: #ccfbf1;
          color: #0f766e;
          border-radius: 999px;
          padding: 5px 10px;
          font-size: 12px;
          font-weight: 700;
        }}
        .grid {{
          display: grid;
          grid-template-columns: 1fr;
          gap: 10px;
          margin-top: 12px;
        }}
        .item {{
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 12px;
          background: #f8fafc;
        }}
        .item h4 {{
          margin: 0 0 6px;
          font-size: 14px;
          color: #334155;
        }}
        .item p {{
          margin: 0;
          word-break: break-word;
        }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="meta">
          <span class="tag">{safe_category}</span>
          <span class="pill">{safe_status}</span>
        </div>
        <h2 style="margin:0 0 6px;">Complaint {safe_number}</h2>
        <p style="margin:0;color:#475569;">Live status view from Urban Sentinel QR scan.</p>

        <div class="grid">
          <div class="item"><h4>Issue</h4><p>{safe_title}</p></div>
          <div class="item"><h4>Reported On</h4><p>{safe_created}</p></div>
          <div class="item"><h4>Location</h4><p>{safe_location}</p></div>
          <div class="item"><h4>Note</h4><p>{safe_description}</p></div>
        </div>
      </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

def build_issue_receipt_pdf(
    issue: Issue,
    pdf_path: str,
    request: Request = None,
    public_base_url: str = None,
):
    setup_pdf_fonts()

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    margin = 30
    page_number = 1

    def apply_page_style(page_no: int):
        # Light watermark in the page background.
        c.saveState()
        c.setFillColorRGB(0.88, 0.91, 0.95)
        c.translate(width / 2, height / 2)
        c.rotate(35)
        c.setFont(PDF_FONT_BOLD, 44)
        c.drawCentredString(0, 0, "URBAN SENTINEL")
        c.restoreState()

        # Double-border layout for a cleaner, professional receipt style.
        c.setStrokeColorRGB(0.18, 0.30, 0.45)
        c.setLineWidth(1.3)
        c.rect(margin, margin, width - 2 * margin, height - 2 * margin)

        c.setStrokeColorRGB(0.70, 0.76, 0.84)
        c.setLineWidth(0.6)
        c.rect(margin + 6, margin + 6, width - 2 * (margin + 6), height - 2 * (margin + 6))

        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1)
        c.setFont(PDF_FONT_REGULAR, 9)
        c.setFillColorRGB(0.35, 0.35, 0.35)
        c.drawString(margin + 12, margin + 12, f"Complaint: {issue.complaint_number}")
        c.drawRightString(width - margin - 12, margin + 12, f"Page {page_no}")
        c.setFillColorRGB(0, 0, 0)

    def next_page():
        nonlocal page_number
        c.showPage()
        page_number += 1
        apply_page_style(page_number)

    y = height - 100

    # Border + page footer for page 1
    apply_page_style(page_number)

    # Logo
    logo_path = os.path.join(BASE_DIR, "assets", "logo.png")
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(
            logo,
            margin + 10,
            height - margin - 100,
            width=100,
            height=100,
            preserveAspectRatio=True,
            mask='auto'
        )

    # Header
    c.setFont(PDF_FONT_BOLD, 18)
    c.drawCentredString(width / 2, y, "URBAN SENTINEL")
    y -= 25
    c.setFont(PDF_FONT_REGULAR, 14)
    c.drawCentredString(width / 2, y, "Complaint Acknowledgement Receipt")
    y -= 10
    c.setStrokeColorRGB(0.20, 0.35, 0.50)
    c.setLineWidth(1)
    c.line(60, y, width - 60, y)
    c.setStrokeColorRGB(0, 0, 0)
    y -= 40

    # Complaint Details
    created_date = format_app_datetime(issue.created_at, "%d-%m-%Y")
    created_time = format_app_datetime(issue.created_at, "%I:%M %p")
    detail_rows = [
        ("Complaint Number", issue.complaint_number or "N/A"),
        ("Title", issue.title or "N/A"),
        ("Description", issue.description or "N/A"),
        ("Location", issue.location or "N/A"),
        ("Status", issue.status or "Pending"),
        ("Date", created_date),
        ("Time", created_time),
    ]

    label_x = 60
    value_x = 185
    for label, value in detail_rows:
        c.setFont(PDF_FONT_BOLD, 12)
        c.drawString(label_x, y, f"{label} :")
        c.setFont(PDF_FONT_REGULAR, 12)
        wrapped_lines = wrap_pdf_text(c, value, PDF_FONT_REGULAR, 12, width - value_x - 60)
        for idx, line in enumerate(wrapped_lines):
            c.drawString(value_x, y, line)
            if idx < len(wrapped_lines) - 1:
                y -= 18
        y -= 22
        if y < 120:
            next_page()
            y = height - 90

    c.line(60, y, width - 60, y)
    y -= 30

    # MEDIA SECTION
    media_files = []

    if issue.media_urls:
        if isinstance(issue.media_urls, str):
            media_files = [name.strip() for name in issue.media_urls.split(",") if name.strip()]
        elif isinstance(issue.media_urls, list):
            media_files = [name.strip() for name in issue.media_urls if name.strip()]

    image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
    image_files = []
    other_files = []

    for file_name in media_files:
        media_path = os.path.join(UPLOAD_FOLDER, file_name)
        if not os.path.exists(media_path):
            continue
        ext = os.path.splitext(file_name)[1].lower()
        if ext in image_extensions:
            image_files.append((file_name, media_path))
        else:
            other_files.append(file_name)

    c.setFont(PDF_FONT_BOLD, 11)
    c.drawString(60, y, f"Total Attachments: {len(image_files) + len(other_files)}")
    y -= 18

    # Dynamic image gallery layout based on selected file count.
    if image_files:
        c.setFont(PDF_FONT_BOLD, 12)
        c.drawString(60, y, "Uploaded Images")
        y -= 16

        image_count = len(image_files)
        if image_count == 1:
            columns = 1
        elif image_count <= 4:
            columns = 2
        else:
            columns = 3

        gallery_left = 60
        gallery_right = width - 60
        gallery_gap = 12
        tile_width = (gallery_right - gallery_left - (gallery_gap * (columns - 1))) / columns
        tile_height = tile_width * 0.62
        if image_count == 1:
            max_tile_height = max(120, y - 230)
            tile_height = min(180, max_tile_height)
            tile_width = min(320, tile_height * 1.5)

        row_height = tile_height + 24
        footer_safe_area = 105
        col = 0

        for idx, (file_name, media_path) in enumerate(image_files, start=1):
            if col == 0 and (y - row_height) < footer_safe_area:
                next_page()
                y = height - 90
                c.setFont(PDF_FONT_BOLD, 12)
                c.drawString(60, y, "Uploaded Images (Continued)")
                y -= 20

            if columns == 1:
                x = (width - tile_width) / 2
            else:
                x = gallery_left + col * (tile_width + gallery_gap)
            short_name = file_name if len(file_name) <= 28 else f"{file_name[:25]}..."
            c.setFont(PDF_FONT_REGULAR, 8)
            c.drawString(x, y, f"{idx}. {short_name}")

            try:
                img = ImageReader(media_path)
                c.drawImage(
                    img,
                    x,
                    y - tile_height - 2,
                    width=tile_width,
                    height=tile_height,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except Exception as e:
                print("Media error:", e)
                c.rect(x, y - tile_height - 2, tile_width, tile_height)
                c.setFont(PDF_FONT_ITALIC, 8)
                c.drawString(x + 5, y - 15, "Preview unavailable")

            col += 1
            if col == columns:
                col = 0
                y -= row_height

        if col != 0:
            y -= row_height
    else:
        c.setFont(PDF_FONT_ITALIC, 10)
        c.drawString(60, y, "No image attachments found for this complaint.")
        y -= 20

    if other_files:
        if y < 160:
            next_page()
            y = height - 90
        c.setFont(PDF_FONT_BOLD, 11)
        c.drawString(60, y, "Other Uploaded Files")
        y -= 16
        c.setFont(PDF_FONT_REGULAR, 9)
        for file_name in other_files:
            if y < 120:
                next_page()
                y = height - 90
                c.setFont(PDF_FONT_BOLD, 11)
                c.drawString(60, y, "Other Uploaded Files (Continued)")
                y -= 16
                c.setFont(PDF_FONT_REGULAR, 9)
            wrapped_lines = wrap_pdf_text(c, f"- {file_name}", PDF_FONT_REGULAR, 9, width - 130)
            for line in wrapped_lines:
                c.drawString(70, y, line)
                y -= 12

    # Professional Message + QR layout (prevents overlap on receipt)
    if y < 170:
        next_page()
        y = height - 130

    message_lines = [
        "Thank you for reporting this issue.",
        "Your complaint has been successfully registered in the Urban Sentinel system.",
        "Our concerned authorities will review and resolve it at the earliest possible time.",
        "You can track your complaint status anytime using your Complaint Number."
    ]
    qr_box_size = 120
    qr_x = width - 180
    qr_y = 120
    text_right_limit = qr_x - 25
    text_width = text_right_limit - 60

    c.setFont(PDF_FONT_ITALIC, 11)
    y -= 8
    for line in message_lines:
        for wrapped_line in wrap_pdf_text(c, line, PDF_FONT_ITALIC, 11, text_width):
            c.drawString(60, y, wrapped_line)
            y -= 18

    qr_image = ImageReader(
        BytesIO(
            generate_qr_png_bytes(
                issue.complaint_number,
                request,
                public_base_url=public_base_url,
            )
        )
    )
    c.drawImage(qr_image, qr_x, qr_y, width=qr_box_size, height=qr_box_size)

    c.setFont(PDF_FONT_REGULAR, 9)
    c.drawString(qr_x - 6, qr_y - 15, "Scan to Track Complaint")

    # Footer
    c.setFont(PDF_FONT_REGULAR, 10)
    c.drawCentredString(width / 2, 50, "This is a system generated receipt. No signature required.")

    c.save()
    return pdf_path


@app.get("/receipt/{complaint_number}")
def generate_receipt(
    complaint_number: str,
    request: Request = None,
    db: Session = Depends(get_db)
):
    issue = db.query(Issue).filter(
        Issue.complaint_number == complaint_number
    ).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Complaint not found")

    pdf_path = receipt_file_path(complaint_number)
    if not os.path.exists(pdf_path):
        status_payload = load_submission_status(complaint_number)
        if status_payload and not status_payload.get("receipt_ready"):
            return JSONResponse(
                status_code=202,
                content={"detail": "Receipt is still being prepared", "status": "processing"},
            )
        build_issue_receipt_pdf(issue, pdf_path, request)

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(pdf_path)
    )


@app.get("/receipt/closure/{complaint_number}")
def generate_closure_receipt(
    complaint_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    issue = db.query(Issue).filter(
        Issue.complaint_number == complaint_number,
        Issue.user_id == current_user.id,
    ).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if issue.status not in {"Resolved", "Rejected"}:
        raise HTTPException(status_code=400, detail="Closure receipt available only for resolved/rejected complaints")

    pdf_bytes = build_closure_receipt_pdf_bytes(issue, current_user)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="closure_receipt_{complaint_number}.pdf"'},
    )

@app.get("/admin/stats", include_in_schema=False)
def get_admin_stats(_: dict = Depends(get_current_admin), db: Session = Depends(get_db)):

    total = db.query(Issue).filter(admin_visible_issue_filter()).count()

    pending = db.query(Issue).filter(admin_visible_issue_filter(), Issue.status == "Pending").count()

    resolved = db.query(Issue).filter(admin_visible_issue_filter(), Issue.status == "Resolved").count()

    return {
        "total_issues": total,
        "pending": pending,
        "resolved": resolved
    }


def _build_admin_panel_payload(db: Session) -> dict:
    pending_issues = db.query(Issue).filter(admin_visible_issue_filter(), Issue.status == "Pending").order_by(Issue.id.desc()).limit(12).all()
    recent_issues = db.query(Issue).filter(admin_visible_issue_filter()).order_by(Issue.id.desc()).limit(12).all()
    all_issues = db.query(Issue).filter(admin_visible_issue_filter()).order_by(Issue.id.desc()).all()
    all_users = db.query(User).order_by(User.id.desc()).all()
    workers = db.query(Worker).order_by(Worker.department.asc(), Worker.worker_id.asc()).all()
    reset_requests = db.query(WorkerResetRequest).order_by(WorkerResetRequest.requested_at.desc()).all()
    next_worker_ids = compute_next_worker_ids(workers)
    department_configs = [serialize_department_config(None, department, next_worker_ids) for department in WORKER_DEPARTMENTS]
    workers_by_pk = {worker.id: worker for worker in workers}
    visible_emergency_rows = get_visible_emergency_alerts()
    alerts_by_user = {}
    for alert in visible_emergency_rows:
        uid = alert.get("user", {}).get("id")
        if uid is None:
            continue
        alerts_by_user.setdefault(uid, []).append(alert)

    complaints_by_user = {}
    for issue in all_issues:
        complaints_by_user.setdefault(issue.user_id, []).append(issue)
    users_by_id = {user.id: user for user in all_users}

    enriched_alerts = []
    for alert in visible_emergency_rows[::-1]:
        alert_user = alert.get("user", {}) or {}
        uid = alert_user.get("id")
        user_issues = complaints_by_user.get(uid, [])
        latest_location = user_issues[0].location if user_issues else None
        enriched_alerts.append(
            {
                **alert,
                "sender_name": alert_user.get("full_name") or "Unknown User",
                "sender_email": alert_user.get("email") or "",
                "sender_phone": alert_user.get("phone") or "",
                "created_at": serialize_app_timestamp(alert.get("created_at")),
                "assigned_at": serialize_app_timestamp(alert.get("assigned_at")),
                "updated_at": serialize_app_timestamp(alert.get("updated_at")),
                "location": alert.get("location") or latest_location or "Location not available",
                "latitude": alert.get("latitude"),
                "longitude": alert.get("longitude"),
                "assigned_department": alert.get("assigned_department"),
                "worker_status": alert.get("worker_status") or ("Assigned" if alert.get("assigned_department") else "Unassigned"),
                "worker_updated_at": serialize_app_timestamp(alert.get("worker_updated_at")),
                "worker_resolution_requested_at": serialize_app_timestamp(alert.get("worker_resolution_requested_at")),
            }
        )

    emergency_total = len(visible_emergency_rows)
    emergency_resolved = sum(
        1 for alert in visible_emergency_rows if str(alert.get("status", "")).strip().lower() == "resolved"
    )
    total_issues = db.query(Issue).filter(admin_visible_issue_filter()).count()
    pending_count = db.query(Issue).filter(admin_visible_issue_filter(), Issue.status == "Pending").count()
    resolved_count = db.query(Issue).filter(admin_visible_issue_filter(), Issue.status == "Resolved").count()
    in_progress_count = db.query(Issue).filter(admin_visible_issue_filter(), Issue.status == "In Progress").count()

    return {
        "stats": {
            "total_issues": total_issues,
            "pending": pending_count,
            "resolved": resolved_count,
            "in_progress": in_progress_count,
            "emergency_total": emergency_total,
            "emergency_resolved": emergency_resolved,
        },
        "pending_issues": [
            {
                "id": item.id,
                "complaint_number": item.complaint_number,
                "title": item.title,
                "status": item.status,
                "created_at": isoformat_app_datetime(item.created_at),
            }
            for item in pending_issues
        ],
        "recent_issues": [serialize_admin_recent_issue(item) for item in recent_issues],
        "reported_complaints": [
            serialize_admin_issue_card(
                item,
                (
                    users_by_id[item.user_id].full_name
                    if item.user_id in users_by_id and users_by_id[item.user_id].full_name
                    else f"User #{item.user_id}" if item.user_id is not None else "Unknown User"
                ),
            )
            for item in all_issues[:50]
        ],
        "recent_alerts": enriched_alerts[-12:][::-1],
        "users": [
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "created_at": isoformat_app_datetime(user.created_at),
                "last_login_at": isoformat_app_datetime(user.last_login_at),
                "complaints": [
                    {
                        "id": issue.id,
                        "complaint_number": issue.complaint_number,
                        "title": issue.title,
                        "status": issue.status,
                        "location": issue.location,
                        "created_at": isoformat_app_datetime(issue.created_at),
                    }
                    for issue in complaints_by_user.get(user.id, [])
                ],
                "emergency_alerts": alerts_by_user.get(user.id, [])[::-1],
            }
            for user in all_users
        ],
        "workers": [serialize_worker(worker) for worker in workers],
        "worker_reset_requests": [
            {
                "id": item.id,
                "worker_db_id": item.worker_id,
                "worker_id": workers_by_pk[item.worker_id].worker_id if item.worker_id in workers_by_pk else f"worker-{item.worker_id}",
                "department": item.department,
                "status": item.status,
                "requested_at": isoformat_app_datetime(item.requested_at),
                "resolved_at": isoformat_app_datetime(item.resolved_at),
            }
            for item in reset_requests
        ],
        "worker_resolution_requests": [
            {
                "id": item.id,
                "complaint_number": item.complaint_number,
                "title": item.title,
                "department": item.assigned_department,
                "worker_status": item.worker_status or "Assigned",
                "requested_at": isoformat_app_datetime(item.worker_resolution_requested_at),
            }
            for item in all_issues
            if item.assigned_department and item.worker_status == "Resolved" and item.worker_resolution_requested_at
        ],
        "departments": WORKER_DEPARTMENTS,
        "department_configs": department_configs,
    }


def normalize_media_items(media_value) -> list[str]:
    if not media_value:
        return []
    if isinstance(media_value, str):
        parts = media_value.split(",")
    elif isinstance(media_value, list):
        parts = media_value
    else:
        return []

    cleaned: list[str] = []
    for item in parts:
        if item is None:
            continue
        text_item = str(item).strip().strip("\"'").strip()
        if text_item:
            cleaned.append(text_item)
    return cleaned


def as_public_media_url(media_item: str) -> str:
    value = str(media_item or "").strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if value.startswith("/uploads/"):
        return value
    safe_file = os.path.basename(value.replace("\\", "/"))
    return f"/uploads/{safe_file}"


@app.get("/admin/panel-data", include_in_schema=False)
def admin_panel_data(_: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return get_or_compute_cached_json(
        "admin-panel:main",
        3,
        lambda: _build_admin_panel_payload(db),
    )


@app.get("/worker/panel-data", include_in_schema=False)
def worker_panel_data(worker: Worker = Depends(get_current_worker), db: Session = Depends(get_db)):
    return get_or_compute_cached_json(
        f"worker-panel:{worker.id}",
        3,
        lambda: _build_worker_panel_payload(worker, db),
    )


def _build_worker_panel_payload(worker: Worker, db: Session) -> dict:
    assigned_issues = db.query(Issue).filter(
        admin_visible_issue_filter(),
        Issue.assigned_department == worker.department,
        or_(Issue.assigned_worker_id == worker.worker_id, Issue.assigned_worker_id == None, Issue.assigned_worker_id == ""),
    ).order_by(Issue.id.desc()).all()
    assigned_emergency_alerts = []
    visible_alerts = list(reversed(get_visible_emergency_alerts()))
    relevant_user_ids = {
        item.get("user", {}).get("id")
        for item in visible_alerts
        if " ".join(str(item.get("assigned_department") or "").strip().split()).lower() == worker.department.lower()
        and item.get("user", {}).get("id") is not None
    }
    user_issue_locations: dict[int, str] = {}
    if relevant_user_ids:
        recent_user_issues = db.query(Issue).filter(
            admin_visible_issue_filter(),
            Issue.user_id.in_(list(relevant_user_ids)),
        ).order_by(Issue.created_at.desc(), Issue.id.desc()).all()
        for issue in recent_user_issues:
            if issue.user_id is None or issue.user_id in user_issue_locations:
                continue
            user_issue_locations[issue.user_id] = issue.location

    for item in visible_alerts:
        assigned_department = " ".join(str(item.get("assigned_department") or "").strip().split())
        if not assigned_department:
            continue
        if assigned_department.lower() != worker.department.lower():
            continue
        alert_user = item.get("user") or {}
        user_id = alert_user.get("id")
        fallback_location = user_issue_locations.get(user_id)
        latitude = item.get("latitude")
        longitude = item.get("longitude")
        if item.get("location"):
            resolved_location = item.get("location")
        elif latitude is not None and longitude is not None:
            resolved_location = f"{round(float(latitude), 4)}, {round(float(longitude), 4)}"
        else:
            resolved_location = fallback_location or "Location not available"
        assigned_emergency_alerts.append(
            {
                "id": item.get("id"),
                "sensor_label": item.get("sensor_label") or "Emergency alert",
                "severity": item.get("severity") or "Normal",
                "status": item.get("status") or "Open",
                "priority": item.get("priority") or "Normal",
                "location": resolved_location,
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "note": item.get("note") or "-",
                "created_at": serialize_app_timestamp(item.get("created_at")),
                "assigned_at": serialize_app_timestamp(item.get("assigned_at")),
                "worker_status": item.get("worker_status") or "Assigned",
                "worker_updated_at": serialize_app_timestamp(item.get("worker_updated_at")),
                "worker_resolution_requested_at": serialize_app_timestamp(item.get("worker_resolution_requested_at")),
                "value": item.get("value") or "-",
                "sender_name": alert_user.get("full_name") or "Citizen",
                "sender_email": alert_user.get("email") or "",
                "sender_phone": alert_user.get("phone") or "",
                "details": (
                    f"{item.get('sensor_label') or 'Emergency alert'} reported with value {item.get('value') or '-'}."
                    f" Priority: {item.get('priority') or 'Normal'}."
                ),
            }
        )
    return {
        "worker": serialize_worker(worker),
        "assigned_issues": [serialize_worker_issue_card(item) for item in assigned_issues],
        "assigned_emergency_alerts": assigned_emergency_alerts,
    }


@app.post("/worker/issues/{issue_id}/status", include_in_schema=False)
def update_worker_issue_status(
    issue_id: int,
    payload: WorkerIssueStatusPayload,
    worker: Worker = Depends(get_current_worker),
    db: Session = Depends(get_db),
):
    issue = db.query(Issue).filter(Issue.id == issue_id, admin_visible_issue_filter()).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if issue.assigned_department != worker.department:
        raise HTTPException(status_code=403, detail="This complaint is not assigned to your department")
    if issue.assigned_worker_id and str(issue.assigned_worker_id).strip().lower() != str(worker.worker_id).strip().lower():
        raise HTTPException(status_code=403, detail="This complaint is assigned to another worker")

    next_status = " ".join(str(payload.status or "").strip().split()).title()
    if next_status not in WORKER_PROGRESS_STATUSES:
        raise HTTPException(status_code=400, detail="Worker status must be Assigned, In Progress, Resolved, or Rejected")

    issue.worker_status = next_status
    issue.updated_at = datetime.utcnow()
    if next_status in {"Resolved", "Rejected"}:
        issue.worker_resolution_requested_at = datetime.utcnow()
    else:
        issue.worker_resolution_requested_at = None
        if issue.status == "Pending":
            issue.status = "In Progress"
        if next_status == "Assigned" and issue.assigned_at is None:
            issue.assigned_at = datetime.utcnow()

    db.commit()
    db.refresh(issue)
    publish_panel_event(
        "worker-issue-status-updated",
        {
            "issue_id": issue.id,
            "status": issue.status,
            "worker_status": issue.worker_status,
            "worker_resolution_requested_at": isoformat_app_datetime(issue.worker_resolution_requested_at),
            "assigned_department": issue.assigned_department,
            "assigned_worker_id": issue.assigned_worker_id,
            "recent_issue": serialize_admin_recent_issue(issue),
        },
    )
    return {
        "message": (
            "Worker decision sent to admin"
            if next_status in {"Resolved", "Rejected"}
            else "Worker status updated successfully"
        ),
        "issue_id": issue.id,
        "worker_status": issue.worker_status,
        "worker_resolution_requested_at": isoformat_app_datetime(issue.worker_resolution_requested_at),
    }


@app.post("/worker/emergency-alerts/{alert_id}/status", include_in_schema=False)
async def update_worker_emergency_status(
    alert_id: str,
    request: Request,
    worker: Worker = Depends(get_current_worker),
):
    alert = find_emergency_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Emergency alert not found")

    assigned_department = " ".join(str(alert.get("assigned_department") or "").strip().split())
    if not assigned_department or assigned_department.lower() != worker.department.lower():
        raise HTTPException(status_code=403, detail="This emergency is not assigned to your department")

    next_status = None
    content_type = (request.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        body = await request.json()
        if isinstance(body, dict):
            next_status = body.get("status")
    else:
        form = await request.form()
        next_status = form.get("status")

    next_status = " ".join(str(next_status or "").strip().split()).title()
    if next_status not in {"Assigned", "In Progress", "Resolved", "Rejected"}:
        raise HTTPException(status_code=400, detail="Worker status must be Assigned, In Progress, Resolved, or Rejected")

    timestamp = datetime.utcnow().isoformat()
    alert["worker_status"] = next_status
    alert["worker_updated_at"] = timestamp
    alert["updated_at"] = timestamp
    if next_status == "Resolved":
        alert["worker_resolution_requested_at"] = timestamp
        alert["status"] = "Awaiting Admin Closure"
    elif next_status == "Rejected":
        alert["worker_resolution_requested_at"] = timestamp
        alert["status"] = "Rejected"
    elif next_status == "In Progress":
        alert["worker_resolution_requested_at"] = None
        alert["status"] = "In Progress"
    else:
        alert["worker_resolution_requested_at"] = None
        alert["status"] = f"Assigned to {assigned_department}"

    save_all_emergency_alerts()
    publish_panel_event(
        "worker-emergency-status-updated",
        {
            "alert_id": alert_id,
            "status": alert.get("status"),
            "worker_status": alert.get("worker_status"),
            "assigned_department": assigned_department,
        },
    )
    return {
        "message": (
            "Emergency worker decision sent to admin."
            if next_status in {"Resolved", "Rejected"}
            else "Emergency worker status updated successfully"
        ),
        "alert_id": alert_id,
        "status": alert.get("status"),
        "worker_status": alert.get("worker_status"),
        "worker_updated_at": serialize_app_timestamp(alert.get("worker_updated_at")),
    }


@app.delete("/worker/emergency-alerts/{alert_id}", include_in_schema=False)
def delete_worker_emergency_alert(
    alert_id: str,
    worker: Worker = Depends(get_current_worker),
):
    alert = find_emergency_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Emergency alert not found")

    assigned_department = " ".join(str(alert.get("assigned_department") or "").strip().split())
    if not assigned_department or assigned_department.lower() != worker.department.lower():
        raise HTTPException(status_code=403, detail="This emergency is not assigned to your department")

    final_status = str(alert.get("status") or "").strip().title()
    if final_status not in {"Resolved", "Rejected"}:
        raise HTTPException(
            status_code=400,
            detail="Worker can delete only after admin closes the emergency as Resolved or Rejected",
        )

    for idx, item in enumerate(emergency_alerts):
        if str(item.get("id")) == str(alert_id):
            emergency_alerts.pop(idx)
            save_all_emergency_alerts()
            publish_panel_event(
                "worker-emergency-deleted",
                {
                    "alert_id": alert_id,
                    "assigned_department": assigned_department,
                },
            )
            return {"message": "Emergency alert deleted successfully", "alert_id": alert_id}

    raise HTTPException(status_code=404, detail="Emergency alert not found")


def worker_login_redirect_target(
    department: Optional[str] = None,
    error_code: Optional[str] = None,
    worker_id: Optional[str] = None,
) -> str:
    target_path = f"/worker/login/{department_slug(department)}" if department else "/worker"
    query = {}
    if error_code:
        query["error"] = error_code
    if worker_id:
        query["worker_id"] = worker_id.strip()
    return f"{target_path}?{urlencode(query)}" if query else target_path


def render_worker_login_page(request: Optional[Request] = None, department: Optional[str] = None):
    department_title = department or "Department"
    department_hint = f"{department_title} Worker Portal" if department else "Worker Department Portal"
    department_json = json.dumps(department) if department else "null"
    error_code = (request.query_params.get("error", "") if request else "").strip().lower()
    worker_id_value = (request.query_params.get("worker_id", "") if request else "").strip()
    error_messages = {
        "invalid_credentials": "Invalid worker ID or password. Please try again or send a reset request to the admin.",
        "department_not_found": "Department login page not found. Please reopen the worker link from the admin panel.",
        "department_mismatch": "This worker ID is not assigned to the selected department.",
    }
    error_message = error_messages.get(error_code, "")
    error_banner = f'<div class="alert" role="alert">{escape(error_message)}</div>' if error_message else ""
    department_input = (
        f'<input type="hidden" name="department" value="{escape(department)}" />'
        if department
        else ""
    )
    html = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__TITLE__</title>
  <style>
    body { margin:0; min-height:100vh; display:grid; place-items:center; font-family:Segoe UI,Arial,sans-serif; background:linear-gradient(150deg,#dbeafe,#ecfccb); color:#0f172a; padding:16px; }
    .shell { width:min(960px,96vw); display:grid; grid-template-columns:1.1fr .9fr; gap:18px; }
    .hero, .card { background:rgba(255,255,255,.92); border:1px solid #dbeafe; border-radius:22px; box-shadow:0 18px 45px rgba(15,23,42,.12); }
    .hero { padding:28px; }
    .hero h1 { margin:0 0 10px; font-size:2rem; }
    .hero p { color:#475569; line-height:1.6; }
    .card { padding:24px; }
    .alert { margin:14px 0 0; padding:12px 14px; border-radius:14px; border:1px solid #fecaca; background:#fef2f2; color:#991b1b; font-weight:700; }
    label { display:block; margin:14px 0 6px; font-weight:700; }
    input { width:100%; box-sizing:border-box; padding:12px; border-radius:12px; border:1px solid #cbd5e1; }
    button { margin-top:16px; width:100%; padding:12px; border:none; border-radius:12px; font-weight:700; background:#0f766e; color:#fff; cursor:pointer; }
    .ghost { background:#e2e8f0; color:#0f172a; }
    .muted { color:#64748b; font-size:.92rem; }
    .msg { min-height:20px; color:#0f766e; font-weight:700; }
    @media (max-width: 840px) { .shell { grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>__HINT__</h1>
      <p>Use the worker ID and password provided by the admin. After login, you will only see complaints assigned to your department.</p>
      <p class="muted">If you forget your password, send a reset request. The admin will review it and set a new password for you.</p>
    </section>
    <section class="card">
      <form method="post" action="/worker/session-login">
        <h2 style="margin:0;">__DEPARTMENT__ Login</h2>
        __ERROR_BANNER__
        __DEPARTMENT_INPUT__
        <label>Worker ID</label>
        <input name="worker_id" placeholder="Enter worker ID" value="__WORKER_ID__" required />
        <label>Password</label>
        <input name="password" type="password" placeholder="Enter password" required />
        <button type="submit">Login to Department</button>
      </form>
      <hr style="margin:22px 0;border:none;border-top:1px solid #e2e8f0;" />
      <div>
        <h3 style="margin:0 0 10px;">Forgot Password</h3>
        <label>Worker ID</label>
        <input id="forgot_worker_id" placeholder="Enter worker ID" />
        <button class="ghost" type="button" onclick="sendResetRequest()">Send Request to Admin</button>
        <p id="msg" class="msg"></p>
      </div>
    </section>
  </main>
  <script>
    async function sendResetRequest() {
      const workerId = document.getElementById('forgot_worker_id').value.trim();
      const msg = document.getElementById('msg');
      msg.textContent = '';
      if (!workerId) { msg.textContent = 'Enter your worker ID.'; return; }
      const res = await fetch('/worker/forgot-password-request', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({ worker_id: workerId, department: __DEPARTMENT_JSON__ })
      });
      const payload = await res.json().catch(() => ({}));
      msg.textContent = payload.message || 'Request submitted';
    }
  </script>
</body>
</html>
"""
    return HTMLResponse(
        content=html
        .replace("__TITLE__", escape(department_hint))
        .replace("__HINT__", escape(department_hint))
        .replace("__DEPARTMENT__", escape(department_title))
        .replace("__ERROR_BANNER__", error_banner)
        .replace("__DEPARTMENT_INPUT__", department_input)
        .replace("__DEPARTMENT_JSON__", department_json)
        .replace("__WORKER_ID__", escape(worker_id_value))
    )


@app.get("/worker", response_class=HTMLResponse, include_in_schema=False)
def worker_login_page(request: Request):
    return render_worker_login_page(request=request)


@app.get("/worker/login/{department_slug_value}", response_class=HTMLResponse, include_in_schema=False)
def worker_department_login_page(request: Request, department_slug_value: str):
    department = find_department_by_slug(department_slug_value)
    return render_worker_login_page(request=request, department=department)


@app.get("/worker/panel", response_class=HTMLResponse, include_in_schema=False)
def worker_panel(_: Worker = Depends(get_current_worker)):
    return HTMLResponse(
        content="""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Urban Sentinel Worker Panel</title>
  <style>
    body { margin:0; font-family:Segoe UI,Arial,sans-serif; background:linear-gradient(145deg,#f8fafc,#dcfce7); color:#0f172a; }
    .wrap { width:min(1100px,95vw); margin:18px auto; }
    .head { display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:12px; }
    .card { background:#fff; border:1px solid #dbeafe; border-radius:18px; padding:14px; box-shadow:0 10px 25px rgba(15,23,42,.08); }
    .stats { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:12px; }
    .muted { color:#64748b; }
    table { width:100%; border-collapse:collapse; }
    th,td { padding:10px 8px; border-bottom:1px solid #e2e8f0; text-align:left; }
    .pill { border-radius:999px; padding:4px 8px; font-size:.75rem; font-weight:700; display:inline-block; }
    .pending { background:#fef3c7; color:#92400e; }
    .progress { background:#dbeafe; color:#1d4ed8; }
    .resolved { background:#dcfce7; color:#166534; }
    .danger { background:#fee2e2; color:#991b1b; }
    .logout { text-decoration:none; padding:10px 12px; border-radius:12px; background:#dcfce7; color:#166534; font-weight:700; }
    .linkBtn { text-decoration:none; display:inline-flex; align-items:center; justify-content:center; padding:8px 10px; border-radius:10px; border:1px solid #cbd5e1; color:#0f172a; background:#fff; font-weight:700; cursor:pointer; }
    .modal { position:fixed; inset:0; background:rgba(2,6,23,.5); display:none; align-items:center; justify-content:center; padding:16px; z-index:50; }
    .modal.show { display:flex; }
    .modalCard { width:min(760px,94vw); max-height:86vh; overflow:auto; background:#ffffff; border-radius:16px; border:1px solid #dbeafe; box-shadow:0 20px 50px rgba(2,6,23,.25); padding:14px; }
    .modalHead { display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:8px; }
    .btn { text-decoration:none; border:none; border-radius:10px; padding:9px 12px; font-weight:700; cursor:pointer; }
    .closeBtn { background:#f1f5f9; border:1px solid #cbd5e1; }
    .thumbGrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(120px,1fr)); gap:10px; margin-top:10px; }
    .thumbGrid img { width:100%; height:100px; object-fit:cover; border-radius:10px; border:1px solid #cbd5e1; background:#f8fafc; }
    .actionLeft { display:inline-flex; align-items:center; gap:8px; flex-wrap:wrap; }
    .mono { font-family:Consolas,monospace; font-size:.83rem; }
    .panelGrid { display:grid; gap:12px; }
    .feedbackToast { position:fixed; right:16px; bottom:16px; padding:12px 14px; border-radius:12px; background:#0f172a; color:#fff; box-shadow:0 16px 36px rgba(15,23,42,.22); display:none; z-index:90; }
    .feedbackToast.show { display:block; }
    @media (max-width: 860px) { .stats { grid-template-columns:1fr 1fr; } }
    @media (max-width: 560px) { .stats { grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <main class="wrap">
    <header class="head">
      <div>
        <h1 style="margin:0;">Worker Department Dashboard</h1>
        <p id="workerMeta" class="muted" style="margin:6px 0 0;">Loading assigned department...</p>
      </div>
      <a class="logout" href="/worker/logout">Logout</a>
    </header>
    <section class="stats">
      <article class="card"><h3 id="assignedCount" style="margin:0;font-size:1.5rem;">-</h3><p class="muted" style="margin:6px 0 0;">Assigned Complaints</p></article>
      <article class="card"><h3 id="pendingCount" style="margin:0;font-size:1.5rem;">-</h3><p class="muted" style="margin:6px 0 0;">Pending or In Progress</p></article>
      <article class="card"><h3 id="deadlineCount" style="margin:0;font-size:1.5rem;">-</h3><p class="muted" style="margin:6px 0 0;">Deadlines Set</p></article>
      <article class="card"><h3 id="alertCount" style="margin:0;font-size:1.5rem;">-</h3><p class="muted" style="margin:6px 0 0;">Emergency Assignments</p></article>
    </section>
    <section class="panelGrid">
      <section class="card">
        <h2 style="margin:0 0 10px;font-size:1.05rem;">Department Complaints</h2>
        <table>
          <thead><tr><th>Complaint</th><th>Issue</th><th>Location</th><th>Status</th><th>Deadline</th><th>Action</th></tr></thead>
          <tbody id="workerRows"></tbody>
        </table>
      </section>
      <section class="card">
        <h2 style="margin:0 0 10px;font-size:1.05rem;">Department Emergency Alerts</h2>
        <table>
          <thead><tr><th>Citizen</th><th>Alert</th><th>Location</th><th>Status</th><th>Assigned</th><th>Action</th></tr></thead>
          <tbody id="workerAlertRows"></tbody>
        </table>
      </section>
    </section>
  </main>
  <div id="workerComplaintModal" class="modal" onclick="closeWorkerComplaintModal(event)">
    <div class="modalCard" onclick="event.stopPropagation()">
      <div class="modalHead">
        <h3 style="margin:0;font-size:1.05rem;">Assigned Complaint</h3>
        <button class="btn closeBtn" onclick="closeWorkerComplaintModal()">Close</button>
      </div>
      <div id="workerComplaintBody"></div>
    </div>
  </div>
  <div id="workerEmergencyModal" class="modal" onclick="closeWorkerEmergencyModal(event)">
    <div class="modalCard" onclick="event.stopPropagation()">
      <div class="modalHead">
        <h3 style="margin:0;font-size:1.05rem;">Assigned Emergency Alert</h3>
        <button class="btn closeBtn" onclick="closeWorkerEmergencyModal()">Close</button>
      </div>
      <div id="workerEmergencyBody"></div>
    </div>
  </div>
  <div id="workerFeedbackToast" class="feedbackToast" role="status" aria-live="polite"></div>
  <script>
    function formatClientMessage(value, fallback) {
      if (typeof value === 'string' && value.trim()) return value;
      if (Array.isArray(value)) {
        const joined = value.map(item => {
          if (typeof item === 'string') return item;
          if (item && typeof item === 'object' && item.msg) return item.msg;
          try { return JSON.stringify(item); } catch (_) { return String(item); }
        }).join(' | ');
        return joined || fallback;
      }
      if (value && typeof value === 'object') {
        if (typeof value.msg === 'string' && value.msg.trim()) return value.msg;
        try { return JSON.stringify(value); } catch (_) { return fallback; }
      }
      return fallback;
    }
    function statusPill(status) {
      const key = (status || '').toLowerCase();
      if (key === 'resolved') return '<span class="pill resolved">Resolved</span>';
      if (key === 'in progress') return '<span class="pill progress">In Progress</span>';
      if (key.includes('assigned')) return '<span class="pill progress">' + (status || 'Assigned') + '</span>';
      if (key === 'danger' || key === 'high') return '<span class="pill danger">' + (status || 'Danger') + '</span>';
      return '<span class="pill pending">' + (status || 'Pending') + '</span>';
    }
    function prettyWorkerDate(value) {
      if (!value) return '-';
      try {
        const normalized = typeof value === 'string' && !/[zZ]|[+-]\\d{2}:\\d{2}$/.test(value)
          ? `${value}Z`
          : value;
        return new Date(normalized).toLocaleString();
      } catch (_) {
        return value;
      }
    }
    let workerIssueStore = [];
    let workerContext = null;
    let workerPanelLoadInFlight = false;
    let workerPanelPausedUntil = 0;
    let workerPanelEventSource = null;
    let workerPanelSocket = null;
    let workerPanelRefreshTimer = null;
    const WORKER_PANEL_CACHE_KEY = 'urbanSentinelWorkerPanelCacheV1';
    const WORKER_PANEL_REFRESH_EVENT_TYPES = new Set([
      'issue-created',
      'emergency-status-updated',
      'emergency-alert-assigned',
      'emergency-alert-deleted'
    ]);
    function showWorkerFeedback(message) {
      const toast = document.getElementById('workerFeedbackToast');
      if (!toast || !message) return;
      toast.textContent = message;
      toast.classList.remove('show');
      window.clearTimeout(showWorkerFeedback._timer);
      requestAnimationFrame(() => toast.classList.add('show'));
      showWorkerFeedback._timer = window.setTimeout(() => {
        toast.classList.remove('show');
      }, 1800);
    }
    function workerPanelHasInteractiveFocus() {
      const active = document.activeElement;
      if (!active) return false;
      if (active.tagName === 'SELECT') return true;
      return false;
    }
    function queueWorkerRefresh(delay = 300) {
      if (workerPanelRefreshTimer) window.clearTimeout(workerPanelRefreshTimer);
      workerPanelRefreshTimer = window.setTimeout(() => {
        workerPanelRefreshTimer = null;
        loadWorkerPanel();
      }, delay);
    }
    function persistWorkerPanelCache() {
      try {
        sessionStorage.setItem(WORKER_PANEL_CACHE_KEY, JSON.stringify({
          worker: workerContext,
          assigned_issues: workerIssueStore,
          assigned_emergency_alerts: window.workerEmergencyStore || []
        }));
      } catch (_) {}
    }
    function applyWorkerPanelData(data, options = {}) {
      workerContext = data.worker || workerContext;
      workerIssueStore = data.assigned_issues || [];
      window.workerEmergencyStore = data.assigned_emergency_alerts || [];
      if (workerContext) {
        document.getElementById('workerMeta').textContent = workerContext.worker_id + ' | ' + workerContext.department + ' Department';
      }
      renderWorkerMetrics();
      renderWorkerIssueRows();
      renderWorkerEmergencyRows();
      if (options.persist !== false) {
        persistWorkerPanelCache();
      }
    }
    function hydrateWorkerPanelFromCache() {
      try {
        const raw = sessionStorage.getItem(WORKER_PANEL_CACHE_KEY);
        if (!raw) return false;
        const cached = JSON.parse(raw);
        if (!cached || typeof cached !== 'object') return false;
        applyWorkerPanelData(cached, { persist: false });
        return true;
      } catch (_) {
        return false;
      }
    }
    function syncWorkerIssue(issueId, patch) {
      workerIssueStore = workerIssueStore.map(item => item.id === issueId ? { ...item, ...patch } : item);
      renderWorkerMetrics();
      renderWorkerIssueRows();
      persistWorkerPanelCache();
    }
    function handleWorkerRealtimeEvent(event) {
      if (!event || !event.type || event.type === 'keep-alive') return;
      if (event.type === 'issue-assigned') {
        const nextIssue = event.payload?.issue;
        const assignedWorkerId = String(nextIssue?.assigned_worker_id || '').trim().toLowerCase();
        const isAssignedToThisWorker = !assignedWorkerId || assignedWorkerId === String(workerContext?.worker_id || '').trim().toLowerCase();
        if (nextIssue && workerContext && isAssignedToThisWorker && String(nextIssue.assigned_department || '').toLowerCase() === String(workerContext.department || '').toLowerCase()) {
          const existingIndex = workerIssueStore.findIndex(item => item.id === nextIssue.id);
          if (existingIndex >= 0) {
            workerIssueStore[existingIndex] = { ...workerIssueStore[existingIndex], ...nextIssue };
          } else {
            workerIssueStore.unshift(nextIssue);
          }
          renderWorkerMetrics();
          renderWorkerIssueRows();
          persistWorkerPanelCache();
          return;
        }
        if (nextIssue?.id) {
          workerIssueStore = workerIssueStore.filter(item => item.id !== nextIssue.id);
          renderWorkerMetrics();
          renderWorkerIssueRows();
          persistWorkerPanelCache();
        }
      }
      if (event.type === 'worker-issue-status-updated' || event.type === 'issue-status-updated') {
        const existing = workerIssueStore.find(item => item.id === event.payload?.issue_id);
        if (!existing) return;
        syncWorkerIssue(event.payload.issue_id, {
          status: event.payload.status ?? existing.status,
          worker_status: event.payload.worker_status ?? existing.worker_status,
          worker_resolution_requested_at: event.payload.worker_resolution_requested_at ?? existing.worker_resolution_requested_at
        });
        return;
      }
      if (event.type === 'issue-hidden-from-admin') {
        const issueId = event.payload?.issue_id;
        workerIssueStore = workerIssueStore.filter(item => item.id !== issueId);
        renderWorkerMetrics();
        renderWorkerIssueRows();
        persistWorkerPanelCache();
        return;
      }
      if (WORKER_PANEL_REFRESH_EVENT_TYPES.has(event.type)) {
        queueWorkerRefresh(0);
      }
    }
    function renderWorkerMetrics() {
      const rows = workerIssueStore || [];
      const alertRows = window.workerEmergencyStore || [];
      document.getElementById('assignedCount').textContent = rows.length;
      document.getElementById('pendingCount').textContent = rows.filter(item => item.status !== 'Resolved' && item.status !== 'Rejected').length;
      document.getElementById('deadlineCount').textContent = rows.filter(item => item.assignment_deadline).length;
      document.getElementById('alertCount').textContent = alertRows.length;
    }
    function canDeleteWorkerEmergency(item) {
      const adminStatus = (item.status || '').trim();
      return adminStatus === 'Resolved' || adminStatus === 'Rejected';
    }
    function renderWorkerIssueRows() {
      const rows = workerIssueStore || [];
      document.getElementById('workerRows').innerHTML = rows.map(item => `
        <tr>
          <td>${item.complaint_number || '-'}</td>
          <td>${item.title || '-'}</td>
          <td>${item.location || '-'}</td>
          <td>
            ${statusPill(item.status)}
            <div style="margin-top:6px;">Worker: ${statusPill(item.worker_status || 'Assigned')}</div>
          </td>
          <td>${item.assignment_duration_label || '-'}${item.assignment_deadline ? ' | ' + prettyWorkerDate(item.assignment_deadline) : ''}</td>
          <td>
            <div class="actionLeft">
              <button type="button" onclick="viewWorkerComplaint(${item.id})">View</button>
              <select id="worker_status_${item.id}">
                <option ${(item.worker_status || 'Assigned') === 'Assigned' ? 'selected' : ''}>Assigned</option>
                <option ${(item.worker_status || 'Assigned') === 'In Progress' ? 'selected' : ''}>In Progress</option>
                <option ${(item.worker_status || 'Assigned') === 'Resolved' ? 'selected' : ''}>Resolved</option>
                <option ${(item.worker_status || 'Assigned') === 'Rejected' ? 'selected' : ''}>Rejected</option>
              </select>
              <button type="button" onclick="updateWorkerComplaintStatus(${item.id})">Update</button>
            </div>
          </td>
        </tr>
      `).join('') || '<tr><td colspan="6">No complaints assigned to your department yet.</td></tr>';
    }
    function renderWorkerEmergencyRows() {
      const alertRows = window.workerEmergencyStore || [];
      document.getElementById('workerAlertRows').innerHTML = alertRows.map(item => `
        <tr>
          <td>${item.sender_name || '-'}</td>
          <td>${item.sensor_label || '-'}</td>
          <td>${item.location || '-'}</td>
          <td>
            ${statusPill(item.status)}
            <div style="margin-top:6px;">${statusPill(item.severity)}</div>
            <div style="margin-top:6px;">Worker: ${statusPill(item.worker_status || 'Assigned')}</div>
          </td>
          <td>${prettyWorkerDate(item.assigned_at)}</td>
          <td>
            <div class="actionLeft">
              <button type="button" onclick="viewWorkerEmergency('${item.id}')">View</button>
              <select id="worker_em_status_${item.id}">
                <option ${(item.worker_status || 'Assigned') === 'Assigned' ? 'selected' : ''}>Assigned</option>
                <option ${(item.worker_status || 'Assigned') === 'In Progress' ? 'selected' : ''}>In Progress</option>
                <option ${(item.worker_status || 'Assigned') === 'Resolved' ? 'selected' : ''}>Resolved</option>
                <option ${(item.worker_status || 'Assigned') === 'Rejected' ? 'selected' : ''}>Rejected</option>
              </select>
              <button type="button" onclick="updateWorkerEmergencyStatus('${item.id}')">Update</button>
              ${canDeleteWorkerEmergency(item) ? `<button type="button" onclick="deleteWorkerEmergency('${item.id}')">Delete</button>` : ''}
            </div>
          </td>
        </tr>
      `).join('') || '<tr><td colspan="6">No emergency alerts assigned to your department yet.</td></tr>';
    }
    function closeWorkerComplaintModal(event) {
      if (event && event.target && event.target.id !== 'workerComplaintModal') return;
      const modal = document.getElementById('workerComplaintModal');
      if (modal) modal.classList.remove('show');
    }
    function closeWorkerEmergencyModal(event) {
      if (event && event.target && event.target.id !== 'workerEmergencyModal') return;
      const modal = document.getElementById('workerEmergencyModal');
      if (modal) modal.classList.remove('show');
    }
    function viewWorkerComplaint(issueId) {
      const item = workerIssueStore.find(row => row.id === issueId);
      if (!item) return;
      const body = document.getElementById('workerComplaintBody');
      const imageBlock = (item.media_urls || []).length
        ? `<div class="thumbGrid">${item.media_urls.map(src => `<a href="${src}" target="_blank" rel="noopener noreferrer"><img src="${src}" alt="Complaint image" /></a>`).join('')}</div>`
        : '<p class="muted">No uploaded images for this complaint.</p>';
      body.innerHTML = `
        <div class="mono" style="margin-bottom:8px;">${item.complaint_number || '-'}</div>
        <p><strong>Issue:</strong> ${item.title || '-'}</p>
        <p><strong>Description:</strong> ${item.description || '-'}</p>
        <p><strong>Location:</strong> ${item.location || '-'}</p>
        <p><strong>Category:</strong> ${item.category || '-'}</p>
        <p><strong>Admin Status:</strong> ${item.status || '-'}</p>
        <p><strong>Assigned Worker:</strong> ${item.assigned_worker_id || '-'}</p>
        <p><strong>Worker Status:</strong> ${item.worker_status || 'Assigned'}</p>
        <p><strong>Deadline:</strong> ${item.assignment_duration_label || '-'}${item.assignment_deadline ? ' | ' + prettyWorkerDate(item.assignment_deadline) : ''}</p>
        <h4 style="margin:12px 0 8px;">Uploaded Images</h4>
        ${imageBlock}
      `;
      document.getElementById('workerComplaintModal').classList.add('show');
    }
    async function updateWorkerComplaintStatus(issueId) {
      const picker = document.getElementById('worker_status_' + issueId);
      if (!picker) return;
      const nextStatus = picker.value;
      try {
        const res = await fetch('/worker/issues/' + issueId + '/status', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: nextStatus })
        });
        const payload = await res.json().catch(() => ({}));
        if (!res.ok) {
          showWorkerFeedback(formatClientMessage(payload.detail, 'Unable to update worker status'));
          return;
        }
        const row = workerIssueStore.find(item => item.id === issueId);
        if (row) {
          row.worker_status = payload.worker_status || nextStatus;
          if (nextStatus === 'Resolved' || nextStatus === 'Rejected') {
            row.worker_resolution_requested_at = payload.worker_resolution_requested_at || new Date().toISOString();
          } else {
            row.worker_resolution_requested_at = null;
            if (row.status === 'Pending') row.status = 'In Progress';
          }
        }
        renderWorkerIssueRows();
        renderWorkerMetrics();
        persistWorkerPanelCache();
        showWorkerFeedback(formatClientMessage(payload.message, 'Worker status updated'));
      } catch (_) {
        showWorkerFeedback('Unable to update worker status');
      }
    }
    function viewWorkerEmergency(alertId) {
      const item = (window.workerEmergencyStore || []).find(row => row.id === alertId);
      if (!item) return;
      const body = document.getElementById('workerEmergencyBody');
      body.innerHTML = `
        <div class="mono" style="margin-bottom:8px;">${item.id || '-'}</div>
        <p><strong>Citizen:</strong> ${item.sender_name || '-'}</p>
        <p><strong>Citizen Contact:</strong> ${item.sender_email || '-'}${item.sender_phone ? ' | ' + item.sender_phone : ''}</p>
        <p><strong>Alert:</strong> ${item.sensor_label || '-'}</p>
        <p><strong>Location:</strong> ${item.location || '-'}</p>
        <p><strong>Reported At:</strong> ${prettyWorkerDate(item.created_at)}</p>
        <p><strong>Assigned Department:</strong> ${item.assigned_department || 'Emergency'}</p>
        <p><strong>Worker Status:</strong> ${item.worker_status || 'Assigned'}</p>
        <p><strong>Admin Status:</strong> ${item.status || '-'}</p>
        <p><strong>Sensor Value:</strong> ${item.value || '-'}</p>
        <p><strong>Emergency Details:</strong> ${item.details || '-'}</p>
        <p><strong>Public Note:</strong> ${item.note || '-'}</p>
      `;
      document.getElementById('workerEmergencyModal').classList.add('show');
    }
    async function updateWorkerEmergencyStatus(alertId) {
      const picker = document.getElementById('worker_em_status_' + alertId);
      if (!picker) return;
      const nextStatus = picker.value;
      try {
        const res = await fetch('/worker/emergency-alerts/' + alertId + '/status', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: nextStatus })
        });
        const payload = await res.json().catch(() => ({}));
        if (!res.ok) {
          showWorkerFeedback(formatClientMessage(payload.detail, 'Unable to update emergency status'));
          return;
        }
        const row = (window.workerEmergencyStore || []).find(item => item.id === alertId);
        if (row) {
          row.worker_status = payload.worker_status || nextStatus;
          row.worker_updated_at = payload.worker_updated_at || new Date().toISOString();
          row.status = payload.status || row.status;
        }
        renderWorkerEmergencyRows();
        renderWorkerMetrics();
        persistWorkerPanelCache();
        showWorkerFeedback(formatClientMessage(payload.message, 'Emergency worker status updated'));
      } catch (_) {
        showWorkerFeedback('Unable to update emergency status');
      }
    }
    async function deleteWorkerEmergency(alertId) {
      const item = (window.workerEmergencyStore || []).find(row => row.id === alertId);
      if (!item) return;
      const confirmed = confirm('Delete this emergency from the worker panel? This action cannot be undone.');
      if (!confirmed) return;
      try {
        const res = await fetch('/worker/emergency-alerts/' + alertId, { method: 'DELETE' });
        const payload = await res.json().catch(() => ({}));
        if (!res.ok) {
          showWorkerFeedback(formatClientMessage(payload.detail, 'Unable to delete emergency alert'));
          return;
        }
        window.workerEmergencyStore = (window.workerEmergencyStore || []).filter(row => row.id !== alertId);
        renderWorkerEmergencyRows();
        renderWorkerMetrics();
        persistWorkerPanelCache();
        closeWorkerEmergencyModal();
        showWorkerFeedback(formatClientMessage(payload.message, 'Emergency alert deleted'));
      } catch (_) {
        showWorkerFeedback('Unable to delete emergency alert');
      }
    }
    async function loadWorkerPanel(force = false) {
      if (workerPanelLoadInFlight) return;
      if (!force && (Date.now() < workerPanelPausedUntil || workerPanelHasInteractiveFocus())) return;
      workerPanelLoadInFlight = true;
      try {
        const res = await fetch('/worker/panel-data', { cache: 'no-store' });
        if (!res.ok) { window.location.href = '/worker'; return; }
        const data = await res.json();
        applyWorkerPanelData(data);
      } finally {
        workerPanelLoadInFlight = false;
      }
    }
    function connectWorkerPanelEvents() {
      if (!workerContext?.worker_id) return;
      if (workerPanelSocket || workerPanelEventSource) return;
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        workerPanelSocket = new WebSocket(`${protocol}//${window.location.host}/ws/worker/${encodeURIComponent(workerContext.worker_id)}`);
        workerPanelSocket.onmessage = (event) => {
          try {
            handleWorkerRealtimeEvent(JSON.parse(event.data));
          } catch (_) {
            queueWorkerRefresh(0);
          }
        };
        workerPanelSocket.onclose = () => {
          workerPanelSocket = null;
          connectWorkerPanelSSEFallback();
        };
        workerPanelSocket.onerror = () => {
          if (workerPanelSocket) workerPanelSocket.close();
        };
      } catch (_) {
        connectWorkerPanelSSEFallback();
      }
    }
    function connectWorkerPanelSSEFallback() {
      if (workerPanelEventSource) return;
      workerPanelEventSource = new EventSource('/panel/events');
      workerPanelEventSource.onmessage = (event) => {
        try {
          handleWorkerRealtimeEvent(JSON.parse(event.data));
        } catch (_) {
          queueWorkerRefresh(0);
        }
      };
      workerPanelEventSource.onerror = () => {
        if (workerPanelEventSource) {
          workerPanelEventSource.close();
          workerPanelEventSource = null;
        }
        window.setTimeout(connectWorkerPanelEvents, 1500);
      };
    }
    document.addEventListener('focusin', (event) => {
      if (event.target && event.target.tagName === 'SELECT') {
        workerPanelPausedUntil = Date.now() + 1500;
      }
    });
    document.addEventListener('focusout', (event) => {
      if (event.target && event.target.tagName === 'SELECT') {
        workerPanelPausedUntil = Date.now() + 600;
      }
    });
    hydrateWorkerPanelFromCache();
    loadWorkerPanel(true).then(() => connectWorkerPanelEvents());
    setInterval(() => loadWorkerPanel(), 45000);
  </script>
</body>
</html>
"""
    )


@app.get("/admin/panel", response_class=HTMLResponse, include_in_schema=False)
def admin_panel(_: dict = Depends(get_current_admin)):
    return HTMLResponse(
        content="""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Urban Sentinel Admin Panel</title>
  <style>
    :root { --bg:#f1f5f9; --ink:#0f172a; --card:#ffffff; --line:#dbeafe; --ok:#16a34a; --warn:#f59e0b; --bad:#dc2626; --brand:#0f766e; --space-1:8px; --space-2:16px; --space-3:24px; }
    body { margin:0; font-family:Segoe UI,Arial,sans-serif; background:linear-gradient(140deg,#e2e8f0,#ecfeff); color:var(--ink); }
    .wrap { width:min(1280px,95vw); margin:18px auto; }
    .head { display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:12px; }
    .head h1 { margin:0; font-size:1.5rem; }
    .head p { margin:4px 0 0; color:#475569; }
    .btn { text-decoration:none; border:none; border-radius:10px; padding:9px 12px; font-weight:700; cursor:pointer; }
    .toolbar { display:flex; align-items:center; gap:10px; }
    .workersBtn { background:#ccfbf1; color:#115e59; position:relative; }
    .toolbarBadge {
      min-width:1.3rem;
      height:1.3rem;
      padding:0 6px;
      border-radius:999px;
      background:#b91c1c;
      color:#fff;
      font-size:.75rem;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      margin-left:6px;
    }
    .logout { background:#fee2e2; color:#7f1d1d; }
    .cards { display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:10px; margin-bottom:12px; }
    .card { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:12px; box-shadow:0 8px 18px rgba(15,23,42,.08); }
    .card h3 { margin:0; font-size:1.45rem; }
    .card p { margin:4px 0 0; color:#475569; }
    .grid { display:grid; grid-template-columns:minmax(0,1fr); gap:12px; margin-bottom:12px; align-items:start; }
    table { width:100%; border-collapse:collapse; }
    th,td { font-size:.9rem; padding:8px; border-bottom:1px solid #e2e8f0; text-align:left; }
    th { color:#334155; }
    .pill { border-radius:999px; padding:4px 8px; font-size:.75rem; font-weight:700; display:inline-block; }
    .pending { background:#fef3c7; color:#92400e; }
    .resolved { background:#dcfce7; color:#166534; }
    .progress { background:#dbeafe; color:#1d4ed8; }
    .rejected { background:#fee2e2; color:#991b1b; }
    .danger { background:#fee2e2; color:#991b1b; }
    .assigned { background:#ede9fe; color:#6d28d9; }
    select, button { border:1px solid #cbd5e1; border-radius:8px; padding:6px 8px; background:#fff; }
    select, button { min-height:36px; }
    .actionCell { text-align:right; white-space:nowrap; }
    .actionWrap { display:inline-flex; align-items:center; gap:8px; }
    .actionLeft { display:inline-flex; align-items:center; gap:8px; }
    .iconBtn { width:34px; height:34px; display:inline-flex; align-items:center; justify-content:center; border-radius:10px; cursor:pointer; border:1px solid #fecaca; background:#fff1f2; color:#b91c1c; font-size:1rem; }
    .iconBtn:hover { background:#ffe4e6; }
    .thumbGrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(120px,1fr)); gap:10px; margin-top:10px; }
    .thumbGrid img { width:100%; height:100px; object-fit:cover; border-radius:10px; border:1px solid #cbd5e1; background:#f8fafc; }
    #complaintTable { table-layout:fixed; }
    #complaintTable th:nth-child(1), #complaintTable td:nth-child(1) { width:14%; }
    #complaintTable th:nth-child(2), #complaintTable td:nth-child(2) { width:18%; }
    #complaintTable th:nth-child(3), #complaintTable td:nth-child(3) { width:44%; }
    #complaintTable th:nth-child(4), #complaintTable td:nth-child(4) { width:24%; }
    #complaintTable th:nth-child(4) { text-align:center; }
    #complaintTable td:nth-child(4) { text-align:center; }
    #complaintTable td:nth-child(4) .actionWrap { justify-content:center; }
    .compactLocationWrap { vertical-align:top; }
    .compactLocation { font-size:.9rem; line-height:1.45; color:#334155; }
    .modal { position:fixed; inset:0; background:rgba(2,6,23,.5); display:none; align-items:center; justify-content:center; padding:16px; z-index:50; }
    .modal.show { display:flex; }
    .modalCard { width:min(760px,94vw); max-height:86vh; overflow:auto; background:#ffffff; border-radius:16px; border:1px solid #dbeafe; box-shadow:0 20px 50px rgba(2,6,23,.25); padding:14px; }
    .modalHead { display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:8px; }
    .closeBtn { background:#f1f5f9; border:1px solid #cbd5e1; }
    .users { display:grid; gap:10px; }
    .userCard { border:1px solid #dbeafe; border-radius:12px; padding:10px; background:#fff; }
    .workerGrid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
    .workerForm { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; align-items:end; }
    .workerForm input, .workerForm select { width:100%; box-sizing:border-box; padding:10px; }
    .workerForm label { display:block; font-weight:700; font-size:.9rem; margin-bottom:6px; }
    .stack { display:grid; gap:10px; }
    .helper { color:#475569; font-size:.86rem; margin:0; }
    .muted { color:#64748b; font-size:.86rem; }
    details { border:1px solid #e2e8f0; border-radius:10px; padding:8px; background:#f8fafc; margin-top:8px; }
    summary { cursor:pointer; font-weight:700; }
    .mono { font-family:Consolas,monospace; font-size:.83rem; }
    .adminSectionHead { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin-bottom:12px; flex-wrap:wrap; }
    .adminSectionHead p { margin:0; color:#64748b; font-size:.86rem; }
    .sectionHeaderActions { display:flex; align-items:center; gap:12px; margin-left:auto; }
    .tableWrap { overflow:hidden; }
    .adminDataTable { table-layout:fixed; }
    .adminDataTable col:nth-child(1) { width:12%; }
    .adminDataTable col:nth-child(2) { width:18%; }
    .adminDataTable col:nth-child(3) { width:30%; }
    .adminDataTable col:nth-child(4) { width:14%; }
    .adminDataTable col:nth-child(5) { width:12%; }
    .adminDataTable col:nth-child(6) { width:14%; }
    .adminDataTable td { vertical-align:top; }
    .tableId { font-weight:800; color:#0f172a; }
    .tableTitle { font-weight:700; color:#0f172a; }
    .tableLocation { color:#334155; line-height:1.5; word-break:break-word; }
    .statusStack, .workerStack { display:grid; gap:6px; justify-items:start; }
    .workerStack strong { font-size:.84rem; color:#0f172a; }
    .tableActions { display:flex; flex-wrap:wrap; align-items:center; justify-content:flex-end; gap:8px; }
    .tableActions select { min-width:132px; }
    .buttonPrimary { background:#ecfeff; color:#115e59; border-color:#99f6e4; font-weight:700; }
    .buttonSecondary { background:#eff6ff; color:#1d4ed8; border-color:#bfdbfe; font-weight:700; }
    .buttonSuccess { background:#dcfce7; color:#166534; border-color:#bbf7d0; font-weight:700; }
    .buttonWarning { background:#fef3c7; color:#92400e; border-color:#fde68a; font-weight:700; }
    .buttonMuted { background:#f8fafc; color:#475569; border-color:#cbd5e1; font-weight:700; }
    .buttonDisabled, button:disabled { opacity:.6; cursor:not-allowed; }
    .emergencyButton {
      position:relative;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      gap:8px;
      min-height:40px;
      padding:10px 16px;
      border-radius:12px;
      border:1px solid #b91c1c;
      background:linear-gradient(180deg,#dc2626,#b91c1c);
      color:#fff;
      box-shadow:0 10px 22px rgba(185,28,28,.22);
      transition:background .2s ease, transform .2s ease, box-shadow .2s ease;
    }
    .emergencyButton:hover { background:linear-gradient(180deg,#b91c1c,#991b1b); box-shadow:0 14px 26px rgba(153,27,27,.26); transform:translateY(-1px); }
    .emergencyButton:focus-visible { outline:3px solid rgba(239,68,68,.28); outline-offset:2px; }
    .emergencyButton.has-alert { animation:emergencyPulse 2s ease-in-out infinite; }
    .emergencyDot {
      position:absolute;
      top:6px;
      right:6px;
      width:10px;
      height:10px;
      border-radius:999px;
      background:#fecaca;
      box-shadow:0 0 0 0 rgba(254,202,202,.85);
      opacity:0;
      transform:scale(.8);
      transition:opacity .18s ease, transform .18s ease;
    }
    .emergencyButton.has-alert .emergencyDot { opacity:1; transform:scale(1); animation:dotGlow 1.8s ease-in-out infinite; }
    .alertTable td { vertical-align:top; }
    .alertActionStack { display:grid; gap:8px; justify-items:end; }
    .alertActionRow { display:flex; flex-wrap:wrap; justify-content:flex-end; gap:8px; }
    .modalOpen { overflow:hidden; }
    .modalPanel { width:min(980px,94vw); max-height:min(86vh,48rem); animation:modalFade .22s ease; }
    .modalBodyScroll { overflow:auto; max-height:calc(86vh - 4.5rem); padding-right:2px; }
    .emergencyModalList { display:grid; gap:12px; }
    .emergencyCard { border:1px solid #e2e8f0; border-radius:14px; background:#fff; padding:16px; display:grid; gap:12px; }
    .emergencyCardHeader { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap; }
    .emergencyMeta { display:grid; gap:4px; }
    .emergencyMeta h4 { margin:0; font-size:1rem; }
    .emergencyMeta p { margin:0; color:#475569; font-size:.9rem; }
    .emergencyDataGrid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px 16px; }
    .emergencyField { display:grid; gap:4px; min-width:0; }
    .emergencyFieldLabel { font-size:.78rem; font-weight:700; letter-spacing:.02em; color:#64748b; text-transform:uppercase; }
    .emergencyFieldValue { color:#0f172a; line-height:1.5; word-break:break-word; }
    .emergencyModalActions { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
    .emergencyActionGroup { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
    .loadingSpinner {
      width:14px;
      height:14px;
      border:2px solid rgba(255,255,255,.45);
      border-top-color:#fff;
      border-radius:999px;
      display:inline-block;
      animation:spin .8s linear infinite;
    }
    .hidden { display:none !important; }
    .workerPreview { color:#0f766e; font-weight:700; }
    .feedbackToast { position:fixed; right:16px; bottom:16px; padding:12px 14px; border-radius:12px; background:#0f172a; color:#fff; box-shadow:0 16px 36px rgba(15,23,42,.22); display:none; z-index:90; }
    .feedbackToast.show { display:block; }
    @keyframes emergencyPulse { 0%,100% { box-shadow:0 10px 22px rgba(185,28,28,.22); } 50% { box-shadow:0 14px 32px rgba(185,28,28,.34); } }
    @keyframes dotGlow { 0%,100% { box-shadow:0 0 0 0 rgba(254,202,202,.85); } 70% { box-shadow:0 0 0 10px rgba(254,202,202,0); } }
    @keyframes modalFade { from { opacity:0; transform:translateY(12px) scale(.98); } to { opacity:1; transform:translateY(0) scale(1); } }
    @keyframes spin { to { transform:rotate(360deg); } }
    @media (max-width: 980px) { .cards { grid-template-columns:1fr 1fr; } .workerGrid,.workerForm,.emergencyDataGrid { grid-template-columns:1fr; } .adminDataTable col { width:auto !important; } .tableActions,.alertActionRow,.alertActionStack { justify-content:flex-start; } .sectionHeaderActions { width:100%; justify-content:flex-start; margin-left:0; } }
    @media (max-width: 720px) { .cards { grid-template-columns:1fr; } .adminSectionHead { align-items:flex-start; flex-direction:column; } .adminDataTable, .adminDataTable thead, .adminDataTable tbody, .adminDataTable tr, .adminDataTable th, .adminDataTable td { display:block; width:100%; } .adminDataTable thead { display:none; } .adminDataTable tr { border-bottom:1px solid #e2e8f0; padding:12px 0; } .adminDataTable td { border:none; padding:4px 0; } .tableActions select, .tableActions button, .emergencyActionGroup button, .emergencyActionGroup select { width:100%; } .actionWrap, .actionLeft, .emergencyModalActions, .emergencyActionGroup { flex-wrap:wrap; } .modalPanel { width:min(100%,94vw); } }
  </style>
</head>
<body>
  <main class="wrap">
    <header class="head">
      <div>
        <h1>Urban Sentinel Admin Panel</h1>
        <p>Secure backend operations dashboard</p>
      </div>
      <div class="toolbar">
        <button class="btn workersBtn" type="button" onclick="openWorkerModal()">Workers <span id="workerResetBadge" class="toolbarBadge hidden">0</span></button>
        <a class="btn logout" href="/admin/logout">Logout</a>
      </div>
    </header>
    <section class="cards">
      <article class="card"><h3 id="total">-</h3><p>Total Complaints</p></article>
      <article class="card"><h3 id="pending">-</h3><p>Pending</p></article>
      <article class="card"><h3 id="progress">-</h3><p>In Progress</p></article>
      <article class="card"><h3 id="resolved">-</h3><p>Resolved</p></article>
      <article class="card"><h3 id="emTotal">-</h3><p>Emergency Alerts</p></article>
      <article class="card"><h3 id="emResolved">-</h3><p>Emergency Resolved</p></article>
    </section>
    <section class="grid">
      <article class="card">
        <div class="adminSectionHead">
          <div>
            <h3 style="font-size:1.05rem;margin:0 0 8px;">Recent Complaints</h3>
            <p>Structured complaint rows with aligned status, worker progress, and admin actions.</p>
          </div>
          <div class="sectionHeaderActions">
            <button id="emergencyPanelButton" class="emergencyButton" type="button" onclick="openEmergencyModal()" aria-haspopup="dialog" aria-controls="emergencyModal" aria-expanded="false">
              <span>🔴 Emergency</span>
              <span id="emergencyIndicator" class="emergencyDot hidden" aria-hidden="true"></span>
            </button>
          </div>
        </div>
        <div class="tableWrap">
          <table class="adminDataTable">
            <colgroup><col /><col /><col /><col /><col /><col /></colgroup>
            <thead><tr><th>ID</th><th>Title</th><th>Location</th><th>Status</th><th>Worker</th><th>Action</th></tr></thead>
            <tbody id="issueRows"></tbody>
          </table>
        </div>
      </article>
    </section>
    <section class="card" style="margin-bottom:10px;">
      <h3 style="font-size:1.05rem;margin:0 0 8px;">Reported Complaints</h3>
      <table id="complaintTable">
        <thead><tr><th>User</th><th>Issue</th><th>Location</th><th>Action</th></tr></thead>
        <tbody id="complaintRows"></tbody>
      </table>
    </section>
    <section class="card">
      <details>
        <summary style="font-size:1.05rem;">Registered Users</summary>
        <p class="muted" style="margin-top:10px;">Passwords are not shown for security. Complaints and emergency history are listed per account.</p>
        <div id="userCards" class="users" style="margin-top:10px;"></div>
      </details>
    </section>
    <section class="card" style="margin-top:10px;">
      <h3 style="font-size:1.05rem;margin:0 0 8px;">Worker Password Reset Requests</h3>
      <p class="muted">Department worker password reset requests appear here and inside the Workers panel.</p>
      <div id="workerResetRequestsInline" class="users"></div>
    </section>
    <section class="card" style="margin-top:10px;">
      <h3 style="font-size:1.05rem;margin:0 0 8px;">Worker Resolution Requests</h3>
      <p class="muted">When a department worker marks a complaint as resolved, it appears here so the admin can verify and update the official complaint status.</p>
      <div id="workerResolutionRequests" class="users"></div>
    </section>
  </main>
  <div id="complaintModal" class="modal" onclick="closeComplaintModal(event)">
    <div class="modalCard" onclick="event.stopPropagation()">
      <div class="modalHead">
        <h3 style="margin:0;font-size:1.05rem;">Complaint Details</h3>
        <button class="btn closeBtn" onclick="closeComplaintModal()">Close</button>
      </div>
      <div id="complaintModalBody"></div>
    </div>
  </div>
  <div id="assignModal" class="modal" onclick="closeAssignModal(event)">
    <div class="modalCard" onclick="event.stopPropagation()">
      <div class="modalHead">
        <h3 style="margin:0;font-size:1.05rem;">Assign Complaint</h3>
        <button class="btn closeBtn" onclick="closeAssignModal()">Close</button>
      </div>
      <div class="stack">
        <p id="assignComplaintLabel" class="helper" style="margin:0;"></p>
        <div>
          <label style="display:block;font-weight:700;margin-bottom:6px;">Department</label>
          <select id="assignDepartment"></select>
        </div>
        <div>
          <label style="display:block;font-weight:700;margin-bottom:6px;">Workers in this department</label>
          <select id="assignWorker"></select>
          <p id="assignWorkerHelper" class="helper" style="margin:6px 0 0;">Select the exact worker who should receive this complaint.</p>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
          <div>
            <label style="display:block;font-weight:700;margin-bottom:6px;">Duration Value</label>
            <input id="assignDurationValue" type="number" min="1" max="365" value="1" />
          </div>
          <div>
            <label style="display:block;font-weight:700;margin-bottom:6px;">Duration Unit</label>
            <select id="assignDurationUnit">
              <option value="days">Days</option>
              <option value="months">Months</option>
            </select>
          </div>
        </div>
        <button id="assignSubmitButton" class="btn workersBtn" type="button" onclick="submitAssignment()">Assign to Selected Worker</button>
      </div>
    </div>
  </div>
  <div id="workerModal" class="modal" onclick="closeWorkerModal(event)">
    <div class="modalCard" style="width:min(920px,96vw);" onclick="event.stopPropagation()">
      <div class="modalHead">
        <h3 style="margin:0;font-size:1.05rem;">Worker Management</h3>
        <button class="btn closeBtn" onclick="closeWorkerModal()">Close</button>
      </div>
      <p class="helper" style="margin-bottom:12px;">Select the department, set the password, and the system will auto-generate the worker ID for that department.</p>
      <div class="workerGrid">
        <article class="card">
          <h4 style="margin:0 0 10px;">Create Worker</h4>
          <form class="workerForm" onsubmit="createWorker(event)">
            <div>
              <label>Department</label>
              <select id="workerDepartment"></select>
            </div>
            <div>
              <label>Create Password</label>
              <input id="workerPassword" type="password" placeholder="Minimum 6 characters" required />
            </div>
            <div>
              <label>Worker ID</label>
              <input id="workerIdPreview" class="workerPreview" value="Auto-generated" disabled />
            </div>
            <button class="btn workersBtn" style="grid-column:1 / -1;" type="submit">Create Worker</button>
          </form>
          <p id="workerCreateMessage" class="helper" style="margin-top:10px;"></p>
        </article>
        <article class="card">
          <h4 style="margin:0 0 10px;">Password Reset Requests</h4>
          <div id="workerResetRequests" class="stack"></div>
        </article>
      </div>
      <article class="card" style="margin-top:12px;">
        <h4 style="margin:0 0 10px;">Department Workers</h4>
        <div id="workerList" class="stack"></div>
      </article>
    </div>
  </div>
  <div id="emergencyModal" class="modal" onclick="closeEmergencyModal(event)" aria-hidden="true">
    <div class="modalCard modalPanel" role="dialog" aria-modal="true" aria-labelledby="emergencyModalTitle" onclick="event.stopPropagation()">
      <div class="modalHead">
        <div>
          <h3 id="emergencyModalTitle" style="margin:0;font-size:1.05rem;">Emergency Alerts</h3>
          <p class="helper">Urgent public alerts with direct assignment into the Emergency department.</p>
        </div>
        <button class="btn closeBtn" type="button" onclick="closeEmergencyModal()">Close</button>
      </div>
      <div class="modalBodyScroll">
        <div id="emergencyList" class="emergencyModalList"></div>
      </div>
    </div>
  </div>
  <div id="feedbackToast" class="feedbackToast" role="status" aria-live="polite"></div>
  <script>
    function statusPill(status) {
      const key = (status || '').toLowerCase();
      if (key === 'resolved') return '<span class="pill resolved">Resolved</span>';
      if (key === 'in progress') return '<span class="pill progress">In Progress</span>';
      if (key === 'rejected') return '<span class="pill rejected">Rejected</span>';
      if (key.includes('assigned to emergency')) return '<span class="pill assigned">Assigned to Emergency</span>';
      return '<span class="pill pending">' + (status || 'Pending') + '</span>';
    }
    let adminPanelLoadInFlight = false;
    let adminPanelEventSource = null;
    let adminPanelSocket = null;
    const ADMIN_PANEL_CACHE_KEY = 'urbanSentinelAdminPanelCacheV1';
    const ADMIN_PANEL_REFRESH_EVENT_TYPES = new Set([
      'emergency-alert-created',
      'emergency-status-updated',
      'emergency-deleted',
      'emergency-assigned',
      'worker-reset-request-created',
      'worker-reset-request-deleted',
      'worker-created'
    ]);
    let recentIssueStore = [];
    let adminUserStore = [];
    let adminStats = {
      total_issues: 0,
      pending: 0,
      in_progress: 0,
      resolved: 0,
      emergency_total: 0,
      emergency_resolved: 0
    };
    function cloneData(value) {
      return JSON.parse(JSON.stringify(value ?? null));
    }
    function upsertById(list, incoming) {
      if (!incoming || incoming.id === undefined || incoming.id === null) return list || [];
      const next = Array.isArray(list) ? [...list] : [];
      const index = next.findIndex(item => item.id === incoming.id);
      if (index >= 0) {
        next[index] = { ...next[index], ...incoming };
      } else {
        next.unshift(incoming);
      }
      return next;
    }
    function removeById(list, id) {
      return (list || []).filter(item => item.id !== id);
    }
    function trimByLimit(list, limit) {
      return (list || []).slice(0, limit);
    }
    function persistAdminPanelCache() {
      try {
        sessionStorage.setItem(ADMIN_PANEL_CACHE_KEY, JSON.stringify({
          stats: adminStats,
          recent_issues: recentIssueStore,
          reported_complaints: complaintStore,
          recent_alerts: emergencyAlertStore,
          users: adminUserStore,
          workers: workerStore,
          worker_reset_requests: workerResetStore,
          worker_resolution_requests: workerResolutionStore,
          departments: departmentStore,
          department_configs: departmentConfigStore
        }));
      } catch (_) {}
    }
    function renderComplaintTable() {
      document.getElementById('complaintRows').innerHTML = complaintStore.map((item, idx) =>
        `<tr>
          <td class="singleLine" title="${esc(item.user_name || '-')}">${esc(item.user_name || '-')}</td>
          <td class="singleLine" title="${esc(item.title || '-')}">${esc(item.title || '-')}</td>
          <td class="compactLocationWrap"><div class="compactLocation" title="${esc(item.location || '-')}">${esc(item.location || '-')}</div></td>
          <td class="actionCell complaintAction">
            <div class="actionWrap">
              <span class="actionLeft"><button onclick="viewComplaint(${idx})">View Complaint</button><button onclick="openAssignModal(${item.id})">Assign</button></span>
              <button class="iconBtn" title="Delete complaint" onclick="deleteComplaint(${item.id})">&#128465;</button>
            </div>
          </td>
        </tr>`
      ).join('') || '<tr><td colspan="4">No complaints reported</td></tr>';
    }
    function renderUserCards() {
      document.getElementById('userCards').innerHTML = adminUserStore.map(user => `
        <article class="userCard">
          <div><strong>${user.full_name || 'Unknown User'}</strong> <span class="mono">#${user.id}</span></div>
          <div class="muted">${user.email || 'No email'} | ${user.phone || 'No phone'}</div>
          <div class="muted">Complaints: ${(user.complaints || []).length} | Emergencies: ${(user.emergency_alerts || []).length}</div>
          <details>
            <summary>View complaints</summary>
            ${(user.complaints || []).length ? user.complaints.map(c =>
              `<div class="mono">${c.complaint_number} | ${c.status} | ${c.location || '-'} | ${c.title || '-'}</div>`
            ).join('') : '<div class="muted">No complaints submitted</div>'}
          </details>
          <details>
            <summary>View emergencies</summary>
            ${(user.emergency_alerts || []).length ? user.emergency_alerts.map(a =>
              `<div class="mono">${a.created_at || ''} | ${a.sensor_label || '-'} | ${a.severity || '-'} | ${a.note || '-'}</div>`
            ).join('') : '<div class="muted">No emergency alerts</div>'}
          </details>
        </article>
      `).join('') || '<p class="muted">No users registered yet.</p>';
    }
    function renderWorkerList() {
      document.getElementById('workerList').innerHTML = workerStore.map(worker => `
        <article class="userCard">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;">
            <strong>${esc(worker.worker_id)}</strong>
          </div>
          <div class="muted">${esc(worker.department)} Department</div>
          <div class="muted">Created: ${esc(prettyDate(worker.created_at))} | Last login: ${esc(prettyDate(worker.last_login_at))}</div>
          <div class="muted">Department login page: <a href="/worker/login/${esc(worker.department_slug)}" target="_blank" rel="noopener noreferrer">/worker/login/${esc(worker.department_slug)}</a></div>
        </article>
      `).join('') || '<p class="muted">No workers created yet.</p>';
    }
    function renderWorkerResolutionRequests() {
      document.getElementById('workerResolutionRequests').innerHTML = workerResolutionStore.map(item => `
        <article class="userCard">
          <div><strong>${esc(item.complaint_number)}</strong> <span class="muted">${esc(item.department || '-')}</span></div>
          <div class="muted">${esc(item.title || '-')}</div>
          <div class="muted">Worker marked resolved on: ${esc(prettyDate(item.requested_at))}</div>
          <div class="muted">Update the official complaint status from the complaints table after verification.</div>
        </article>
      `).join('') || '<p class="muted">No worker resolution notifications yet.</p>';
    }
    function renderAdminStats() {
      document.getElementById('total').textContent = adminStats.total_issues ?? 0;
      document.getElementById('pending').textContent = adminStats.pending ?? 0;
      document.getElementById('progress').textContent = adminStats.in_progress ?? 0;
      document.getElementById('resolved').textContent = adminStats.resolved ?? 0;
      document.getElementById('emTotal').textContent = adminStats.emergency_total ?? 0;
      document.getElementById('emResolved').textContent = adminStats.emergency_resolved ?? 0;
    }
    function recomputeAdminStats() {
      adminStats = {
        ...adminStats,
        total_issues: complaintStore.length,
        pending: complaintStore.filter(item => item.status === 'Pending').length,
        in_progress: complaintStore.filter(item => item.status === 'In Progress').length,
        resolved: complaintStore.filter(item => item.status === 'Resolved').length
      };
    }
    function renderAdminDashboard() {
      renderAdminStats();
      renderIssueRows(recentIssueStore);
      renderEmergencyList();
      renderComplaintTable();
      renderUserCards();
      renderWorkerList();
      renderWorkerResetRequests('workerResetRequests');
      renderWorkerResetRequests('workerResetRequestsInline');
      updateWorkerResetBadge();
      renderWorkerResolutionRequests();
    }
    function applyAdminPanelData(data, options = {}) {
      emergencyAlertStore = data.recent_alerts || [];
      complaintStore = data.reported_complaints || [];
      recentIssueStore = data.recent_issues || [];
      workerStore = data.workers || [];
      workerResetStore = data.worker_reset_requests || [];
      workerResolutionStore = data.worker_resolution_requests || [];
      departmentStore = data.departments || [];
      departmentConfigStore = data.department_configs || [];
      adminUserStore = data.users || [];
      adminStats = data.stats || adminStats;
      renderDepartmentOptions('workerDepartment');
      const workerDepartment = document.getElementById('workerDepartment');
      if (workerDepartment && !workerDepartment.dataset.bound) {
        workerDepartment.addEventListener('change', updateWorkerIdPreview);
        workerDepartment.dataset.bound = 'true';
      }
      const assignDepartment = document.getElementById('assignDepartment');
      if (assignDepartment && !assignDepartment.dataset.bound) {
        assignDepartment.addEventListener('change', renderAssignmentWorkerOptions);
        assignDepartment.dataset.bound = 'true';
      }
      updateWorkerIdPreview();
      renderAssignmentWorkerOptions();
      renderAdminDashboard();
      if (options.persist !== false) {
        persistAdminPanelCache();
      }
    }
    function hydrateAdminPanelFromCache() {
      try {
        const raw = sessionStorage.getItem(ADMIN_PANEL_CACHE_KEY);
        if (!raw) return false;
        const cached = JSON.parse(raw);
        if (!cached || typeof cached !== 'object') return false;
        applyAdminPanelData(cached, { persist: false });
        return true;
      } catch (_) {
        return false;
      }
    }
    function syncIssueAcrossAdminStores(issueId, patch) {
      complaintStore = complaintStore.map(item => item.id === issueId ? { ...item, ...patch } : item);
      recentIssueStore = recentIssueStore.map(item => item.id === issueId ? { ...item, ...patch } : item);
      const complaint = complaintStore.find(item => item.id === issueId);
      if (complaint) {
        adminUserStore = adminUserStore.map(user => ({
          ...user,
          complaints: (user.complaints || []).map(entry => entry.id === issueId ? {
            ...entry,
            complaint_number: complaint.complaint_number,
            title: complaint.title,
            status: complaint.status,
            location: complaint.location,
            created_at: complaint.created_at
          } : entry)
        }));
      }
      workerResolutionStore = workerResolutionStore.filter(item => item.id !== issueId);
      if ((patch.worker_status || complaint?.worker_status) === 'Resolved' && (patch.worker_resolution_requested_at || complaint?.worker_resolution_requested_at)) {
        const source = complaint || recentIssueStore.find(item => item.id === issueId);
        if (source) {
          workerResolutionStore = upsertById(workerResolutionStore, {
            id: source.id,
            complaint_number: source.complaint_number,
            title: source.title,
            department: source.assigned_department,
            worker_status: source.worker_status || patch.worker_status || 'Assigned',
            requested_at: patch.worker_resolution_requested_at || source.worker_resolution_requested_at
          });
        }
      }
      recomputeAdminStats();
      renderAdminDashboard();
      persistAdminPanelCache();
    }
    function handleAdminRealtimeEvent(event) {
      if (!event || !event.type || event.type === 'keep-alive') return;
      if (event.type === 'issue-created') {
        if (event.payload?.issue) {
          complaintStore = trimByLimit(upsertById(complaintStore, event.payload.issue), 50);
        }
        if (event.payload?.recent_issue) {
          recentIssueStore = trimByLimit(upsertById(recentIssueStore, event.payload.recent_issue), 12);
        }
        recomputeAdminStats();
        renderAdminDashboard();
        persistAdminPanelCache();
        return;
      }
      if (event.type === 'issue-assigned' || event.type === 'issue-status-updated' || event.type === 'worker-issue-status-updated') {
        const recentIssue = event.payload?.recent_issue || {};
        syncIssueAcrossAdminStores(event.payload?.issue_id, {
          ...recentIssue,
          status: event.payload?.status ?? recentIssue.status,
          worker_status: event.payload?.worker_status ?? recentIssue.worker_status,
          assigned_department: event.payload?.assigned_department ?? recentIssue.assigned_department,
          assigned_worker_id: event.payload?.assigned_worker_id ?? recentIssue.assigned_worker_id,
          assignment_deadline: event.payload?.assignment_deadline ?? recentIssue.assignment_deadline,
          assignment_duration_label: event.payload?.assignment_duration_label ?? recentIssue.assignment_duration_label,
          worker_resolution_requested_at: event.payload?.worker_resolution_requested_at ?? recentIssue.worker_resolution_requested_at,
          worker_status_message: (
            (event.payload?.worker_status || recentIssue.worker_status) && ['In Progress', 'Resolved', 'Rejected'].includes(event.payload?.worker_status || recentIssue.worker_status)
          ) ? 'Worker:' : ''
        });
        if (event.type === 'issue-assigned' && event.payload?.issue) {
          recentIssueStore = trimByLimit(upsertById(recentIssueStore, event.payload.recent_issue || event.payload.issue), 12);
          complaintStore = trimByLimit(upsertById(complaintStore, {
            ...event.payload.issue,
            user_name: complaintStore.find(item => item.id === event.payload.issue.id)?.user_name || event.payload.issue.user_name || 'Citizen'
          }), 50);
          recomputeAdminStats();
          renderAdminDashboard();
          persistAdminPanelCache();
        }
        return;
      }
      if (event.type === 'issue-hidden-from-admin') {
        const issueId = event.payload?.issue_id;
        complaintStore = removeById(complaintStore, issueId);
        recentIssueStore = removeById(recentIssueStore, issueId);
        workerResolutionStore = removeById(workerResolutionStore, issueId);
        adminUserStore = adminUserStore.map(user => ({
          ...user,
          complaints: removeById(user.complaints || [], issueId)
        }));
        recomputeAdminStats();
        renderAdminDashboard();
        persistAdminPanelCache();
        return;
      }
      if (ADMIN_PANEL_REFRESH_EVENT_TYPES.has(event.type)) {
        queueAdminRefresh(0);
      }
    }
    async function updateIssueStatus(issueId, nextStatus) {
      const formData = new FormData();
      formData.append('status', nextStatus);
      const res = await fetch('/admin/issues/' + issueId, { method: 'PUT', body: formData });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Status not been updated');
        return;
      }
      const payload = await res.json();
      syncIssueAcrossAdminStores(issueId, { status: payload.new_status || nextStatus });
      if (payload.mail_sent === false) {
        showFeedback('Status updated, but email failed: ' + (payload.mail_status || 'unknown'), 'warning');
      } else if (payload.mail_sent === true) {
        showFeedback(payload.mail_status || 'Status updated and user notification queued.');
      } else {
        showFeedback(payload.message || 'Status updated successfully.');
      }
    }
    let emergencyAlertStore = [];
    let complaintStore = [];
    let workerStore = [];
    let workerResetStore = [];
    let workerResolutionStore = [];
    let departmentStore = [];
    let departmentConfigStore = [];
    let currentAssignmentIssueId = null;
    let expandedEmergencyId = null;
    const assigningEmergencyIds = new Set();
    let adminPanelRefreshTimer = null;
    let isAdminEmergencyModalOpen = false;
    function queueAdminRefresh(delay = 300) {
      if (adminPanelRefreshTimer) window.clearTimeout(adminPanelRefreshTimer);
      adminPanelRefreshTimer = window.setTimeout(() => {
        adminPanelRefreshTimer = null;
        loadPanel();
      }, delay);
    }
    function esc(value) {
      return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }
    function prettyDate(value) {
      if (!value) return '-';
      try {
        const normalized = typeof value === 'string' && !/[zZ]|[+-]\\d{2}:\\d{2}$/.test(value)
          ? `${value}Z`
          : value;
        return new Date(normalized).toLocaleString();
      } catch (_) { return value; }
    }
    function requiresEmergencyAttention(item) {
      const status = String(item?.status || '').trim().toLowerCase();
      const assignedDepartment = String(item?.assigned_department || '').trim().toLowerCase();
      const unresolved = status !== 'resolved' && status !== 'rejected';
      return unresolved && (!assignedDepartment || status === 'open' || status === 'in progress' || status === 'awaiting admin closure');
    }
    function setBodyScrollLock(locked) {
      document.body.classList.toggle('modalOpen', !!locked);
    }
    function openEmergencyModal() {
      const modal = document.getElementById('emergencyModal');
      const trigger = document.getElementById('emergencyPanelButton');
      if (!modal) return;
      renderEmergencyList();
      modal.classList.add('show');
      modal.setAttribute('aria-hidden', 'false');
      isAdminEmergencyModalOpen = true;
      if (trigger) trigger.setAttribute('aria-expanded', 'true');
      setBodyScrollLock(true);
    }
    function closeEmergencyModal(event) {
      if (event && event.target && event.target.id !== 'emergencyModal') return;
      const modal = document.getElementById('emergencyModal');
      const trigger = document.getElementById('emergencyPanelButton');
      if (!modal) return;
      modal.classList.remove('show');
      modal.setAttribute('aria-hidden', 'true');
      isAdminEmergencyModalOpen = false;
      if (trigger) trigger.setAttribute('aria-expanded', 'false');
      setBodyScrollLock(false);
      queueAdminRefresh(50);
    }
    function updateEmergencyIndicator() {
      const trigger = document.getElementById('emergencyPanelButton');
      const indicator = document.getElementById('emergencyIndicator');
      const hasAttention = (emergencyAlertStore || []).some(requiresEmergencyAttention);
      if (trigger) {
        trigger.classList.toggle('has-alert', hasAttention);
        trigger.setAttribute('aria-label', hasAttention ? 'Emergency alerts require attention' : 'Emergency alerts');
      }
      if (indicator) {
        indicator.classList.toggle('hidden', !hasAttention);
      }
    }
    function showFeedback(message, kind = 'success') {
      const toast = document.getElementById('feedbackToast');
      if (!toast) return;
      toast.textContent = message || '';
      toast.classList.remove('show');
      toast.dataset.kind = kind;
      if (!message) return;
      window.clearTimeout(showFeedback._timer);
      requestAnimationFrame(() => toast.classList.add('show'));
      showFeedback._timer = window.setTimeout(() => {
        toast.classList.remove('show');
      }, 2600);
    }
    function renderDepartmentOptions(targetId) {
      const target = document.getElementById(targetId);
      if (!target) return;
      target.innerHTML = (departmentStore || []).map(item => `<option value="${esc(item)}">${esc(item)}</option>`).join('');
    }
    function getWorkersForDepartment(department) {
      const selected = String(department || '').trim().toLowerCase();
      return (workerStore || []).filter(worker =>
        worker.is_active !== false && String(worker.department || '').trim().toLowerCase() === selected
      );
    }
    function renderAssignmentWorkerOptions() {
      const departmentField = document.getElementById('assignDepartment');
      const workerField = document.getElementById('assignWorker');
      const helper = document.getElementById('assignWorkerHelper');
      const assignButton = document.getElementById('assignSubmitButton');
      if (!departmentField || !workerField) return;
      const departmentWorkers = getWorkersForDepartment(departmentField.value);
      workerField.innerHTML = departmentWorkers.length
        ? departmentWorkers.map(worker => `<option value="${esc(worker.worker_id)}">${esc(worker.worker_id)} - ${esc(worker.department)} Department</option>`).join('')
        : '<option value="">No registered worker available</option>';
      workerField.disabled = departmentWorkers.length === 0;
      if (assignButton) assignButton.disabled = departmentWorkers.length === 0;
      if (helper) {
        helper.textContent = departmentWorkers.length
          ? `${departmentWorkers.length} registered worker${departmentWorkers.length === 1 ? '' : 's'} available. New workers appear here after creation.`
          : 'Create a worker for this department before assigning this complaint.';
      }
    }
    function renderWorkerResetRequests(targetId) {
      const target = document.getElementById(targetId);
      if (!target) return;
      target.innerHTML = workerResetStore.map(item => `
        <article class="userCard">
          <div><strong>${esc(item.worker_id)}</strong> <span class="muted">${esc(item.department)}</span></div>
          <div class="muted">Requested: ${esc(prettyDate(item.requested_at))} | Status: ${esc(item.status)}</div>
          <div class="actionLeft">
            <button onclick="adminResetWorkerPassword(${item.worker_db_id})">Set New Password</button>
            <button class="iconBtn" title="Delete password reset request" onclick="deleteWorkerResetRequest(${item.id})">&#128465;</button>
          </div>
        </article>
      `).join('') || '<p class="muted">No worker password reset requests.</p>';
    }
    function updateWorkerResetBadge() {
      const badge = document.getElementById('workerResetBadge');
      if (!badge) return;
      const pendingCount = (workerResetStore || []).filter(item => String(item.status || '').toLowerCase() === 'pending').length;
      badge.textContent = String(pendingCount);
      badge.classList.toggle('hidden', pendingCount === 0);
    }
    function updateWorkerIdPreview() {
      const departmentField = document.getElementById('workerDepartment');
      const previewField = document.getElementById('workerIdPreview');
      if (!departmentField || !previewField) return;
      const selectedDepartment = departmentField.value;
      const config = (departmentConfigStore || []).find(item => item.name === selectedDepartment);
      previewField.value = config?.next_worker_id || 'Auto-generated';
    }
    function openWorkerModal() {
      renderDepartmentOptions('workerDepartment');
      updateWorkerIdPreview();
      const modal = document.getElementById('workerModal');
      if (modal) modal.classList.add('show');
    }
    function closeWorkerModal(event) {
      if (event && event.target && event.target.id !== 'workerModal') return;
      const modal = document.getElementById('workerModal');
      if (modal) modal.classList.remove('show');
    }
    async function createWorker(event) {
      event.preventDefault();
      const message = document.getElementById('workerCreateMessage');
      const payload = {
        department: document.getElementById('workerDepartment').value,
        password: document.getElementById('workerPassword').value
      };
      message.textContent = '';
      const res = await fetch('/admin/workers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        message.textContent = data.detail || 'Unable to create worker';
        showFeedback(message.textContent, 'error');
        return;
      }
      message.textContent = (data.message || 'Worker created successfully') + ' | Worker ID: ' + (data.worker?.worker_id || '-');
      document.getElementById('workerPassword').value = '';
      showFeedback('Worker created successfully for ' + payload.department + '.');
      updateWorkerIdPreview();
      loadPanel();
    }
    async function adminResetWorkerPassword(workerDbId) {
      const nextPassword = prompt('Enter the new password for this worker:');
      if (!nextPassword) return;
      const res = await fetch('/admin/workers/' + workerDbId + '/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_password: nextPassword })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        alert(data.detail || 'Unable to update worker password');
        return;
      }
      alert(data.message || 'Worker password updated');
      loadPanel();
    }
    async function deleteWorkerResetRequest(requestId) {
      if (!requestId) return;
      const confirmed = confirm('Delete this password reset request?');
      if (!confirmed) return;
      const res = await fetch('/admin/worker-reset-requests/' + requestId, { method: 'DELETE' });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        alert(data.detail || 'Unable to delete password reset request');
        return;
      }
      loadPanel();
    }
    function openAssignModal(issueId) {
      const issue = complaintStore.find(item => item.id === issueId);
      currentAssignmentIssueId = issueId;
      renderDepartmentOptions('assignDepartment');
      const departmentField = document.getElementById('assignDepartment');
      if (departmentField && issue?.assigned_department) {
        departmentField.value = issue.assigned_department;
      }
      renderAssignmentWorkerOptions();
      document.getElementById('assignComplaintLabel').textContent = issue
        ? `${issue.complaint_number || '-'} | ${issue.title || '-'}`
        : 'Assign selected complaint';
      document.getElementById('assignDurationValue').value = 1;
      document.getElementById('assignDurationUnit').value = 'days';
      document.getElementById('assignModal').classList.add('show');
    }
    function closeAssignModal(event) {
      if (event && event.target && event.target.id !== 'assignModal') return;
      const modal = document.getElementById('assignModal');
      if (modal) modal.classList.remove('show');
      currentAssignmentIssueId = null;
    }
    async function submitAssignment() {
      if (!currentAssignmentIssueId) return;
      const payload = {
        department: document.getElementById('assignDepartment').value,
        worker_id: document.getElementById('assignWorker').value,
        duration_value: Number(document.getElementById('assignDurationValue').value || 1),
        duration_unit: document.getElementById('assignDurationUnit').value
      };
      if (!payload.worker_id) {
        showFeedback('Select a registered worker before assigning this complaint.', 'error');
        return;
      }
      const res = await fetch('/admin/issues/' + currentAssignmentIssueId + '/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        alert(data.detail || 'Complaint assignment failed');
        return;
      }
      syncIssueAcrossAdminStores(currentAssignmentIssueId, {
        assigned_department: data.assigned_department || payload.department,
        assigned_worker_id: data.assigned_worker_id || payload.worker_id,
        assignment_deadline: data.assignment_deadline || null,
        assignment_duration_label: data.assignment_duration_label || null,
        status: data.status || 'In Progress',
        worker_status: 'Assigned',
        worker_status_message: 'Assigned to ' + (data.assigned_worker_id || payload.worker_id)
      });
      closeAssignModal();
      showFeedback(data.message || 'Complaint assigned successfully.');
    }
    function viewEmergency(index) {
      const item = emergencyAlertStore[index];
      if (!item) return;
      expandedEmergencyId = expandedEmergencyId === item.id ? null : item.id;
      renderEmergencyList();
    }
    async function updateEmergencyStatus(index) {
      const item = emergencyAlertStore[index];
      if (!item) return;
      const picker = document.getElementById('em_status_' + index);
      if (!picker) return;
      const nextStatus = picker.value;
      if (nextStatus === 'Resolved' && (item.worker_status || '').toLowerCase() !== 'resolved') {
        alert('Worker must resolve this emergency before admin can close it.');
        return;
      }
      const formData = new FormData();
      formData.append('status', nextStatus);
      const res = await fetch('/admin/emergency-alerts/' + item.id + '/status', { method: 'PUT', body: formData });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Emergency status update failed');
        return;
      }
      const payload = await res.json();
      emergencyAlertStore[index] = {
        ...item,
        status: payload.new_status || nextStatus,
        updated_at: new Date().toISOString(),
        worker_status: payload.worker_status || item.worker_status,
        severity: payload.reset_snapshot ? 'Safe' : item.severity,
        value: payload.reset_snapshot ? 'Reset to safe baseline' : item.value,
        note: payload.reset_snapshot ? 'Monitoring updated' : item.note
      };
      renderEmergencyList();
      if (payload.mail_sent === true) {
        showFeedback('Emergency status updated and user notification sent.');
      } else if (payload.mail_sent === false) {
        showFeedback('Emergency updated, but email failed: ' + (payload.mail_status || 'unknown'), 'warning');
      } else {
        showFeedback(payload.message || 'Emergency status updated.');
      }
      queueAdminRefresh(0);
    }
    async function assignEmergencyAlert(index) {
      const item = emergencyAlertStore[index];
      if (!item || item.assigned_department === 'Emergency') return;
      assigningEmergencyIds.add(item.id);
      renderEmergencyList();
      const res = await fetch('/admin/emergency-alerts/' + item.id + '/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ department: 'Emergency' })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        assigningEmergencyIds.delete(item.id);
        renderEmergencyList();
        showFeedback(data.detail || 'Unable to assign alert to Emergency.', 'error');
        return;
      }
      assigningEmergencyIds.delete(item.id);
      emergencyAlertStore[index] = {
        ...item,
        assigned_department: data.assigned_department || 'Emergency',
        assigned_at: data.assigned_at || new Date().toISOString(),
        status: data.status || 'Assigned to Emergency',
        worker_status: data.worker_status || 'Assigned'
      };
      updateEmergencyIndicator();
      renderEmergencyList();
      showFeedback(data.message || 'Emergency alert assigned to Emergency department.');
      queueAdminRefresh();
    }
    async function deleteEmergency(index) {
      const item = emergencyAlertStore[index];
      if (!item) return;
      const confirmed = confirm('Delete this emergency alert? This action cannot be undone.');
      if (!confirmed) return;
      const res = await fetch('/admin/emergency-alerts/' + item.id, { method: 'DELETE' });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Emergency delete failed');
        return;
      }
      emergencyAlertStore.splice(index, 1);
      if (expandedEmergencyId === item.id) expandedEmergencyId = null;
      renderEmergencyList();
      showFeedback('Emergency alert deleted successfully.');
      queueAdminRefresh(0);
    }
    function closeComplaintModal(event) {
      if (event && event.target && event.target.id !== 'complaintModal') return;
      const modal = document.getElementById('complaintModal');
      if (modal) modal.classList.remove('show');
    }
    function viewComplaint(index) {
      const item = complaintStore[index];
      if (!item) return;
      const modal = document.getElementById('complaintModal');
      const body = document.getElementById('complaintModalBody');
      if (!modal || !body) return;

      const imageBlock = (item.media_urls || []).length
        ? `<div class="thumbGrid">${item.media_urls.map(src => `<a href="${esc(src)}" target="_blank" rel="noopener noreferrer"><img src="${esc(src)}" alt="Complaint photo" /></a>`).join('')}</div>`
        : '<p class="muted">No uploaded images for this complaint.</p>';

      body.innerHTML = `
        <div class="mono" style="margin-bottom:8px;">${esc(item.complaint_number || '-')}</div>
        <p><strong>User:</strong> ${esc(item.user_name || '-')}</p>
        <p><strong>Issue:</strong> ${esc(item.title || '-')}</p>
        <p><strong>Location:</strong> ${esc(item.location || '-')}</p>
        <p><strong>Status:</strong> ${esc(item.status || '-')}</p>
        <p><strong>Category:</strong> ${esc(item.category || '-')}</p>
        <p><strong>Assigned Department:</strong> ${esc(item.assigned_department || 'Not assigned')}</p>
        <p><strong>Assigned Worker:</strong> ${esc(item.assigned_worker_id || 'Not assigned')}</p>
        <p><strong>Deadline:</strong> ${esc(item.assignment_duration_label || '-')}${item.assignment_deadline ? ' | ' + esc(prettyDate(item.assignment_deadline)) : ''}</p>
        <p><strong>Reported At:</strong> ${esc(prettyDate(item.created_at))}</p>
        <p><strong>Description:</strong> ${esc(item.description || '-')}</p>
        <h4 style="margin:12px 0 8px;">Uploaded Images</h4>
        ${imageBlock}
      `;
      modal.classList.add('show');
    }
    async function deleteComplaint(issueId) {
      if (!issueId) return;
      const confirmed = confirm('Delete this complaint? This action cannot be undone.');
      if (!confirmed) return;
      const res = await fetch('/admin/issues/' + issueId, { method: 'DELETE' });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Delete failed');
        return;
      }
      complaintStore = removeById(complaintStore, issueId);
      recentIssueStore = removeById(recentIssueStore, issueId);
      workerResolutionStore = removeById(workerResolutionStore, issueId);
      adminUserStore = adminUserStore.map(user => ({
        ...user,
        complaints: removeById(user.complaints || [], issueId)
      }));
      recomputeAdminStats();
      closeComplaintModal();
      renderAdminDashboard();
      persistAdminPanelCache();
    }
    function renderEmergencyList() {
      const target = document.getElementById('emergencyList');
      if (!target) return;
      target.innerHTML = (emergencyAlertStore || []).map((item, idx) => {
        const assignedToEmergency = (item.assigned_department || '').toLowerCase() === 'emergency';
        const isExpanded = expandedEmergencyId === item.id;
        const isAssigning = assigningEmergencyIds.has(item.id);
        const canDelete = ['Resolved', 'Rejected'].includes(item.status || '');
        return `
          <article class="emergencyCard">
            <div class="emergencyCardHeader">
              <div class="emergencyMeta">
                <h4>${esc(item.sender_name || 'Unknown sender')}</h4>
                <p>${esc(item.sensor_label || 'Emergency sensor')} • ${esc(prettyDate(item.created_at))}</p>
              </div>
              <div class="statusStack">
                ${statusPill(item.status)}
                <span class="pill danger">${esc(item.severity || 'Danger')}</span>
              </div>
            </div>
            <div class="emergencyDataGrid">
              <div class="emergencyField">
                <span class="emergencyFieldLabel">Location</span>
                <span class="emergencyFieldValue">${esc(item.location || '-')}</span>
              </div>
              <div class="emergencyField">
                <span class="emergencyFieldLabel">Assigned Department</span>
                <span class="emergencyFieldValue">${esc(item.assigned_department || 'Not assigned yet')}</span>
              </div>
              <div class="emergencyField">
                <span class="emergencyFieldLabel">Assigned to Worker</span>
                <span class="emergencyFieldValue">${esc(item.worker_status || 'Awaiting worker action')}</span>
              </div>
              <div class="emergencyField">
                <span class="emergencyFieldLabel">Sender Contact</span>
                <span class="emergencyFieldValue">${esc(item.sender_email || '-')}${item.sender_phone ? ' • ' + esc(item.sender_phone) : ''}</span>
              </div>
              <div class="emergencyField">
                <span class="emergencyFieldLabel">Public Note</span>
                <span class="emergencyFieldValue">${esc(item.note || 'No note shared')}</span>
              </div>
              ${isExpanded ? `
              <div class="emergencyField">
                <span class="emergencyFieldLabel">Priority</span>
                <span class="emergencyFieldValue">${esc(item.priority || '-')}</span>
              </div>
              <div class="emergencyField">
                <span class="emergencyFieldLabel">Sensor Value</span>
                <span class="emergencyFieldValue">${esc(item.value || '-')}</span>
              </div>
              <div class="emergencyField">
                <span class="emergencyFieldLabel">Assigned At</span>
                <span class="emergencyFieldValue">${esc(item.assigned_at ? prettyDate(item.assigned_at) : '-')}</span>
              </div>
              <div class="emergencyField">
                <span class="emergencyFieldLabel">Worker Updated</span>
                <span class="emergencyFieldValue">${esc(item.worker_updated_at ? prettyDate(item.worker_updated_at) : '-')}</span>
              </div>
              <div class="emergencyField">
                <span class="emergencyFieldLabel">Alert ID</span>
                <span class="emergencyFieldValue mono">${esc(item.id || '-')}</span>
              </div>` : ''}
            </div>
            <div class="emergencyModalActions">
              <div class="muted">${requiresEmergencyAttention(item) ? 'Needs admin attention' : 'Monitoring updated'}</div>
              <div class="emergencyActionGroup">
                <select id="em_status_${idx}" aria-label="Update emergency status for ${esc(item.sender_name || 'alert')}">
                  <option ${item.status === 'Open' ? 'selected' : ''}>Open</option>
                  <option ${item.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                  <option ${item.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                  <option ${item.status === 'Rejected' ? 'selected' : ''}>Rejected</option>
                  <option ${item.status === 'Assigned to Emergency' ? 'selected' : ''}>Assigned to Emergency</option>
                  <option ${item.status === 'Awaiting Admin Closure' ? 'selected' : ''}>Awaiting Admin Closure</option>
                </select>
                <button class="buttonPrimary" type="button" onclick="updateEmergencyStatus(${idx})">Update</button>
                <button id="em_assign_${idx}" class="buttonWarning" type="button" ${assignedToEmergency || isAssigning ? 'disabled' : ''} onclick="assignEmergencyAlert(${idx})">${isAssigning ? '<span class="loadingSpinner" aria-hidden="true"></span> Assigning' : assignedToEmergency ? 'Assigned' : 'Assign'}</button>
                <button class="buttonSecondary" type="button" onclick="viewEmergency(${idx})">${isExpanded ? 'Hide' : 'View'}</button>
                ${canDelete ? `<button class="iconBtn" title="Delete emergency alert" aria-label="Delete emergency alert ${esc(item.id || '')}" onclick="deleteEmergency(${idx})">&#128465;</button>` : ''}
              </div>
            </div>
          </article>
        `;
      }).join('') || '<div class="muted">No emergency alerts right now.</div>';
      updateEmergencyIndicator();
    }
    function renderIssueRows(items) {
      const target = document.getElementById('issueRows');
      if (!target) return;
      target.innerHTML = (items || []).map(item => `
        <tr>
          <td class="tableId">${esc(item.complaint_number || '-')}</td>
          <td class="tableTitle">${esc(item.title || '-')}</td>
          <td class="tableLocation">${esc(item.location || '-')}</td>
          <td>
            <div class="statusStack">
              ${statusPill(item.status)}
              ${item.assigned_department ? `<span class="pill progress">${esc(item.assigned_department)}</span>` : '<span class="pill pending">Awaiting Assignment</span>'}
              ${item.assigned_worker_id ? `<span class="pill progress">${esc(item.assigned_worker_id)}</span>` : ''}
            </div>
          </td>
          <td>
            <div class="workerStack">
              <strong>${esc(item.worker_status_message || 'Worker')}</strong>
              <span>${item.worker_status ? statusPill(item.worker_status) : '<span class="muted">No update</span>'}</span>
            </div>
          </td>
          <td>
            <div class="tableActions">
              <select id="status_${item.id}" aria-label="Update complaint status for ${esc(item.complaint_number || 'complaint')}">
                <option ${item.status === 'Pending' ? 'selected' : ''}>Pending</option>
                <option ${item.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                <option ${item.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                <option ${item.status === 'Rejected' ? 'selected' : ''}>Rejected</option>
              </select>
              <button class="buttonPrimary" onclick="updateIssueStatus(${item.id}, document.getElementById('status_${item.id}').value)">Update</button>
              <button class="iconBtn" title="Delete complaint" aria-label="Delete complaint ${esc(item.complaint_number || '')}" onclick="deleteComplaint(${item.id})">&#128465;</button>
            </div>
          </td>
        </tr>
      `).join('') || '<tr><td colspan="6">No complaints found</td></tr>';
    }
    async function loadPanel(force = false) {
      if (adminPanelLoadInFlight) return;
      if (isAdminEmergencyModalOpen) return;
      adminPanelLoadInFlight = true;
      try {
        const res = await fetch('/admin/panel-data', { cache: 'no-store' });
        if (!res.ok) { window.location.href = '/admin'; return; }
        const data = await res.json();
        applyAdminPanelData(data);
      } finally {
        adminPanelLoadInFlight = false;
      }
    }
    function connectAdminPanelEvents() {
      if (adminPanelSocket || adminPanelEventSource) return;
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        adminPanelSocket = new WebSocket(`${protocol}//${window.location.host}/ws/admin`);
        adminPanelSocket.onmessage = (event) => {
          try {
            handleAdminRealtimeEvent(JSON.parse(event.data));
          } catch (_) {
            queueAdminRefresh(0);
          }
        };
        adminPanelSocket.onclose = () => {
          adminPanelSocket = null;
          connectAdminPanelSSEFallback();
        };
        adminPanelSocket.onerror = () => {
          if (adminPanelSocket) adminPanelSocket.close();
        };
      } catch (_) {
        connectAdminPanelSSEFallback();
      }
    }
    function connectAdminPanelSSEFallback() {
      if (adminPanelEventSource) return;
      adminPanelEventSource = new EventSource('/panel/events');
      adminPanelEventSource.onmessage = (event) => {
        try {
          handleAdminRealtimeEvent(JSON.parse(event.data));
        } catch (_) {
          queueAdminRefresh(0);
        }
      };
      adminPanelEventSource.onerror = () => {
        if (adminPanelEventSource) {
          adminPanelEventSource.close();
          adminPanelEventSource = null;
        }
        window.setTimeout(connectAdminPanelEvents, 1500);
      };
    }
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        closeEmergencyModal();
        closeComplaintModal();
        closeAssignModal();
        closeWorkerModal();
      }
    });
    hydrateAdminPanelFromCache();
    loadPanel(true);
    connectAdminPanelEvents();
    setInterval(() => loadPanel(), 60000);
  </script>
</body>
</html>
"""
    )


@app.get("/user/stats")
def get_user_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_or_compute_cached_json(
        f"user-stats:{current_user.id}",
        5,
        lambda: {
            "total_issues": db.query(Issue).filter(Issue.user_id == current_user.id).count(),
            "pending": db.query(Issue).filter(
                Issue.user_id == current_user.id,
                Issue.status.notin_(["Resolved", "Rejected"]),
            ).count(),
            "resolved": db.query(Issue).filter(Issue.user_id == current_user.id, Issue.status == "Resolved").count(),
        },
    )


# ─────────────────────────────────────────────
# IoT SENSOR DATA ENDPOINTS  ← ONLY NEW ADDITION
# ─────────────────────────────────────────────

EMERGENCY_ALERTS_FILE = os.path.join(BASE_DIR, "emergency_alerts.jsonl")
emergency_alerts = []


class EmergencyAlertPayload(BaseModel):
    sensor_id: str
    sensor_label: str
    severity: str
    value: Optional[str] = None
    note: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class WorkerEmergencyStatusPayload(BaseModel):
    status: str


def append_emergency_alert(entry: dict):
    emergency_alerts.append(entry)
    if len(emergency_alerts) > 5000:
        del emergency_alerts[: len(emergency_alerts) - 5000]
    try:
        with open(EMERGENCY_ALERTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception:
        pass


def save_all_emergency_alerts():
    try:
        with open(EMERGENCY_ALERTS_FILE, "w", encoding="utf-8") as f:
            for entry in emergency_alerts:
                f.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception:
        pass


def load_emergency_alerts_from_disk():
    if not os.path.exists(EMERGENCY_ALERTS_FILE):
        return
    try:
        with open(EMERGENCY_ALERTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                row = line.strip()
                if not row:
                    continue
                try:
                    emergency_alerts.append(json.loads(row))
                except Exception:
                    continue
    except Exception:
        pass


def normalize_emergency_alert_rows():
    changed = False
    for item in emergency_alerts:
        if "source" not in item:
            note = str(item.get("note") or "").strip().lower()
            if note.startswith("triggered from dashboard at") or note.startswith("street light failure detected at"):
                item["source"] = "legacy_auto"
            else:
                item["source"] = "user_report"
            changed = True
        if "worker_status" not in item:
            item["worker_status"] = "Assigned" if item.get("assigned_department") else "Unassigned"
            changed = True
        if "worker_updated_at" not in item:
            item["worker_updated_at"] = None
            changed = True
        if "worker_resolution_requested_at" not in item:
            item["worker_resolution_requested_at"] = None
            changed = True
        if "location" not in item:
            item["location"] = None
            changed = True
        if "latitude" not in item:
            item["latitude"] = None
            changed = True
        if "longitude" not in item:
            item["longitude"] = None
            changed = True
    if changed:
        save_all_emergency_alerts()


def get_visible_emergency_alerts():
    return [item for item in emergency_alerts if str(item.get("source") or "").strip().lower() == "user_report"]


load_emergency_alerts_from_disk()
normalize_emergency_alert_rows()


@app.post("/user/emergency-alerts")
def create_emergency_alert(
    payload: EmergencyAlertPayload,
    current_user: User = Depends(get_current_user),
):
    severity = (payload.severity or "").strip().title()
    if severity not in {"Safe", "Moderate", "Danger"}:
        raise HTTPException(status_code=400, detail="Severity must be Safe, Moderate, or Danger")
    if severity != "Danger":
        raise HTTPException(status_code=400, detail="Only danger alerts can be sent to admin")

    sensor_id = payload.sensor_id.strip()
    user_id = current_user.id
    visible_alerts = get_visible_emergency_alerts()
    existing_open_alert = next(
        (
            item
            for item in reversed(visible_alerts)
            if (item.get("user") or {}).get("id") == user_id
            and str(item.get("sensor_id") or "").strip() == sensor_id
            and str(item.get("status") or "").strip().lower() not in {"resolved", "rejected"}
        ),
        None,
    )
    if existing_open_alert:
        return {
            "message": "Emergency report already submitted",
            "duplicate": True,
            "alert": existing_open_alert,
        }

    alert = {
        "id": str(uuid.uuid4()),
        "created_at": iso_now(),
        "priority": "High" if severity == "Danger" else "Normal",
        "severity": severity,
        "sensor_id": sensor_id,
        "sensor_label": payload.sensor_label.strip(),
        "value": (payload.value or "").strip(),
        "note": (payload.note or "").strip(),
        "source": "user_report",
        "status": "Open",
        "assigned_department": None,
        "assigned_at": None,
        "worker_status": "Unassigned",
        "worker_updated_at": None,
        "worker_resolution_requested_at": None,
        "location": (payload.location or "").strip() or None,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "user": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone": current_user.phone,
        },
    }
    append_emergency_alert(alert)
    publish_panel_event("emergency-alert-created", {"alert": alert})
    return {"message": "Message sent successfully", "alert": alert}


def send_emergency_resolution_email(alert: dict, status_value: str) -> tuple[bool, str]:
    user = (alert or {}).get("user", {}) or {}
    to_email = (user.get("email") or "").strip()
    full_name = user.get("full_name") or "Citizen"
    if not to_email:
        return False, "User email missing for emergency alert"
    if not (MAIL_SERVER and MAIL_PORT and MAIL_USERNAME and MAIL_PASSWORD and MAIL_FROM):
        return False, "Email configuration is incomplete"

    sensor = alert.get("sensor_label") or "Emergency sensor"
    location = alert.get("location") or "Reported location"
    priority = alert.get("priority") or "High"
    note = alert.get("note") or "-"

    body = (
        f"Dear {full_name},\n\n"
        f"Your emergency alert has been updated by the admin team.\n\n"
        f"Alert ID: {alert.get('id', '-')}\n"
        f"Sensor: {sensor}\n"
        f"Priority: {priority}\n"
        f"Location: {location}\n"
        f"Status: {status_value}\n"
        f"Note: {note}\n\n"
        "Update: Your emergency issue is solved and necessary action has been completed.\n"
        "If you still face the issue, please raise a fresh emergency alert.\n\n"
        "Regards,\nUrban Sentinel Admin"
    )

    msg = EmailMessage()
    msg["Subject"] = f"Urban Sentinel Emergency Update - {status_value}"
    msg["From"] = MAIL_FROM
    msg["To"] = to_email
    msg.set_content(body)

    try:
        if MAIL_SSL_TLS:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, context=context) as smtp:
                smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as smtp:
                smtp.ehlo()
                if MAIL_STARTTLS:
                    smtp.starttls(context=ssl.create_default_context())
                    smtp.ehlo()
                smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
                smtp.send_message(msg)
        return True, "Emergency update email sent"
    except Exception as exc:
        return False, f"Emergency email failed: {exc}"


def find_emergency_alert(alert_id: str) -> Optional[dict]:
    for item in emergency_alerts:
        if str(item.get("id")) == str(alert_id):
            return item
    return None


def reset_sensor_state_from_emergency(alert: dict):
    location = alert.get("location")
    latitude = _safe_float(alert.get("latitude"))
    longitude = _safe_float(alert.get("longitude"))
    if not location and latitude is None and longitude is None:
        return None
    reset = force_reset_snapshot(
        latest_sensor_data_by_location,
        sensor_history,
        location=location,
        latitude=latitude,
        longitude=longitude,
    )
    sensor_label = str(alert.get("sensor_label") or "").strip().lower()
    if "fire" in sensor_label or "smoke" in sensor_label:
        reset["fire_smoke"] = 10
        reset["fire_status"] = "Safe"
    global latest_sensor_data
    global latest_iot_data
    latest_sensor_data = reset.copy()
    latest_iot_data = build_latest_iot_snapshot(reset)
    try:
        with open(SENSOR_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(reset, ensure_ascii=True) + "\n")
    except Exception:
        pass
    return enrich_snapshot(reset, sensor_history)


@app.get("/user/emergency-alerts")
def get_user_emergency_alerts(limit: int = 50, current_user: User = Depends(get_current_user)):
    safe_limit = max(1, min(limit, 200))
    filtered = [a for a in get_visible_emergency_alerts() if a.get("user", {}).get("id") == current_user.id]
    return {"count": min(len(filtered), safe_limit), "alerts": filtered[-safe_limit:][::-1]}


@app.get("/admin/emergency-alerts", include_in_schema=False)
def get_admin_emergency_alerts(_: dict = Depends(get_current_admin), limit: int = 200):
    safe_limit = max(1, min(limit, 500))
    visible = get_visible_emergency_alerts()
    return {"count": min(len(visible), safe_limit), "alerts": visible[-safe_limit:][::-1]}


@app.put("/admin/emergency-alerts/{alert_id}/status", include_in_schema=False)
def update_emergency_alert_status(
    alert_id: str,
    status: str = Form(...),
    background_tasks: BackgroundTasks = None,
    _: dict = Depends(get_current_admin),
):
    normalized = (status or "").strip().title()
    valid = {"Open", "In Progress", "Resolved", "Rejected"}
    if normalized not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(sorted(valid))}")

    found = find_emergency_alert(alert_id)

    if not found:
        raise HTTPException(status_code=404, detail="Emergency alert not found")
    if normalized == "Resolved" and str(found.get("worker_status") or "").strip().lower() != "resolved":
        raise HTTPException(
            status_code=400,
            detail="Worker must update the emergency to Resolved before admin can close it",
        )

    found["status"] = normalized
    found["updated_at"] = datetime.utcnow().isoformat()

    save_all_emergency_alerts()

    mail_sent = None
    mail_status = "No email sent"
    reset_snapshot = None
    if normalized == "Resolved":
        if background_tasks is not None:
            background_tasks.add_task(send_emergency_resolution_email, found, normalized)
            mail_sent = True
            mail_status = "Emergency email notification queued"
        else:
            mail_sent, mail_status = send_emergency_resolution_email(found, normalized)
        reset_snapshot = reset_sensor_state_from_emergency(found)
        if reset_snapshot is not None:
            found["severity"] = "Safe"
            found["value"] = "Reset to safe baseline"
            found["note"] = "Monitoring updated"
            save_all_emergency_alerts()

    publish_panel_event(
        "emergency-status-updated",
        {
            "alert_id": alert_id,
            "status": normalized,
            "worker_status": found.get("worker_status"),
            "alert": found,
            "reset_snapshot": reset_snapshot,
        },
    )

    return {
        "message": "Emergency alert status updated",
        "alert_id": alert_id,
        "new_status": normalized,
        "worker_status": found.get("worker_status"),
        "mail_sent": mail_sent,
        "mail_status": mail_status,
        "reset_snapshot": reset_snapshot,
    }


@app.post("/admin/emergency-alerts/{alert_id}/assign", include_in_schema=False)
def assign_emergency_alert(
    alert_id: str,
    _: dict = Depends(get_current_admin),
):
    assigned_department = normalize_department("Emergency")
    found = find_emergency_alert(alert_id)

    if not found:
        raise HTTPException(status_code=404, detail="Emergency alert not found")
    found["assigned_department"] = assigned_department
    found["assigned_at"] = datetime.utcnow().isoformat()
    found["updated_at"] = found["assigned_at"]
    found["status"] = f"Assigned to {assigned_department}"
    found["worker_status"] = "Assigned"
    found["worker_updated_at"] = found["assigned_at"]

    save_all_emergency_alerts()
    publish_panel_event(
        "emergency-assigned",
        {
            "alert_id": alert_id,
            "assigned_department": assigned_department,
            "status": found["status"],
            "worker_status": found["worker_status"],
        },
    )
    return {
        "message": "Emergency alert assigned successfully",
        "alert_id": alert_id,
        "assigned_department": assigned_department,
        "status": found["status"],
        "worker_status": found["worker_status"],
        "assigned_at": found["assigned_at"],
    }


@app.delete("/admin/emergency-alerts/{alert_id}", include_in_schema=False)
def delete_emergency_alert(
    alert_id: str,
    _: dict = Depends(get_current_admin),
):
    index = None
    for idx, item in enumerate(emergency_alerts):
        if str(item.get("id")) == str(alert_id):
            index = idx
            break

    if index is None:
        raise HTTPException(status_code=404, detail="Emergency alert not found")

    emergency_alerts.pop(index)
    save_all_emergency_alerts()
    publish_panel_event(
        "emergency-deleted",
        {
            "alert_id": alert_id,
        },
    )
    return {"message": "Emergency alert deleted successfully", "deleted_alert_id": alert_id}


class SensorData(BaseModel):
    device_identifier: Optional[str] = None
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    device_model: Optional[str] = None
    device_platform: Optional[str] = None
    device_os_version: Optional[str] = None
    firmware_version: Optional[str] = None
    app_version: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    flood_distance: Optional[float] = None
    flood_level: Optional[int] = None
    flood_status: Optional[str] = None
    air_smoke: Optional[int] = None
    air_status: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    temp_status: Optional[str] = None
    traffic_lane1: Optional[int] = None
    traffic_lane2: Optional[int] = None
    traffic_total: Optional[int] = None
    traffic_status: Optional[str] = None
    noise_level: Optional[int] = None
    noise_status: Optional[str] = None
    light_percent: Optional[int] = None
    light_status: Optional[str] = None
    bin_distance: Optional[float] = None
    bin_fill: Optional[int] = None
    bin_status: Optional[str] = None
    rain_percent: Optional[int] = None
    rain_status: Optional[str] = None
    fire_smoke: Optional[int] = None
    fire_status: Optional[str] = None
    parking_a: Optional[str] = None
    parking_b: Optional[str] = None
    parking_available: Optional[int] = None
    parking_status: Optional[str] = None
    timestamp: Optional[str] = None


DEFAULT_LIVE_IOT_DATA = {
    "air": {"value": 50, "status": "Safe"},
    "temperature": {"value": 28, "status": "Safe"},
    "humidity": {"value": 60, "status": "Safe"},
    "rain": {"value": 0, "status": "Safe"},
    "timestamp": None,
}

latest_sensor_data = {}
latest_sensor_data_by_location = {}
latest_iot_data = DEFAULT_LIVE_IOT_DATA.copy()
serial_log_lines = []
MAX_SERIAL_LOG_LINES = 2000
SERIAL_LOG_FILE = os.path.join(BASE_DIR, "iot_serial_logs.jsonl")
sensor_history = []
MAX_SENSOR_HISTORY = 30000
SENSOR_HISTORY_FILE = os.path.join(BASE_DIR, "iot_sensor_history.jsonl")
INCIDENT_HISTORY_FILE = os.path.join(BASE_DIR, "incident_history.jsonl")
incident_records = []
incident_query_cache = {}
INCIDENT_QUERY_CACHE_LIMIT = 48
incidents = incident_records
sensor_data = sensor_history


class SerialLogLine(BaseModel):
    line: str
    source: Optional[str] = "serial_reader"
    timestamp: Optional[str] = None


class MonitoringAlertCreatePayload(BaseModel):
    sensor_id: str
    sensor_label: str
    severity: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    note: Optional[str] = None
    predicted_status_5_min: Optional[str] = None
    value: Optional[str] = None


class MonitoringAlertAdminPayload(BaseModel):
    status: Optional[str] = None
    assigned_department: Optional[str] = None
    resolve: bool = False


class SensorResetPayload(BaseModel):
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


MONITORING_ALERTS_FILE = os.path.join(BASE_DIR, "sensor_alert_events.jsonl")
monitoring_alerts = []
central_sensor_engine = CentralSensorEngine(interval_seconds=SENSOR_SIM_INTERVAL_SECONDS)


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_iso_datetime(value, default_timezone=timezone.utc):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            if default_timezone is not None:
                parsed = parsed.replace(tzinfo=default_timezone)
            else:
                return parsed
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return None


def serialize_app_timestamp(value, default_timezone=timezone.utc):
    if isinstance(value, datetime):
        return isoformat_app_datetime(value)
    parsed = parse_iso_datetime(value, default_timezone)
    if parsed is None:
        return value
    return isoformat_app_datetime(parsed)


def format_window_label(range_key: str, custom_date: Optional[str] = None) -> str:
    if range_key == "5m":
        return "Last 5 Minutes"
    if range_key == "30m":
        return "Last 30 Minutes"
    if range_key == "1d":
        return "Last 24 Hours"
    if range_key == "custom" and custom_date:
        parsed = parse_iso_datetime(f"{custom_date}T00:00:00", APP_TIMEZONE)
        if parsed:
            return to_app_timezone(parsed).strftime("%d/%m/%Y")
    return "Selected Window"


def floor_incident_bucket(value: datetime, bucket_minutes: int) -> datetime:
    bucket = value.replace(second=0, microsecond=0)
    if bucket_minutes >= 60:
        return bucket.replace(minute=0)
    bucket_minute = (bucket.minute // bucket_minutes) * bucket_minutes
    return bucket.replace(minute=bucket_minute)


def format_incident_timestamp(value: datetime) -> str:
    localized = to_app_timezone(value)
    if localized is None:
        return value.isoformat()
    return localized.isoformat()


INCIDENT_SENSOR_TOTAL = 7
INCIDENT_SENSOR_BUCKETS = (
    "flood_level",
    "traffic_total",
    "noise_level",
    "light_percent",
    "bin_fill",
    "fire_smoke",
    "parking_available",
)


def normalize_dashboard_severity(status: Optional[str]) -> str:
    normalized = str(status or "").strip().upper()
    if not normalized:
        return "safe"
    if (
        "CRITICAL" in normalized
        or "HAZARDOUS" in normalized
        or "FULL!" in normalized
        or "EMERGENCY" in normalized
        or "FAULT" in normalized
        or "ILLEGAL" in normalized
        or normalized == "DANGER"
    ):
        return "danger"
    if (
        "WARNING" in normalized
        or "MODERATE" in normalized
        or "CAUTION" in normalized
        or "NEARLY FULL" in normalized
        or "WATCH" in normalized
    ):
        return "moderate"
    return "safe"


def classify_simulation_sensor(sensor_id: str, value: Optional[float]) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "safe"
    config = {
        "noise_level": {"moderate": 80, "danger": 100, "danger_when": "high"},
        "flood_level": {"moderate": 45, "danger": 80, "danger_when": "high"},
        "light_percent": {"moderate": 35, "danger": 20, "danger_when": "low"},
        "bin_fill": {"moderate": 70, "danger": 90, "danger_when": "high"},
    }.get(sensor_id)
    if not config:
        return "safe"
    if config["danger_when"] == "low":
        if numeric <= config["danger"]:
            return "danger"
        if numeric <= config["moderate"]:
            return "moderate"
        return "safe"
    if numeric >= config["danger"]:
        return "danger"
    if numeric >= config["moderate"]:
        return "moderate"
    return "safe"


def classify_snapshot_sensor_states(snapshot: dict) -> dict:
    counts = {"danger_count": 0, "moderate_count": 0, "safe_count": 0, "incident_count": 0}

    def add_state(state: str):
        key = f"{state}_count"
        counts[key] += 1
        counts["incident_count"] += 1

    details = snapshot.get("sensor_details") or {}
    for sensor_id in ("flood_level", "noise_level", "light_percent", "bin_fill"):
        add_state(normalize_dashboard_severity((details.get(sensor_id) or {}).get("status")))

    traffic_state = normalize_dashboard_severity(snapshot.get("traffic_status"))
    if traffic_state == "safe":
        traffic_value = _safe_float(snapshot.get("traffic_total"))
        if traffic_value is not None:
            if traffic_value >= 16:
                traffic_state = "danger"
            elif traffic_value >= 8:
                traffic_state = "moderate"
    add_state(traffic_state)

    fire_state = normalize_dashboard_severity(snapshot.get("fire_status"))
    if fire_state == "safe":
        fire_value = _safe_float(snapshot.get("fire_smoke"))
        if fire_value is not None:
            if fire_value >= 80:
                fire_state = "danger"
            elif fire_value >= 45:
                fire_state = "moderate"
    add_state(fire_state)

    parking_state = "safe"
    parking_a = str(snapshot.get("parking_a") or "")
    parking_b = str(snapshot.get("parking_b") or "")
    parking_available = _safe_float(snapshot.get("parking_available"))
    if "ILLEGAL" in parking_a.upper() or "ILLEGAL" in parking_b.upper():
        parking_state = "danger"
    elif parking_available is not None:
        if parking_available <= 0:
            parking_state = "danger"
        elif parking_available == 1:
            parking_state = "moderate"
    add_state(parking_state)

    return counts


def storage_source_label() -> str:
    return "memory"


def build_environment_fallback(latitude: float, longitude: float, location_name: Optional[str] = None, message: str = "Live data unavailable"):
    timestamp = datetime.utcnow().isoformat()
    return {
        "location": {
            "label": location_name or "Selected location",
            "latitude": latitude,
            "longitude": longitude,
        },
        "temperature": 25,
        "humidity": 55,
        "air_smoke": 40,
        "air_quality": "Good",
        "air_status": "Good",
        "rain_intensity": "None",
        "rain_percent": 0,
        "rain_status": "None",
        "timestamp": timestamp,
        "last_updated": timestamp,
        "message": message,
    }


def build_environment_response(status: str, payload: dict, source: str):
    data = {
        "temperature": payload.get("temperature"),
        "humidity": payload.get("humidity"),
        "airQuality": payload.get("air_quality") or payload.get("air_status"),
        "rain": payload.get("rain_intensity") or payload.get("rain_status"),
        "airSmoke": payload.get("air_smoke"),
        "rainPercent": payload.get("rain_percent"),
        "timestamp": payload.get("timestamp"),
        "lastUpdated": payload.get("last_updated") or payload.get("timestamp"),
        "location": payload.get("location") or {},
    }
    return {
        "status": status,
        "source": source,
        "data": data,
        "message": payload.get("message"),
        "temperature": data["temperature"],
        "humidity": data["humidity"],
        "air_smoke": data["airSmoke"],
        "air_quality": data["airQuality"],
        "air_status": payload.get("air_status") or data["airQuality"],
        "rain_intensity": data["rain"],
        "rain_percent": data["rainPercent"],
        "rain_status": payload.get("rain_status") or data["rain"],
        "timestamp": data["timestamp"],
        "last_updated": data["lastUpdated"],
        "location": data["location"],
    }


def clear_incident_query_cache():
    incident_query_cache.clear()


def set_incident_cache(key: str, payload: dict, ttl_seconds: int):
    if len(incident_query_cache) >= INCIDENT_QUERY_CACHE_LIMIT:
        oldest_key = min(
            incident_query_cache.keys(),
            key=lambda cache_key: incident_query_cache[cache_key]["stored_at"],
        )
        incident_query_cache.pop(oldest_key, None)
    incident_query_cache[key] = {
        "stored_at": time.time(),
        "expires_at": time.time() + ttl_seconds,
        "payload": payload,
    }


def get_incident_cache(key: str):
    cached = incident_query_cache.get(key)
    if not cached:
        return None
    if cached["expires_at"] < time.time():
        incident_query_cache.pop(key, None)
        return None
    return cached["payload"]


def build_incident_record(snapshot: dict):
    if not isinstance(snapshot, dict):
        return None
    timestamp = snapshot.get("timestamp") or iso_now()
    raw_status = str(snapshot.get("overall_status") or "SAFE").strip().upper()
    if raw_status in {"CRITICAL", "DANGER"}:
        incident_type = "danger"
    elif raw_status in {"WARNING", "MODERATE"}:
        incident_type = "moderate"
    else:
        incident_type = "safe"

    location = (snapshot.get("location") or "").strip() or None
    latitude = smart_safe_float(snapshot.get("latitude"))
    longitude = smart_safe_float(snapshot.get("longitude"))
    location_key = smart_build_location_key(location, latitude, longitude)

    return {
        "timestamp": timestamp,
        "type": incident_type,
        "value": 1,
        "location": location,
        "location_key": location_key,
        "latitude": latitude,
        "longitude": longitude,
    }


def append_incident_record(entry: dict):
    incident_records.append(entry)
    clear_incident_query_cache()
    try:
        with open(INCIDENT_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception:
        pass


def load_incident_records_from_disk():
    incident_records.clear()
    if not os.path.exists(INCIDENT_HISTORY_FILE):
        clear_incident_query_cache()
        return
    try:
        with open(INCIDENT_HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                row = line.strip()
                if not row:
                    continue
                try:
                    incident_records.append(json.loads(row))
                except Exception:
                    continue
        clear_incident_query_cache()
    except Exception:
        pass


def backfill_incident_records():
    if incident_records:
        return
    for item in sensor_history:
        snapshot = enrich_snapshot(item, sensor_history)
        record = build_incident_record(snapshot)
        if record:
            append_incident_record(record)


def rebuild_incident_records_from_sensor_history():
    incident_records.clear()
    clear_incident_query_cache()
    for item in sensor_history:
        snapshot = enrich_snapshot(item, sensor_history)
        record = build_incident_record(snapshot)
        if record:
            incident_records.append(record)
    try:
        with open(INCIDENT_HISTORY_FILE, "w", encoding="utf-8") as f:
            for entry in incident_records:
                f.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception:
        pass


def resolve_incident_window(range_key: str, custom_date: Optional[str], compare_previous: bool):
    now = utc_now_naive()
    if range_key == "5m":
        window_span = timedelta(minutes=5)
        window_end = now - window_span if compare_previous else now
        return window_end - window_span, window_end, 1, "5m"
    if range_key == "1d":
        window_span = timedelta(days=1)
        window_end = now - window_span if compare_previous else now
        return window_end - window_span, window_end, 60, "1d"
    if range_key == "custom":
        if not custom_date:
            raise HTTPException(status_code=400, detail="A date is required for custom incident queries.")
        selected_day = parse_iso_datetime(f"{custom_date}T00:00:00", APP_TIMEZONE)
        if selected_day is None:
            raise HTTPException(status_code=400, detail="Custom date must use YYYY-MM-DD format.")
        today_local = datetime.now(APP_TIMEZONE).date()
        selected_local_date = to_app_timezone(selected_day).date()
        if selected_local_date > today_local:
            raise HTTPException(status_code=400, detail="Future dates are not available.")
        window_start = selected_day.replace(hour=0, minute=0, second=0, microsecond=0)
        window_end = window_start + timedelta(days=1)
        return window_start, window_end, 60, "custom"

    normalized = "30m"
    window_span = timedelta(minutes=30)
    window_end = now - window_span if compare_previous else now
    return window_end - window_span, window_end, 5, normalized


def query_incident_records(
    window_start: datetime,
    window_end: datetime,
    desired_key: Optional[str] = None,
):
    rows = []
    for item in incident_records:
        parsed = parse_iso_datetime(item.get("timestamp"))
        if parsed is None or parsed < window_start or parsed >= window_end:
            continue
        if desired_key and item.get("location_key") != desired_key:
            continue
        rows.append(item)
    return rows


def query_sensor_snapshots(
    window_start: datetime,
    window_end: datetime,
    desired_key: Optional[str] = None,
):
    rows = []
    for item in sensor_history:
        parsed = parse_iso_datetime(item.get("timestamp"))
        if parsed is None or parsed < window_start or parsed >= window_end:
            continue
        item_key = smart_build_location_key(
            item.get("location"),
            _safe_float(item.get("latitude")),
            _safe_float(item.get("longitude")),
        )
        if desired_key and item_key != desired_key:
            continue
        rows.append(item)
    rows.sort(key=lambda item: parse_iso_datetime(item.get("timestamp")) or window_start)
    return rows


def build_incident_timeseries(rows, window_start: datetime, window_end: datetime, bucket_minutes: int):
    bucket_snapshots = {}
    bucket_counts = {}
    bucket_cursor = floor_incident_bucket(window_start, bucket_minutes)
    last_bucket = floor_incident_bucket(window_end - timedelta(microseconds=1), bucket_minutes)

    while bucket_cursor <= last_bucket:
        bucket_counts[bucket_cursor] = {
            "danger_count": 0,
            "moderate_count": 0,
            "safe_count": 0,
            "incident_count": 0,
        }
        bucket_cursor += timedelta(minutes=bucket_minutes)

    for item in rows:
        parsed = parse_iso_datetime(item.get("timestamp"))
        if parsed is None:
            continue
        bucket_key = floor_incident_bucket(parsed, bucket_minutes)
        if bucket_key not in bucket_counts:
            continue
        current = bucket_snapshots.get(bucket_key)
        if current is None:
            bucket_snapshots[bucket_key] = item
            continue
        current_timestamp = parse_iso_datetime(current.get("timestamp"))
        if current_timestamp is None or parsed >= current_timestamp:
            bucket_snapshots[bucket_key] = item

    for bucket_key, snapshot in bucket_snapshots.items():
        enriched_snapshot = enrich_snapshot(snapshot, sensor_history)
        bucket_counts[bucket_key] = classify_snapshot_sensor_states(enriched_snapshot)

    last_known_counts = None
    for bucket_key in sorted(bucket_counts.keys()):
        counts = bucket_counts[bucket_key]
        if counts["incident_count"] > 0:
            last_known_counts = counts.copy()
            continue
        if last_known_counts is not None:
            bucket_counts[bucket_key] = last_known_counts.copy()

    return [
        {
            "timestamp": format_incident_timestamp(bucket),
            **counts,
        }
        for bucket, counts in sorted(bucket_counts.items(), key=lambda item: item[0])
    ]


def normalize_location_key(value: Optional[str]) -> str:
    cleaned = " ".join(str(value or "").strip().lower().split())
    return cleaned


def build_location_key(location: Optional[str], latitude: Optional[float] = None, longitude: Optional[float] = None) -> str:
    normalized_location = normalize_location_key(location)
    if normalized_location:
      return normalized_location
    if latitude is not None and longitude is not None:
      return f"{round(float(latitude), 4)},{round(float(longitude), 4)}"
    return "default"


def _safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _copy_default_live_iot_data():
    return {
        "air": DEFAULT_LIVE_IOT_DATA["air"].copy(),
        "temperature": DEFAULT_LIVE_IOT_DATA["temperature"].copy(),
        "humidity": DEFAULT_LIVE_IOT_DATA["humidity"].copy(),
        "rain": DEFAULT_LIVE_IOT_DATA["rain"].copy(),
        "timestamp": DEFAULT_LIVE_IOT_DATA["timestamp"],
    }


def _coerce_live_metric(metric_value, status_key: str, fallback: dict) -> dict:
    metric = fallback.copy()
    if isinstance(metric_value, dict):
        raw_value = metric_value.get("value", fallback.get("value"))
        raw_status = metric_value.get("status", fallback.get("status"))
    else:
        raw_value = metric_value
        raw_status = None

    numeric_value = _safe_float(raw_value)
    metric["value"] = numeric_value if numeric_value is not None else fallback.get("value")
    metric["status"] = str(raw_status or status_key or fallback.get("status") or "Safe")
    return metric


def build_latest_iot_snapshot(payload: Optional[dict] = None) -> dict:
    source = payload or latest_sensor_data or {}
    snapshot = _copy_default_live_iot_data()
    snapshot["air"] = _coerce_live_metric(
        source.get("air", source.get("air_smoke")),
        source.get("air_status"),
        snapshot["air"],
    )
    snapshot["temperature"] = _coerce_live_metric(
        source.get("temperature"),
        source.get("temp_status"),
        snapshot["temperature"],
    )
    snapshot["humidity"] = _coerce_live_metric(
        source.get("humidity"),
        source.get("temp_status"),
        snapshot["humidity"],
    )
    snapshot["rain"] = _coerce_live_metric(
        source.get("rain", source.get("rain_percent")),
        source.get("rain_status"),
        snapshot["rain"],
    )
    snapshot["timestamp"] = source.get("timestamp") or source.get("last_updated") or snapshot["timestamp"]
    return snapshot


def normalize_iot_ingest_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        payload = {}

    def _metric_value(name: str, fallback_key: str):
        metric = payload.get(name)
        if isinstance(metric, dict) and metric.get("value") is not None:
            return metric.get("value")
        return payload.get(fallback_key)

    def _metric_status(name: str, fallback_key: str):
        metric = payload.get(name)
        if isinstance(metric, dict) and metric.get("status"):
            return metric.get("status")
        return payload.get(fallback_key)

    normalized = payload.copy()
    normalized["device_identifier"] = normalized.get("device_identifier") or normalized.get("device_id")
    normalized["device_name"] = normalized.get("device_name") or normalized.get("device_label")
    normalized["device_type"] = normalized.get("device_type") or normalized.get("source") or "IOT_SENSOR_DEVICE"
    normalized["device_model"] = normalized.get("device_model")
    normalized["device_platform"] = normalized.get("device_platform") or normalized.get("platform")
    normalized["device_os_version"] = normalized.get("device_os_version") or normalized.get("os_version")
    normalized["firmware_version"] = normalized.get("firmware_version")
    normalized["app_version"] = normalized.get("app_version")
    normalized["mac_address"] = normalized.get("mac_address")
    normalized["ip_address"] = normalized.get("ip_address")
    normalized["air_smoke"] = _metric_value("air", "air_smoke")
    normalized["air_status"] = _metric_status("air", "air_status")
    normalized["temperature"] = _metric_value("temperature", "temperature")
    normalized["temp_status"] = (
        _metric_status("temperature", "temp_status")
        or _metric_status("humidity", "temp_status")
    )
    normalized["humidity"] = _metric_value("humidity", "humidity")
    normalized["rain_percent"] = _metric_value("rain", "rain_percent")
    normalized["rain_status"] = _metric_status("rain", "rain_status")
    normalized["timestamp"] = normalized.get("timestamp") or datetime.utcnow().isoformat()
    return normalized


def rebuild_latest_sensor_data_by_location():
    latest_sensor_data_by_location.clear()
    for item in sensor_history:
        if not isinstance(item, dict):
            continue
        location_key = build_location_key(
            item.get("location"),
            _safe_float(item.get("latitude")),
            _safe_float(item.get("longitude")),
        )
        latest_sensor_data_by_location[location_key] = item.copy()


def upsert_latest_sensor_entry(entry: dict):
    global latest_sensor_data
    latest_sensor_data = entry.copy()
    location_key = build_location_key(
        entry.get("location"),
        _safe_float(entry.get("latitude")),
        _safe_float(entry.get("longitude")),
    )
    latest_sensor_data_by_location[location_key] = entry.copy()


def resolve_latest_sensor_entry(
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
):
    exact_key = build_location_key(location, latitude, longitude)
    if exact_key in latest_sensor_data_by_location:
        return latest_sensor_data_by_location[exact_key].copy()

    normalized_location = normalize_location_key(location)
    if normalized_location:
        for item in latest_sensor_data_by_location.values():
            if normalize_location_key(item.get("location")) == normalized_location:
                return item.copy()

    if latitude is not None and longitude is not None:
        best_match = None
        best_distance = None
        for item in latest_sensor_data_by_location.values():
            item_latitude = _safe_float(item.get("latitude"))
            item_longitude = _safe_float(item.get("longitude"))
            if item_latitude is None or item_longitude is None:
                continue
            distance = abs(item_latitude - float(latitude)) + abs(item_longitude - float(longitude))
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_match = item
        if best_match is not None and best_distance is not None and best_distance <= 0.25:
            return best_match.copy()

    return None


def merge_sensor_payload_with_previous(payload: dict, previous_entry: Optional[dict]) -> dict:
    if not previous_entry:
        return payload.copy()

    merged = previous_entry.copy()
    for key, value in payload.items():
        if value is not None:
            merged[key] = value
        elif key not in merged:
            merged[key] = value

    merged["timestamp"] = payload.get("timestamp") or previous_entry.get("timestamp") or datetime.utcnow().isoformat()
    return merged


def classify_fire_smoke_status(value) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "Data unavailable"
    if numeric >= 80:
        return "CRITICAL - FIRE CONFIRMED!"
    if numeric >= 45:
        return "WARNING - Smoke detected"
    return "Safe"


def process_sensor_ingest(payload: dict):
    location_key = smart_build_location_key(
        payload.get("location"),
        smart_safe_float(payload.get("latitude")),
        smart_safe_float(payload.get("longitude")),
    )
    previous_raw = latest_sensor_data_by_location.get(location_key)
    previous_snapshot = enrich_snapshot(previous_raw, sensor_history) if previous_raw else None
    merged_payload = merge_sensor_payload_with_previous(payload, previous_raw)
    normalized_payload = apply_realism(merged_payload.copy(), previous_raw)
    normalized_payload["fire_status"] = classify_fire_smoke_status(normalized_payload.get("fire_smoke"))
    normalized_payload["traffic_status"] = classify_traffic_status(normalized_payload.get("traffic_total"))
    normalized_payload["parking_status"] = classify_parking_status(
        normalized_payload.get("parking_available"),
        normalized_payload.get("parking_a"),
        normalized_payload.get("parking_b"),
    )
    upsert_latest_sensor_entry(normalized_payload)
    append_sensor_history(normalized_payload.copy())
    current_snapshot = enrich_snapshot(normalized_payload, sensor_history)
    incident_record = build_incident_record(current_snapshot)
    if incident_record:
        append_incident_record(incident_record)
    new_events = build_alert_events(previous_snapshot, current_snapshot)
    for event in new_events:
        append_monitoring_alert(event)
        publish_panel_event("monitoring-alert-created", {"alert": event})
    persist_sensor_rows(normalized_payload)
    return normalized_payload, current_snapshot, new_events


def append_serial_log(entry: dict):
    serial_log_lines.append(entry)
    if len(serial_log_lines) > MAX_SERIAL_LOG_LINES:
        del serial_log_lines[: len(serial_log_lines) - MAX_SERIAL_LOG_LINES]
    try:
        with open(SERIAL_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception:
        pass


def load_serial_logs_from_disk():
    serial_log_lines.clear()
    serial_log_lines.extend(load_jsonl_tail(SERIAL_LOG_FILE, MAX_SERIAL_LOG_LINES))


def append_sensor_history(entry: dict):
    sensor_history.append(entry)
    if len(sensor_history) > MAX_SENSOR_HISTORY:
        del sensor_history[: len(sensor_history) - MAX_SENSOR_HISTORY]
    try:
        with open(SENSOR_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception:
        pass


def load_jsonl_tail(file_path: str, limit: int) -> list[dict]:
    if limit <= 0 or not os.path.exists(file_path):
        return []
    rows = deque(maxlen=limit)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                row = line.strip()
                if not row:
                    continue
                try:
                    rows.append(json.loads(row))
                except Exception:
                    continue
    except Exception:
        return []
    return list(rows)


def append_monitoring_alert(entry: dict):
    monitoring_alerts.append(entry)
    if len(monitoring_alerts) > 5000:
        del monitoring_alerts[: len(monitoring_alerts) - 5000]
    try:
        with open(MONITORING_ALERTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception:
        pass


def save_all_monitoring_alerts():
    try:
        with open(MONITORING_ALERTS_FILE, "w", encoding="utf-8") as f:
            for entry in monitoring_alerts:
                f.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception:
        pass


def load_monitoring_alerts_from_disk():
    monitoring_alerts.clear()
    monitoring_alerts.extend(load_jsonl_tail(MONITORING_ALERTS_FILE, 5000))


def load_sensor_history_from_disk():
    sensor_history.clear()
    sensor_history.extend(load_jsonl_tail(SENSOR_HISTORY_FILE, MAX_SENSOR_HISTORY))


def sync_globals_from_central_sensor_engine():
    global latest_sensor_data
    global latest_iot_data
    sensor_history.clear()
    sensor_history.extend(central_sensor_engine.get_history(limit=50000))
    latest_sensor_data = central_sensor_engine.get_snapshot()
    latest_iot_data = build_latest_iot_snapshot(latest_sensor_data)
    rebuild_latest_sensor_data_by_location()


load_sensor_history_from_disk()
load_incident_records_from_disk()
load_serial_logs_from_disk()
load_monitoring_alerts_from_disk()
sync_globals_from_central_sensor_engine()
rebuild_incident_records_from_sensor_history()

@app.get("/iot/data")
def iot_data_info():
    snapshot = central_sensor_engine.get_snapshot()
    if snapshot:
        return snapshot
    fallback_snapshot = build_latest_iot_snapshot()
    return {
        "air_smoke": fallback_snapshot["air"]["value"],
        "air_status": fallback_snapshot["air"]["status"],
        "temperature": fallback_snapshot["temperature"]["value"],
        "humidity": fallback_snapshot["humidity"]["value"],
        "temp_status": fallback_snapshot["temperature"]["status"],
        "rain_percent": fallback_snapshot["rain"]["value"],
        "rain_status": fallback_snapshot["rain"]["status"],
        "timestamp": fallback_snapshot["timestamp"],
    }


def build_environment_summary_from_flat_payload(payload: dict) -> dict:
    return {
        "temperature": {"live_value": payload.get("temperature") or 0, "status": payload.get("temp_status") or "Weather"},
        "air": {"live_value": payload.get("air_smoke") or 0, "status": payload.get("air_status") or payload.get("air_quality") or "Good"},
        "humidity": {"live_value": payload.get("humidity") or 0, "status": payload.get("humidity_status") or "Comfortable"},
        "rain": {"live_value": payload.get("rain_percent") or 0, "status": payload.get("rain_status") or payload.get("rain_intensity") or "Low"},
        "timestamp": payload.get("timestamp"),
        "last_updated": payload.get("last_updated") or payload.get("timestamp"),
        "location": payload.get("location") or {},
        "source": payload.get("source") or "environment",
    }


@app.get("/iot/live")
def get_live_data(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location_name: Optional[str] = None,
):
    resolved_latitude = latitude if latitude is not None else lat
    resolved_longitude = longitude if longitude is not None else lon
    if resolved_latitude is not None and resolved_longitude is not None and OPENWEATHERMAP_API_KEY:
        try:
            weather_payload = build_openweather_environment_payload(float(resolved_latitude), float(resolved_longitude), location_name)
            return build_environment_summary_from_flat_payload(weather_payload)
        except HTTPException:
            pass
    return central_sensor_engine.get_environment_summary_payload()


@app.get("/iot/timeline")
def get_openweather_timeline(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location_name: Optional[str] = None,
):
    resolved_latitude = latitude if latitude is not None else lat
    resolved_longitude = longitude if longitude is not None else lon

    if resolved_latitude is None or resolved_longitude is None:
        resolved_latitude = DEFAULT_IOT_LIVE_LAT
        resolved_longitude = DEFAULT_IOT_LIVE_LON

    return build_openweather_timeline_payload(
        float(resolved_latitude),
        float(resolved_longitude),
        location_name,
    )

@app.post("/iot/data")
def receive_sensor_data(data: dict):
    global latest_iot_data

    payload = normalize_iot_ingest_payload(data)
    payload["timestamp"] = payload.get("timestamp") or datetime.utcnow().isoformat()
    snapshot = central_sensor_engine.ingest_external(payload)
    sync_globals_from_central_sensor_engine()
    rebuild_incident_records_from_sensor_history()
    latest_iot_data = build_latest_iot_snapshot(snapshot)
    return {
        "status": "ok",
        "message": "Sensor data received",
        "timestamp": snapshot["timestamp"],
        "overall_status": snapshot.get("overall_status"),
        "new_alerts": 0,
        "data": latest_iot_data,
    }


@app.post("/iot/log")
def receive_iot_log(payload: SerialLogLine):
    log_entry = {
        "line": payload.line,
        "source": payload.source or "serial_reader",
        "timestamp": payload.timestamp or datetime.utcnow().isoformat(),
    }
    append_serial_log(log_entry)
    print(f"[IOT] {log_entry['line']}")
    return {"message": "Log stored", "timestamp": log_entry["timestamp"]}


@app.get("/iot/log")
def get_iot_log(limit: int = 200):
    return _build_iot_logs_response(limit)


def _build_iot_logs_response(limit: int = 200):
    if limit < 1:
        limit = 1
    if limit > 2000:
        limit = 2000
    return {"count": min(len(serial_log_lines), limit), "logs": serial_log_lines[-limit:]}


@app.get("/iot/logs")
@app.get("/iot/logs/")
@app.post("/iot/logs")
@app.post("/iot/logs/")
def get_iot_logs(limit: int = 200):
    return _build_iot_logs_response(limit)


@app.get("/iot/history")
def get_iot_history(limit: int = 2000, hours: Optional[int] = None, month: Optional[str] = None):
    safe_limit = max(1, min(limit, 10000))
    rows = central_sensor_engine.get_history(limit=safe_limit, hours=hours)
    if month:
        selected = month.strip()
        rows = [item for item in rows if str(item.get("timestamp", "")).startswith(selected)]
    return {"count": len(rows), "data": rows}


@app.get("/iot/latest")
def get_latest_sensor_data():
    snapshot = central_sensor_engine.get_snapshot()
    if not snapshot:
        return {"message": "No sensor data yet"}
    return snapshot


def http_get_json(url: str, timeout: int = 10):
    request = UrlRequest(
        url,
        headers={
            "User-Agent": "UrbanSentinel/1.0",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def classify_live_air_quality(us_aqi: Optional[int]) -> str:
    if us_aqi is None:
        return "UNKNOWN"
    if us_aqi >= 151:
        return "CRITICAL - Hazardous Air!"
    if us_aqi >= 101:
        return "WARNING - Unhealthy Air"
    if us_aqi >= 51:
        return "MODERATE - Sensitive Groups"
    return "GOOD"


def classify_air_quality_label(us_aqi: Optional[int]) -> str:
    if us_aqi is None:
        return "Unavailable"
    if us_aqi >= 151:
        return "Hazardous"
    if us_aqi >= 101:
        return "Poor"
    if us_aqi >= 51:
        return "Moderate"
    return "Good"


def normalize_openweather_aqi_score(aqi_index: Optional[int]) -> Optional[int]:
    if aqi_index is None:
        return None
    mapping = {
        1: 25,
        2: 75,
        3: 150,
        4: 220,
        5: 300,
    }
    return mapping.get(int(aqi_index))


def classify_public_air_quality(aqi_score: Optional[int]) -> str:
    if aqi_score is None:
        return "Data unavailable"
    if aqi_score <= 50:
        return "Safe"
    if aqi_score <= 100:
        return "Moderate"
    if aqi_score <= 200:
        return "Poor"
    return "Hazardous"


def classify_live_temperature(temperature: Optional[float], humidity: Optional[float]) -> str:
    if temperature is None:
        return "UNKNOWN"
    if temperature >= 41:
        return "CRITICAL - Extreme Heat!"
    if temperature <= 12:
        return "CRITICAL - Extreme Cold!"
    if humidity is not None and humidity >= 90:
        return "WARNING - Very High Humidity!"
    if temperature >= 35 or temperature <= 18:
        return "MODERATE - Temperature Shift"
    return "NORMAL"


def classify_live_rain(rain_mm: Optional[float], precipitation_mm: Optional[float]) -> str:
    rain_value = rain_mm if rain_mm is not None else precipitation_mm
    if rain_value is None or rain_value <= 0.1:
        return "NO RAIN"
    if rain_value >= 12:
        return "CRITICAL - Extreme Rain!"
    if rain_value >= 6:
        return "WARNING - Heavy Rain!"
    if rain_value >= 2:
        return "MODERATE RAIN"
    return "LIGHT DRIZZLE"


def classify_rain_intensity_label(rain_mm: Optional[float], precipitation_mm: Optional[float]) -> str:
    rain_value = rain_mm if rain_mm is not None else precipitation_mm
    if rain_value is None or rain_value <= 0.1:
        return "None"
    if rain_value >= 12:
        return "Extreme"
    if rain_value >= 6:
        return "Heavy"
    if rain_value >= 2:
        return "Moderate"
    return "Low"


def classify_rain_intensity_from_percent(rain_percent: Optional[float]) -> str:
    if rain_percent is None:
        return "Unavailable"
    if rain_percent >= 75:
        return "Heavy"
    if rain_percent >= 35:
        return "Moderate"
    if rain_percent > 0:
        return "Low"
    return "None"


def classify_openweather_rain_intensity(weather_main: Optional[str], rain_one_hour: Optional[float], rain_three_hour: Optional[float]) -> str:
    if rain_one_hour is not None:
        if rain_one_hour >= 7.6:
            return "Heavy"
        if rain_one_hour >= 2.5:
            return "Moderate"
        if rain_one_hour > 0:
            return "Low"
    if rain_three_hour is not None:
        per_hour = rain_three_hour / 3
        if per_hour >= 7.6:
            return "Heavy"
        if per_hour >= 2.5:
            return "Moderate"
        if per_hour > 0:
            return "Low"
    normalized = str(weather_main or "").strip().lower()
    if normalized in {"rain", "drizzle", "thunderstorm"}:
        return "Moderate"
    if normalized in {"mist", "fog", "haze", "clouds"}:
        return "Low"
    if normalized in {"clear"}:
        return "None"
    return "Low" if normalized else "Unavailable"


def validate_metric_range(value, minimum: float, maximum: float):
    parsed = _safe_float(value)
    if parsed is None:
        return None
    if parsed < minimum or parsed > maximum:
        return None
    return parsed


def validate_public_payload(payload: dict) -> dict:
    validated = payload.copy()

    validated["temperature"] = validate_metric_range(payload.get("temperature"), -10, 60)
    validated["humidity"] = validate_metric_range(payload.get("humidity"), 0, 100)
    validated["air_smoke"] = validate_metric_range(payload.get("air_smoke"), 0, 500)
    validated["rain_percent"] = validate_metric_range(payload.get("rain_percent"), 0, 100)
    validated["flood_level"] = validate_metric_range(payload.get("flood_level"), 0, 100)
    validated["noise_level"] = validate_metric_range(payload.get("noise_level"), 0, 150)
    validated["bin_fill"] = validate_metric_range(payload.get("bin_fill"), 0, 100)
    validated["light_percent"] = validate_metric_range(payload.get("light_percent"), 0, 100)

    if validated.get("temperature") is None:
        validated["temp_status"] = "Data unavailable"
    if validated.get("humidity") is None:
        validated["humidity_status"] = "Data unavailable"
    if validated.get("air_smoke") is None:
        validated["air_quality"] = "Data unavailable"
        validated["air_status"] = "Data unavailable"
    else:
        validated["air_quality"] = classify_public_air_quality(int(validated["air_smoke"]))
        validated["air_status"] = validated["air_quality"]
    if validated.get("rain_percent") is None and not payload.get("rain_intensity"):
        validated["rain_intensity"] = "Data unavailable"
        validated["rain_status"] = "Data unavailable"

    return validated


def reverse_geocode_label(latitude: float, longitude: float) -> str:
    url = (
        "https://nominatim.openstreetmap.org/reverse?"
        + urlencode(
            {
                "lat": latitude,
                "lon": longitude,
                "format": "jsonv2",
            }
        )
    )
    try:
        payload = http_get_json(url)
        address = payload.get("address", {}) or {}
        label_parts = [
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("suburb")
            or address.get("county"),
            address.get("state"),
            address.get("country"),
        ]
        label = ", ".join([str(part).strip() for part in label_parts if part])
        return label or payload.get("display_name") or f"{latitude:.4f}, {longitude:.4f}"
    except Exception:
        return f"{latitude:.4f}, {longitude:.4f}"


def geocode_location_name(location: str) -> Optional[dict]:
    cleaned = str(location or "").strip()
    if len(cleaned) < 2:
        return None

    url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        + urlencode({"name": cleaned, "count": 1, "language": "en", "format": "json"})
    )
    try:
        payload = http_get_json(url)
        first = (payload.get("results") or [None])[0]
        if first:
            return {
                "latitude": float(first["latitude"]),
                "longitude": float(first["longitude"]),
                "label": ", ".join(
                    [
                        str(part).strip()
                        for part in [first.get("name"), first.get("admin1"), first.get("country")]
                        if part
                    ]
                )
                or cleaned,
            }
    except Exception:
        return None
    return None


def geocode_location_name_openweather(location: str) -> Optional[dict]:
    cleaned = str(location or "").strip()
    if len(cleaned) < 2 or not OPENWEATHERMAP_API_KEY:
        return None

    url = (
        "https://api.openweathermap.org/geo/1.0/direct?"
        + urlencode(
            {
                "q": cleaned,
                "limit": 1,
                "appid": OPENWEATHERMAP_API_KEY,
            }
        )
    )
    try:
        payload = http_get_json(url)
        if not payload:
            return None
        first = payload[0]
        label = ", ".join(
            [
                str(part).strip()
                for part in [first.get("name"), first.get("state"), first.get("country")]
                if part
            ]
        )
        return {
            "latitude": float(first["lat"]),
            "longitude": float(first["lon"]),
            "label": label or cleaned,
        }
    except Exception:
        return None


def build_live_environment_payload(latitude: float, longitude: float, location_name: Optional[str] = None):
    weather_url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,rain,is_day",
                "timezone": "auto",
            }
        )
    )
    air_url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality?"
        + urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "us_aqi,pm2_5",
                "timezone": "auto",
            }
        )
    )

    weather_payload = {}
    air_payload = {}
    weather_error = None
    air_error = None

    try:
        weather_payload = http_get_json(weather_url)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        weather_error = str(exc)

    try:
        air_payload = http_get_json(air_url)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        air_error = str(exc)

    if weather_error and air_error:
        raise HTTPException(
            status_code=502,
            detail=f"Live environment fetch failed: weather={weather_error}; air_quality={air_error}",
        )

    current_weather = weather_payload.get("current", {}) or {}
    current_air = air_payload.get("current", {}) or {}

    temperature = current_weather.get("temperature_2m")
    humidity = current_weather.get("relative_humidity_2m")
    precipitation = current_weather.get("precipitation")
    rain_mm = current_weather.get("rain")
    air_aqi = current_air.get("us_aqi")
    pm2_5 = current_air.get("pm2_5")

    rain_percent = 0
    if rain_mm is not None:
        rain_percent = max(0, min(100, int(round(float(rain_mm) * 8))))
    elif precipitation is not None:
        rain_percent = max(0, min(100, int(round(float(precipitation) * 8))))

    air_status = classify_live_air_quality(air_aqi)
    rain_status = classify_live_rain(rain_mm, precipitation)
    timestamp = current_weather.get("time") or current_air.get("time") or datetime.utcnow().isoformat()

    return {
        "location": {
            "label": location_name or reverse_geocode_label(latitude, longitude),
            "latitude": latitude,
            "longitude": longitude,
            "timezone": weather_payload.get("timezone") or air_payload.get("timezone"),
        },
        "source": {
            "weather": "Open-Meteo Forecast API",
            "air_quality": "Open-Meteo Air Quality API",
        },
        "source_status": {
            "weather": "ok" if not weather_error else "unavailable",
            "air_quality": "ok" if not air_error else "unavailable",
        },
        "source_errors": {
            "weather": weather_error,
            "air_quality": air_error,
        },
        "timestamp": timestamp,
        "last_updated": timestamp,
        "temperature": temperature,
        "humidity": humidity,
        "air_smoke": air_aqi,
        "air_pm25": pm2_5,
        "air_quality": classify_air_quality_label(air_aqi),
        "rain_percent": rain_percent,
        "rain_mm": rain_mm,
        "precipitation_mm": precipitation,
        "rain_intensity": classify_rain_intensity_label(rain_mm, precipitation),
        "is_day": current_weather.get("is_day"),
        "air_status": air_status,
        "temp_status": classify_live_temperature(temperature, humidity),
        "rain_status": rain_status,
    }


def build_openweather_environment_payload(latitude: float, longitude: float, location_name: Optional[str] = None):
    if not OPENWEATHERMAP_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Unable to fetch live data",
        )

    weather_url = (
        "https://api.openweathermap.org/data/2.5/weather?"
        + urlencode(
            {
                "lat": latitude,
                "lon": longitude,
                "appid": OPENWEATHERMAP_API_KEY,
                "units": "metric",
            }
        )
    )
    air_url = (
        "https://api.openweathermap.org/data/2.5/air_pollution?"
        + urlencode(
            {
                "lat": latitude,
                "lon": longitude,
                "appid": OPENWEATHERMAP_API_KEY,
            }
        )
    )

    try:
        print(f"[OPENWEATHER] Fetching weather for: lat={latitude}, lon={longitude}, location={location_name}")
        weather_payload = http_get_json(weather_url)
        print(f"[OPENWEATHER] Weather API response: {weather_payload}")
        air_payload = http_get_json(air_url)
        print(f"[OPENWEATHER] AQI response: {air_payload}")
    except HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="ignore")
        print(f"[OPENWEATHER] API ERROR ({exc.code}): {error_text}")
        raise HTTPException(status_code=502, detail="Weather API failed")
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        print(f"[OPENWEATHER] API ERROR: {exc}")
        raise HTTPException(status_code=502, detail=f"External weather lookup failed: {exc}")

    weather_items = weather_payload.get("weather") or [{}]
    primary_weather = weather_items[0] or {}
    weather_main = primary_weather.get("main")
    rain_data = weather_payload.get("rain") or {}
    rain_one_hour = _safe_float(rain_data.get("1h"))
    rain_three_hour = _safe_float(rain_data.get("3h"))
    aqi_list = air_payload.get("list") or [{}]
    current_air = aqi_list[0] or {}
    aqi_index = ((current_air.get("main") or {}).get("aqi"))
    aqi_score = normalize_openweather_aqi_score(aqi_index)
    pm_components = current_air.get("components") or {}

    timestamp_source = weather_payload.get("dt")
    if timestamp_source is not None:
        timestamp = datetime.utcfromtimestamp(int(timestamp_source)).isoformat()
    else:
        timestamp = datetime.utcnow().isoformat()

    rain_intensity = classify_openweather_rain_intensity(weather_main, rain_one_hour, rain_three_hour)
    rain_percent = None
    if rain_one_hour is not None:
        rain_percent = max(0, min(100, int(round(rain_one_hour * 10))))
    elif rain_three_hour is not None:
        rain_percent = max(0, min(100, int(round((rain_three_hour / 3) * 10))))

    label = location_name or ", ".join(
        [
            str(part).strip()
            for part in [
                weather_payload.get("name"),
                ((weather_payload.get("sys") or {}).get("country")),
            ]
            if part
        ]
    )

    payload = {
        "location": {
            "label": label or reverse_geocode_label(latitude, longitude),
            "latitude": latitude,
            "longitude": longitude,
            "timezone": weather_payload.get("timezone"),
        },
        "temperature": (weather_payload.get("main") or {}).get("temp"),
        "humidity": (weather_payload.get("main") or {}).get("humidity"),
        "air_smoke": aqi_score,
        "air_quality": classify_public_air_quality(aqi_score),
        "air_status": classify_public_air_quality(aqi_score),
        "air_pm25": pm_components.get("pm2_5"),
        "rain_intensity": rain_intensity,
        "rain_percent": rain_percent,
        "rain_mm": rain_one_hour if rain_one_hour is not None else rain_three_hour,
        "rain_status": rain_intensity,
        "temp_status": weather_main or "Weather",
        "timestamp": timestamp,
        "last_updated": timestamp,
        "source": {
            "weather": "OpenWeatherMap Current Weather API",
            "air_quality": "OpenWeatherMap Air Pollution API",
        },
        "source_status": {
            "weather": "ok",
            "air_quality": "ok",
        },
    }
    return validate_public_payload(payload)


def _openweather_timezone(offset_seconds: Optional[int]):
    try:
        return timezone(timedelta(seconds=int(offset_seconds or 0)))
    except Exception:
        return timezone.utc


def _openweather_local_datetime(unix_timestamp: Optional[int], offset_seconds: Optional[int]):
    if unix_timestamp is None:
        return None
    return datetime.fromtimestamp(int(unix_timestamp), tz=timezone.utc).astimezone(
        _openweather_timezone(offset_seconds)
    )


def _openweather_hour_label(value: Optional[datetime]) -> str:
    if value is None:
        return "--"
    return value.strftime("%I %p").lstrip("0")


def _openweather_rain_percent(rain_one_hour: Optional[float], rain_three_hour: Optional[float]) -> int:
    if rain_one_hour is not None:
        return max(0, min(100, int(round(float(rain_one_hour) * 10))))
    if rain_three_hour is not None:
        return max(0, min(100, int(round((float(rain_three_hour) / 3.0) * 10))))
    return 0


def _openweather_air_score_from_payload(item: Optional[dict]) -> Optional[int]:
    main = (item or {}).get("main") or {}
    aqi_index = main.get("aqi")
    return normalize_openweather_aqi_score(aqi_index)


def _openweather_weather_point_from_current(payload: dict, offset_seconds: Optional[int]) -> dict:
    rain = payload.get("rain") or {}
    rain_one_hour = _safe_float(rain.get("1h"))
    rain_three_hour = _safe_float(rain.get("3h"))
    dt_value = payload.get("dt")
    local_dt = _openweather_local_datetime(dt_value, offset_seconds)
    return {
        "timestamp": dt_value,
        "local_iso": local_dt.isoformat() if local_dt else None,
        "local_hour": local_dt.hour if local_dt else None,
        "temperature": _safe_float(((payload.get("main") or {}).get("temp"))),
        "temperature_min": _safe_float(((payload.get("main") or {}).get("temp_min"))),
        "temperature_max": _safe_float(((payload.get("main") or {}).get("temp_max"))),
        "humidity": _safe_float(((payload.get("main") or {}).get("humidity"))),
        "rain_percent": _openweather_rain_percent(rain_one_hour, rain_three_hour),
        "rain_status": classify_openweather_rain_intensity(
            ((payload.get("weather") or [{}])[0] or {}).get("main"),
            rain_one_hour,
            rain_three_hour,
        ),
    }


def _openweather_weather_point_from_forecast(item: dict, offset_seconds: Optional[int]) -> dict:
    rain = item.get("rain") or {}
    rain_three_hour = _safe_float(rain.get("3h"))
    dt_value = item.get("dt")
    local_dt = _openweather_local_datetime(dt_value, offset_seconds)
    weather_main = ((item.get("weather") or [{}])[0] or {}).get("main")
    return {
        "timestamp": dt_value,
        "local_iso": local_dt.isoformat() if local_dt else None,
        "local_hour": local_dt.hour if local_dt else None,
        "temperature": _safe_float(((item.get("main") or {}).get("temp"))),
        "temperature_min": _safe_float(((item.get("main") or {}).get("temp_min"))),
        "temperature_max": _safe_float(((item.get("main") or {}).get("temp_max"))),
        "humidity": _safe_float(((item.get("main") or {}).get("humidity"))),
        "rain_percent": _openweather_rain_percent(None, rain_three_hour),
        "rain_status": classify_openweather_rain_intensity(weather_main, None, rain_three_hour),
    }


def _openweather_air_point(item: Optional[dict], offset_seconds: Optional[int]) -> Optional[dict]:
    if not item:
        return None
    dt_value = item.get("dt")
    local_dt = _openweather_local_datetime(dt_value, offset_seconds)
    aqi_score = _openweather_air_score_from_payload(item)
    return {
        "timestamp": dt_value,
        "local_iso": local_dt.isoformat() if local_dt else None,
        "air_smoke": aqi_score,
        "air_status": classify_public_air_quality(aqi_score),
    }


def _select_closest_air_point(air_points: list[dict], target_timestamp: int) -> Optional[dict]:
    if not air_points:
        return None
    return min(
        air_points,
        key=lambda item: abs(int(item.get("timestamp") or 0) - int(target_timestamp)),
    )


def _select_timeline_weather_point(
    weather_points: list[dict],
    target_local_hour: int,
    offset_seconds: Optional[int],
    max_distance_seconds: int = 3 * 3600,
) -> Optional[dict]:
    candidates = [point for point in weather_points if point.get("local_hour") is not None]
    if not candidates:
        return None

    desired_candidates = [point for point in candidates if int(point.get("local_hour")) == int(target_local_hour)]
    if desired_candidates:
        return desired_candidates[0]

    target_seconds = target_local_hour * 3600

    def score(point: dict):
        local_dt = _openweather_local_datetime(point.get("timestamp"), offset_seconds)
        if local_dt is None:
            return 10**9
        return abs((local_dt.hour * 3600 + local_dt.minute * 60) - target_seconds)

    closest = min(candidates, key=score)
    if score(closest) > max_distance_seconds:
        return None
    return closest


def build_openweather_timeline_payload(latitude: float, longitude: float, location_name: Optional[str] = None):
    weather_url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,rain,is_day",
                "hourly": "temperature_2m,relative_humidity_2m,precipitation,rain",
                "daily": "temperature_2m_min,temperature_2m_max",
                "timezone": "auto",
                "past_days": 1,
                "forecast_days": 2,
            }
        )
    )
    air_url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality?"
        + urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "us_aqi",
                "hourly": "us_aqi",
                "timezone": "auto",
                "past_days": 1,
                "forecast_days": 2,
            }
        )
    )

    try:
        weather_payload = http_get_json(weather_url)
        air_payload = http_get_json(air_url)
    except HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Weather API failed with status {exc.code}")
    except (URLError, TimeoutError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Timeline fetch failed: {exc}")

    current_weather = weather_payload.get("current", {}) or {}
    current_time_str = current_weather.get("time")
    if not current_time_str:
        raise HTTPException(status_code=502, detail="Timeline source returned no current time")

    current_local = datetime.fromisoformat(current_time_str)
    selected_date = current_local.date()

    weather_hourly = weather_payload.get("hourly", {}) or {}
    weather_times = weather_hourly.get("time") or []
    temperature_series = weather_hourly.get("temperature_2m") or []
    humidity_series = weather_hourly.get("relative_humidity_2m") or []
    precipitation_series = weather_hourly.get("precipitation") or []
    rain_series = weather_hourly.get("rain") or []

    air_hourly = air_payload.get("hourly", {}) or {}
    air_times = air_hourly.get("time") or []
    air_aqi_series = air_hourly.get("us_aqi") or []

    air_by_time = {}
    for index, time_value in enumerate(air_times):
        air_by_time[time_value] = _safe_float(air_aqi_series[index]) if index < len(air_aqi_series) else None

    hourly_points = []
    for index, time_value in enumerate(weather_times):
        if index >= len(temperature_series):
            continue
        local_dt = datetime.fromisoformat(time_value)
        if local_dt.date() != selected_date:
            continue
        rain_mm = _safe_float(rain_series[index]) if index < len(rain_series) else None
        precipitation_mm = _safe_float(precipitation_series[index]) if index < len(precipitation_series) else None
        air_value = air_by_time.get(time_value)
        hourly_points.append(
            {
                "time": time_value,
                "local_dt": local_dt,
                "hour": local_dt.hour,
                "temperature": _safe_float(temperature_series[index]),
                "humidity": _safe_float(humidity_series[index]) if index < len(humidity_series) else None,
                "rain_percent": max(
                    0,
                    min(
                        100,
                        int(round(((rain_mm if rain_mm is not None else precipitation_mm) or 0) * 8)),
                    ),
                ),
                "rain_status": classify_live_rain(rain_mm, precipitation_mm),
                "air_smoke": air_value,
                "air_status": classify_public_air_quality(air_value),
            }
        )

    if not hourly_points:
        raise HTTPException(status_code=502, detail="No hourly data available for the selected day")

    def closest_point_for_hour(target_hour: int):
        same_hour = [point for point in hourly_points if int(point["hour"]) == int(target_hour)]
        if same_hour:
            return same_hour[0]
        return min(hourly_points, key=lambda point: abs(int(point["hour"]) - int(target_hour)))

    current_air = (air_payload.get("current") or {}).get("us_aqi")
    current_rain_mm = _safe_float(current_weather.get("rain"))
    current_precipitation = _safe_float(current_weather.get("precipitation"))
    current_point = {
        "time": current_time_str,
        "local_dt": current_local,
        "hour": current_local.hour,
        "temperature": _safe_float(current_weather.get("temperature_2m")),
        "humidity": _safe_float(current_weather.get("relative_humidity_2m")),
        "rain_percent": max(
            0,
            min(
                100,
                int(round(((current_rain_mm if current_rain_mm is not None else current_precipitation) or 0) * 8)),
            ),
        ),
        "rain_status": classify_live_rain(current_rain_mm, current_precipitation),
        "air_smoke": _safe_float(current_air),
        "air_status": classify_public_air_quality(_safe_float(current_air)),
    }

    slot_specs = [
        {"key": "09", "label": "9 AM", "hour": 9},
        {"key": "12", "label": "12 PM", "hour": 12},
        {"key": "14", "label": "2 PM", "hour": 14},
        {"key": "17", "label": "5 PM", "hour": 17},
        {"key": "current", "label": "Current", "hour": current_local.hour},
    ]

    slots = []
    for spec in slot_specs:
        selected = current_point if spec["key"] == "current" else closest_point_for_hour(spec["hour"])
        source_dt = selected.get("local_dt")
        slots.append(
            {
                "key": spec["key"],
                "label": spec["label"],
                "source_label": "Now" if spec["key"] == "current" else source_dt.strftime("%-I %p") if os.name != "nt" else source_dt.strftime("%#I %p"),
                "timestamp": selected.get("time"),
                "temperature": selected.get("temperature"),
                "humidity": selected.get("humidity"),
                "rain_percent": selected.get("rain_percent"),
                "rain_status": selected.get("rain_status"),
                "air_smoke": selected.get("air_smoke"),
                "air_status": selected.get("air_status"),
            }
        )

    daily = weather_payload.get("daily", {}) or {}
    daily_times = daily.get("time") or []
    daily_temp_min = daily.get("temperature_2m_min") or []
    daily_temp_max = daily.get("temperature_2m_max") or []
    day_min = None
    day_max = None
    for index, day_value in enumerate(daily_times):
        if str(day_value) == selected_date.isoformat():
            day_min = _safe_float(daily_temp_min[index]) if index < len(daily_temp_min) else None
            day_max = _safe_float(daily_temp_max[index]) if index < len(daily_temp_max) else None
            break

    def metric_range(values):
        numeric_values = [float(value) for value in values if value is not None]
        if not numeric_values:
            return {"min": None, "max": None}
        return {"min": round(min(numeric_values), 1), "max": round(max(numeric_values), 1)}

    humidity_range = metric_range([point.get("humidity") for point in hourly_points])
    rain_range = metric_range([point.get("rain_percent") for point in hourly_points])
    air_range = metric_range([point.get("air_smoke") for point in hourly_points])

    return {
        "location": {
            "label": location_name or reverse_geocode_label(latitude, longitude),
            "latitude": latitude,
            "longitude": longitude,
            "timezone": weather_payload.get("timezone"),
        },
        "date": selected_date.isoformat(),
        "current_timestamp": current_time_str,
        "slots": slots,
        "ranges": {
            "temperature": {
                "min": day_min if day_min is not None else metric_range([point.get("temperature") for point in hourly_points])["min"],
                "max": day_max if day_max is not None else metric_range([point.get("temperature") for point in hourly_points])["max"],
            },
            "humidity": humidity_range,
            "rain": rain_range,
            "air": air_range,
        },
    }


DEFAULT_IOT_LIVE_LAT = float(os.getenv("IOT_LIVE_LAT", "13.0827"))
DEFAULT_IOT_LIVE_LON = float(os.getenv("IOT_LIVE_LON", "77.5877"))


def fetch_weather(lat: float, lon: float) -> dict:
    if not OPENWEATHERMAP_API_KEY:
        raise HTTPException(status_code=503, detail="OpenWeather API key is not configured")

    url = (
        "https://api.openweathermap.org/data/2.5/weather?"
        + urlencode(
            {
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHERMAP_API_KEY,
                "units": "metric",
            }
        )
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"OpenWeather request failed: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"OpenWeather returned invalid JSON: {exc}")

    timestamp_source = data.get("dt")
    if timestamp_source is not None:
        timestamp = datetime.utcfromtimestamp(int(timestamp_source)).isoformat()
    else:
        timestamp = datetime.utcnow().isoformat()

    return {
        "air": {
            "live_value": (_safe_float(data.get("visibility")) or 1000) / 100,
            "status": data.get("weather", [{}])[0].get("main", "Unknown"),
            "trend": "No trend",
        },
        "temperature": {
            "live_value": _safe_float((data.get("main") or {}).get("temp")),
            "status": "Live",
        },
        "humidity": {
            "live_value": _safe_float((data.get("main") or {}).get("humidity")),
            "status": "Live",
        },
        "rain": {
            "live_value": _safe_float(((data.get("rain") or {}).get("1h"))) or 0,
            "status": data.get("weather", [{}])[0].get("main", "None"),
        },
        "timestamp": timestamp,
        "source": "OpenWeather",
        "coordinates": {
            "lat": lat,
            "lon": lon,
        },
    }


@app.get("/iot/location-search")
def search_iot_location(query: str, count: int = 5):
    cleaned = sanitize_text_input(query)
    if len(cleaned) < 2:
        return {"count": 0, "results": []}
    if len(cleaned) > 120:
        raise HTTPException(status_code=400, detail="Search query is too long")

    def normalize_location_result(item: dict):
        label_parts = [item.get("name"), item.get("admin1"), item.get("country")]
        label = ", ".join([str(part).strip() for part in label_parts if part])
        return {
            "name": item.get("name"),
            "label": label or item.get("name") or "Selected location",
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
            "country": item.get("country"),
            "admin1": item.get("admin1"),
            "timezone": item.get("timezone"),
        }

    safe_count = max(1, min(count, 10))
    url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        + urlencode({"name": cleaned, "count": safe_count, "language": "en", "format": "json"})
    )
    try:
        payload = http_get_json(url)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Location lookup failed: {exc}")

    results = [normalize_location_result(item) for item in payload.get("results", []) or []]

    if len(results) < safe_count:
        fallback_url = (
            "https://nominatim.openstreetmap.org/search?"
            + urlencode(
                {
                    "q": cleaned,
                    "format": "jsonv2",
                    "addressdetails": 1,
                    "limit": safe_count,
                }
            )
        )
        try:
            fallback_payload = http_get_json(fallback_url)
            seen = {
                (
                    round(float(item["latitude"]), 4),
                    round(float(item["longitude"]), 4),
                    item["label"].lower(),
                )
                for item in results
                if item.get("latitude") is not None and item.get("longitude") is not None
            }
            for item in fallback_payload or []:
                address = item.get("address", {}) or {}
                name = (
                    address.get("city")
                    or address.get("town")
                    or address.get("village")
                    or address.get("suburb")
                    or item.get("name")
                    or str(item.get("display_name", "")).split(",")[0].strip()
                )
                label_parts = [
                    name,
                    address.get("state") or address.get("county"),
                    address.get("country"),
                ]
                label = ", ".join([str(part).strip() for part in label_parts if part])
                lat = item.get("lat")
                lon = item.get("lon")
                if lat is None or lon is None:
                    continue
                dedupe_key = (round(float(lat), 4), round(float(lon), 4), label.lower())
                if dedupe_key in seen:
                    continue
                results.append(
                    {
                        "name": name or label,
                        "label": label or item.get("display_name") or "Selected location",
                        "latitude": float(lat),
                        "longitude": float(lon),
                        "country": address.get("country"),
                        "admin1": address.get("state") or address.get("county"),
                        "timezone": None,
                    }
                )
                seen.add(dedupe_key)
                if len(results) >= safe_count:
                    break
        except Exception:
            pass

    return {"count": len(results), "results": results}


@app.get("/iot/live-environment")
def get_live_environment(latitude: float, longitude: float, location_name: Optional[str] = None):
    if OPENWEATHERMAP_API_KEY:
        try:
            payload = build_openweather_environment_payload(latitude, longitude, location_name)
            response_payload = build_environment_response("success", payload, "openweathermap")
            print("API response sent: /iot/live-environment")
            return response_payload
        except HTTPException:
            pass
    payload = central_sensor_engine.get_environment_payload()
    response_payload = build_environment_response("success", payload, "central_sensor_engine")
    print("API response sent: /iot/live-environment")
    return response_payload


@app.post("/api/update-data")
def update_location_sensor_data(data: SensorData):
    payload = data.dict()
    payload["timestamp"] = payload.get("timestamp") or datetime.utcnow().isoformat()

    if not payload.get("location") and (payload.get("latitude") is None or payload.get("longitude") is None):
        raise HTTPException(
            status_code=400,
            detail="Sensor update must include a location name or latitude/longitude.",
        )

    if not payload.get("location") and payload.get("latitude") is not None and payload.get("longitude") is not None:
        payload["location"] = reverse_geocode_label(float(payload["latitude"]), float(payload["longitude"]))

    payload, snapshot, new_events = process_sensor_ingest(payload)

    return {
        "message": "Sensor data updated successfully",
        "location": payload.get("location"),
        "timestamp": payload["timestamp"],
        "overall_status": snapshot.get("overall_status"),
        "priority": snapshot.get("priority"),
        "new_alerts": len(new_events),
    }


@app.get("/api/location-data")
def get_location_data(
    response: Response,
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    payload = central_sensor_engine.get_environment_payload()
    print("API response sent: /api/location-data")
    return build_environment_response("success", payload, "central_sensor_engine")


@app.get("/api/sensors/live")
def get_sensors_live(
    response: Response,
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    payload = central_sensor_engine.get_live_payload()
    print("API response sent: /api/sensors/live")
    return payload


@app.get("/api/sensors/history")
def get_sensors_history(
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    limit: int = 200,
):
    safe_limit = max(1, min(limit, 2000))
    rows = central_sensor_engine.get_history(limit=safe_limit)
    payload = {
        "status": "success",
        "source": "central_sensor_engine",
        "count": len(rows),
        "data": rows,
        "locations": central_sensor_engine.get_live_payload()["locations"],
    }
    print("API response sent: /api/sensors/history")
    return payload


@app.get("/reports")
def get_precomputed_reports(range: str = "30min"):
    normalized = REPORT_RANGE_ALIASES.get(str(range or "").strip().lower())
    if not normalized:
        raise HTTPException(status_code=400, detail="range must be one of 5min, 30min, or 1day")
    payload = central_sensor_engine.get_reports(normalized)
    payload["status"] = "success"
    payload["source"] = "central_sensor_engine"
    return payload


@app.get("/api/incidents")
def get_incident_analytics(
    range: str = "30m",
    compare_previous: bool = False,
    date: Optional[str] = None,
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
):
    normalized_range = str(range or "30m").strip().lower()
    if normalized_range == "custom":
        normalized = "1day"
    else:
        normalized = REPORT_RANGE_ALIASES.get(normalized_range)
    if not normalized:
        raise HTTPException(status_code=400, detail="range must be one of 5m, 30m, 1d, or custom")
    payload = central_sensor_engine.get_reports(normalized)
    payload.update(
        {
            "status": "success",
            "source": "central_sensor_engine",
            "selected_date": date,
        }
    )
    print("API response sent: /api/incidents")
    return payload


@app.get("/api/alerts")
def get_monitoring_alerts(limit: int = 100, status: Optional[str] = None):
    safe_limit = max(1, min(limit, 500))
    rows = monitoring_alerts
    if status:
        normalized = status.strip().lower()
        rows = [item for item in rows if str(item.get("status", "")).strip().lower() == normalized]
    return {"count": min(len(rows), safe_limit), "alerts": rows[-safe_limit:][::-1]}


@app.post("/api/alerts")
def create_monitoring_alert(payload: MonitoringAlertCreatePayload):
    severity = (payload.severity or "").strip().upper()
    if severity not in STATUS_TO_PRIORITY:
        raise HTTPException(status_code=400, detail="Severity must be SAFE, WARNING, DANGER, or CRITICAL")

    alert = {
        "id": str(uuid.uuid4()),
        "kind": "manual",
        "scope": "sensor",
        "sensor_id": payload.sensor_id.strip(),
        "sensor_label": payload.sensor_label.strip(),
        "severity": severity.title(),
        "priority": STATUS_TO_PRIORITY[severity],
        "status": "Open",
        "location": (payload.location or "").strip() or None,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "value": (payload.value or "").strip(),
        "note": (payload.note or "").strip(),
        "predicted_status_5_min": (payload.predicted_status_5_min or severity).strip().title(),
        "created_at": iso_now(),
        "updated_at": iso_now(),
    }
    append_monitoring_alert(alert)
    return {"message": "Alert created", "alert": alert}


@app.patch("/api/alerts/{alert_id}")
def update_monitoring_alert(alert_id: str, payload: MonitoringAlertAdminPayload):
    should_resolve = payload.resolve or ((payload.status or "").strip().lower() == "resolved")
    found = apply_admin_action(
        monitoring_alerts,
        alert_id,
        assigned_department=(payload.assigned_department or "").strip() or None,
        resolved=should_resolve,
    )
    if found is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    if payload.status and not payload.resolve:
        found["status"] = payload.status.strip().title()
        found["updated_at"] = iso_now()
    save_all_monitoring_alerts()
    reset_snapshot = None
    if should_resolve:
        reset = central_sensor_engine.reset()
        sync_globals_from_central_sensor_engine()
        rebuild_incident_records_from_sensor_history()
        global latest_sensor_data
        global latest_iot_data
        latest_sensor_data = reset.copy()
        latest_iot_data = build_latest_iot_snapshot(reset)
        reset_snapshot = reset
    return {"message": "Alert updated", "alert": found, "reset_snapshot": reset_snapshot}


@app.post("/api/sensors/reset")
def reset_sensor_location(payload: SensorResetPayload):
    reset = central_sensor_engine.reset()
    sync_globals_from_central_sensor_engine()
    rebuild_incident_records_from_sensor_history()
    global latest_sensor_data
    latest_sensor_data = reset.copy()
    return {"message": "Sensor location reset", "snapshot": reset}


@app.get("/api/test-weather")
def test_weather(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location: Optional[str] = None,
):
    try:
        resolved_latitude = latitude
        resolved_longitude = longitude
        resolved_label = (location or "").strip() or None

        if resolved_latitude is None or resolved_longitude is None:
            geocoded = geocode_location_name_openweather(location or "") or geocode_location_name(location or "")
            if not geocoded:
                return {
                    "success": False,
                    "message": "Unable to geocode location",
                }
            resolved_latitude = float(geocoded["latitude"])
            resolved_longitude = float(geocoded["longitude"])
            resolved_label = resolved_label or geocoded.get("label")

        payload = build_openweather_environment_payload(resolved_latitude, resolved_longitude, resolved_label)
        return {
            "success": True,
            "location": payload.get("location"),
            "raw": payload,
        }
    except Exception as error:
        print(f"[TEST-WEATHER] Error: {error}")
        return {
            "success": False,
            "message": str(error),
        }


if __name__ == "__main__":
    print("Server running on http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
