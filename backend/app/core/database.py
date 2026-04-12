import os

import oracledb
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "urban_sentinel.db")
load_dotenv(os.path.join(BASE_DIR, ".env"))


def is_oracle_url(database_url: str) -> bool:
    return database_url.strip().lower().startswith("oracle+oracledb://")


def maybe_enable_oracle_thick_mode() -> None:
    explicit_url = os.getenv("DATABASE_URL", "").strip()
    db_engine = os.getenv("DB_ENGINE", "sqlite").strip().lower()
    if db_engine != "oracle" and not is_oracle_url(explicit_url):
        return

    thick_mode_flag = os.getenv("ORACLE_THICK_MODE", "true").strip().lower()
    if thick_mode_flag not in {"1", "true", "yes", "on"}:
        return

    if getattr(oracledb, "is_thin_mode", None) and not oracledb.is_thin_mode():
        return

    lib_dir = os.getenv("ORACLE_CLIENT_LIB_DIR", "").strip() or None
    config_dir = os.getenv("TNS_ADMIN", "").strip() or None

    try:
        init_kwargs = {}
        if lib_dir:
            init_kwargs["lib_dir"] = lib_dir
        if config_dir:
            init_kwargs["config_dir"] = config_dir
        oracledb.init_oracle_client(**init_kwargs)
    except Exception as exc:
        raise RuntimeError(
            "Failed to enable Oracle thick mode. Set ORACLE_CLIENT_LIB_DIR to your "
            "Oracle Instant Client folder or Oracle client 'bin' folder."
        ) from exc


def build_database_url() -> str:
    explicit_url = os.getenv("DATABASE_URL", "").strip()
    if explicit_url:
        return explicit_url

    db_engine = os.getenv("DB_ENGINE", "sqlite").strip().lower()
    if db_engine == "oracle":
        oracle_user = os.getenv("ORACLE_USER", "").strip()
        oracle_password = os.getenv("ORACLE_PASSWORD", "").strip()
        oracle_host = os.getenv("ORACLE_HOST", "127.0.0.1").strip()
        oracle_port = os.getenv("ORACLE_PORT", "1521").strip()
        oracle_service = os.getenv("ORACLE_SERVICE_NAME", "XE").strip()

        if not oracle_user or not oracle_password:
            raise RuntimeError(
                "Oracle mode requires ORACLE_USER and ORACLE_PASSWORD to be set."
            )

        return (
            f"oracle+oracledb://{oracle_user}:{oracle_password}@{oracle_host}:{oracle_port}/"
            f"?service_name={oracle_service}"
        )

    return f"sqlite:///{DB_PATH}"


DATABASE_URL = build_database_url()
maybe_enable_oracle_thick_mode()
SQLITE_FALLBACK_URL = f"sqlite:///{DB_PATH}"


def make_engine(database_url: str):
    is_sqlite = database_url.startswith("sqlite")
    connect_args = {}
    if is_sqlite:
        connect_args = {
            "check_same_thread": False,
            "timeout": 30,
        }
    engine = create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
    if is_sqlite:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=30000")
            finally:
                cursor.close()
    return engine


def should_fallback_to_sqlite() -> bool:
    return os.getenv("DB_FALLBACK_TO_SQLITE", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def initialize_engine():
    engine = make_engine(DATABASE_URL)

    if DATABASE_URL.startswith("sqlite"):
        return engine, DATABASE_URL

    try:
        with engine.connect():
            pass
        return engine, DATABASE_URL
    except (SQLAlchemyError, RuntimeError, oracledb.Error) as exc:
        if not should_fallback_to_sqlite():
            raise

        fallback_engine = make_engine(SQLITE_FALLBACK_URL)
        print(
            "Oracle database connection failed during startup; falling back to SQLite. "
            f"Reason: {exc}"
        )
        return fallback_engine, SQLITE_FALLBACK_URL


engine, ACTIVE_DATABASE_URL = initialize_engine()
IS_SQLITE = ACTIVE_DATABASE_URL.startswith("sqlite")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
