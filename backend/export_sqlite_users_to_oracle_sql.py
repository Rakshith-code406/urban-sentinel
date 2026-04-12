import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SQLITE_DB_PATH = BASE_DIR / "urban_sentinel.db"
OUTPUT_SQL_PATH = BASE_DIR / "oracle_migrate_users.sql"


def sql_string(value: str | None) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def sql_number(value) -> str:
    if value is None:
        return "NULL"
    return str(int(value))


def sql_timestamp(value: str | None) -> str:
    if not value:
        return "NULL"
    return (
        "TO_TIMESTAMP("
        + sql_string(value)
        + ", 'YYYY-MM-DD HH24:MI:SS.FF6')"
    )


def build_merge_sql(row: sqlite3.Row) -> str:
    full_name = row["full_name"]
    email = row["email"]
    phone = row["phone"]
    password_hash = row["password_hash"]
    is_active = row["is_active"]
    reset_code_hash = row["reset_code_hash"]
    reset_code_expires_at = row["reset_code_expires_at"]
    last_login_at = row["last_login_at"]
    created_at = row["created_at"]
    email_verified = row["email_verified"] if "email_verified" in row.keys() else 0
    email_verification_code_hash = (
        row["email_verification_code_hash"]
        if "email_verification_code_hash" in row.keys()
        else None
    )
    email_verification_expires_at = (
        row["email_verification_expires_at"]
        if "email_verification_expires_at" in row.keys()
        else None
    )

    return f"""MERGE INTO users u
USING (SELECT {sql_string(email)} AS email FROM dual) src
ON (u.email = src.email)
WHEN MATCHED THEN UPDATE SET
    u.full_name = {sql_string(full_name)},
    u.phone = {sql_string(phone)},
    u.password_hash = {sql_string(password_hash)},
    u.is_active = {sql_number(is_active)},
    u.reset_code_hash = {sql_string(reset_code_hash)},
    u.reset_code_expires_at = {sql_timestamp(reset_code_expires_at)},
    u.last_login_at = {sql_timestamp(last_login_at)},
    u.created_at = {sql_timestamp(created_at)},
    u.email_verified = {sql_number(email_verified)},
    u.email_verification_code_hash = {sql_string(email_verification_code_hash)},
    u.email_verification_expires_at = {sql_timestamp(email_verification_expires_at)}
WHEN NOT MATCHED THEN INSERT (
    id,
    full_name,
    email,
    phone,
    password_hash,
    is_active,
    reset_code_hash,
    reset_code_expires_at,
    last_login_at,
    created_at,
    registration_source,
    email_verified,
    email_verification_code_hash,
    email_verification_expires_at
) VALUES (
    users_seq.NEXTVAL,
    {sql_string(full_name)},
    {sql_string(email)},
    {sql_string(phone)},
    {sql_string(password_hash)},
    {sql_number(is_active)},
    {sql_string(reset_code_hash)},
    {sql_timestamp(reset_code_expires_at)},
    {sql_timestamp(last_login_at)},
    {sql_timestamp(created_at)},
    'legacy_sqlite_migration',
    {sql_number(email_verified)},
    {sql_string(email_verification_code_hash)},
    {sql_timestamp(email_verification_expires_at)}
);
"""


def main() -> None:
    if not SQLITE_DB_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {SQLITE_DB_PATH}")

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY id")
    rows = cur.fetchall()

    statements = [
        "SET DEFINE OFF",
        "PROMPT === Migrating legacy SQLite users into Oracle USERS table ===",
    ]
    statements.extend(build_merge_sql(row).strip() for row in rows)
    statements.append("COMMIT;")
    statements.append("PROMPT === User migration complete ===")
    statements.append("SELECT id, full_name, email, phone, registration_source, email_verified FROM users ORDER BY id;")

    OUTPUT_SQL_PATH.write_text("\n\n".join(statements) + "\n", encoding="utf-8")
    print(f"Exported {len(rows)} users to {OUTPUT_SQL_PATH}")


if __name__ == "__main__":
    main()
