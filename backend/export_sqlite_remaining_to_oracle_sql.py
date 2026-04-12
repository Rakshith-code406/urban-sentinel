import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SQLITE_DB_PATH = BASE_DIR / "urban_sentinel.db"
OUTPUT_SQL_PATH = BASE_DIR / "oracle_migrate_remaining.sql"


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
    return "TO_TIMESTAMP(" + sql_string(value) + ", 'YYYY-MM-DD HH24:MI:SS.FF6')"


def fetch_rows(conn: sqlite3.Connection, table_name: str) -> list[sqlite3.Row]:
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name} ORDER BY id")
    return cur.fetchall()


def build_admin_merge(row: sqlite3.Row) -> str:
    return f"""MERGE INTO admin_users a
USING (SELECT {sql_string(row["username"])} AS username FROM dual) src
ON (a.username = src.username)
WHEN MATCHED THEN UPDATE SET
    a.password_hash = {sql_string(row["password_hash"])},
    a.full_name = {sql_string(row["full_name"])},
    a.email = {sql_string(row["email"])},
    a.is_active = {sql_number(row["is_active"])},
    a.created_at = {sql_timestamp(row["created_at"])}
WHEN NOT MATCHED THEN INSERT (
    id, username, password_hash, full_name, email, is_active, created_at
) VALUES (
    admin_users_seq.NEXTVAL,
    {sql_string(row["username"])},
    {sql_string(row["password_hash"])},
    {sql_string(row["full_name"])},
    {sql_string(row["email"])},
    {sql_number(row["is_active"])},
    {sql_timestamp(row["created_at"])}
);
"""


def build_worker_merge(row: sqlite3.Row) -> str:
    return f"""MERGE INTO workers w
USING (SELECT {sql_string(row["worker_id"])} AS worker_id FROM dual) src
ON (w.worker_id = src.worker_id)
WHEN MATCHED THEN UPDATE SET
    w.department = {sql_string(row["department"])},
    w.password_hash = {sql_string(row["password_hash"])},
    w.password_plaintext = {sql_string(row["password_plaintext"])},
    w.created_by_admin_id = {sql_number(row["created_by_admin_id"])},
    w.is_active = {sql_number(row["is_active"])},
    w.last_login_at = {sql_timestamp(row["last_login_at"])},
    w.created_at = {sql_timestamp(row["created_at"])}
WHEN NOT MATCHED THEN INSERT (
    id, worker_id, department, password_hash, password_plaintext, created_by_admin_id, is_active, last_login_at, created_at
) VALUES (
    workers_seq.NEXTVAL,
    {sql_string(row["worker_id"])},
    {sql_string(row["department"])},
    {sql_string(row["password_hash"])},
    {sql_string(row["password_plaintext"])},
    {sql_number(row["created_by_admin_id"])},
    {sql_number(row["is_active"])},
    {sql_timestamp(row["last_login_at"])},
    {sql_timestamp(row["created_at"])}
);
"""


def build_issue_merge(row: sqlite3.Row) -> str:
    return f"""MERGE INTO issues i
USING (SELECT {sql_string(row["complaint_number"])} AS complaint_number FROM dual) src
ON (i.complaint_number = src.complaint_number)
WHEN MATCHED THEN UPDATE SET
    i.user_id = {sql_number(row["user_id"])},
    i.title = {sql_string(row["title"])},
    i.description = {sql_string(row["description"])},
    i.location = {sql_string(row["location"])},
    i.category = {sql_string(row["category"])},
    i.media_urls = {sql_string(row["media_urls"])},
    i.status = {sql_string(row["status"])},
    i.assigned_department = {sql_string(row["assigned_department"])},
    i.assignment_deadline = {sql_timestamp(row["assignment_deadline"])},
    i.assignment_duration_label = {sql_string(row["assignment_duration_label"])},
    i.assigned_by_admin_id = {sql_number(row["assigned_by_admin_id"])},
    i.worker_status = {sql_string(row["worker_status"])},
    i.worker_resolution_requested_at = {sql_timestamp(row["worker_resolution_requested_at"])},
    i.created_at = {sql_timestamp(row["created_at"])},
    i.updated_at = {sql_timestamp(row["updated_at"])},
    i.assigned_at = {sql_timestamp(row["assigned_at"])}
WHEN NOT MATCHED THEN INSERT (
    id, user_id, complaint_number, title, description, location, category, media_urls, status,
    assigned_department, assignment_deadline, assignment_duration_label, assigned_by_admin_id,
    worker_status, worker_resolution_requested_at, created_at, updated_at, assigned_at
) VALUES (
    issues_seq.NEXTVAL,
    {sql_number(row["user_id"])},
    {sql_string(row["complaint_number"])},
    {sql_string(row["title"])},
    {sql_string(row["description"])},
    {sql_string(row["location"])},
    {sql_string(row["category"])},
    {sql_string(row["media_urls"])},
    {sql_string(row["status"])},
    {sql_string(row["assigned_department"])},
    {sql_timestamp(row["assignment_deadline"])},
    {sql_string(row["assignment_duration_label"])},
    {sql_number(row["assigned_by_admin_id"])},
    {sql_string(row["worker_status"])},
    {sql_timestamp(row["worker_resolution_requested_at"])},
    {sql_timestamp(row["created_at"])},
    {sql_timestamp(row["updated_at"])},
    {sql_timestamp(row["assigned_at"])}
);
"""


def build_reset_request_merge(row: sqlite3.Row) -> str:
    return f"""MERGE INTO worker_reset_requests r
USING (
    SELECT {sql_number(row["worker_id"])} AS worker_id,
           {sql_timestamp(row["requested_at"])} AS requested_at
    FROM dual
) src
ON (r.worker_id = src.worker_id AND r.requested_at = src.requested_at)
WHEN MATCHED THEN UPDATE SET
    r.department = {sql_string(row["department"])},
    r.status = {sql_string(row["status"])},
    r.resolved_at = {sql_timestamp(row["resolved_at"])}
WHEN NOT MATCHED THEN INSERT (
    id, worker_id, department, status, requested_at, resolved_at
) VALUES (
    worker_reset_requests_seq.NEXTVAL,
    {sql_number(row["worker_id"])},
    {sql_string(row["department"])},
    {sql_string(row["status"])},
    {sql_timestamp(row["requested_at"])},
    {sql_timestamp(row["resolved_at"])}
);
"""


def main() -> None:
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row

    admin_rows = fetch_rows(conn, "admin_users")
    worker_rows = fetch_rows(conn, "workers")
    issue_rows = fetch_rows(conn, "issues")
    reset_rows = fetch_rows(conn, "worker_reset_requests")

    statements = [
        "SET DEFINE OFF",
        "PROMPT === Migrating legacy SQLite admin_users, workers, issues, worker_reset_requests into Oracle ===",
    ]
    statements.extend(build_admin_merge(row).strip() for row in admin_rows)
    statements.extend(build_worker_merge(row).strip() for row in worker_rows)
    statements.extend(build_issue_merge(row).strip() for row in issue_rows)
    statements.extend(build_reset_request_merge(row).strip() for row in reset_rows)
    statements.append("COMMIT;")
    statements.append("PROMPT === Remaining table migration complete ===")
    statements.append("SELECT COUNT(*) AS admin_count FROM admin_users;")
    statements.append("SELECT COUNT(*) AS worker_count FROM workers;")
    statements.append("SELECT COUNT(*) AS issue_count FROM issues;")
    statements.append("SELECT COUNT(*) AS reset_count FROM worker_reset_requests;")

    OUTPUT_SQL_PATH.write_text("\n\n".join(statements) + "\n", encoding="utf-8")
    print(
        f"Exported admin_users={len(admin_rows)}, workers={len(worker_rows)}, "
        f"issues={len(issue_rows)}, worker_reset_requests={len(reset_rows)} "
        f"to {OUTPUT_SQL_PATH}"
    )


if __name__ == "__main__":
    main()
