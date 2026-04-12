SET LINESIZE 220
SET PAGESIZE 200

PROMPT === USERS ===
COLUMN full_name FORMAT A20
COLUMN first_name FORMAT A12
COLUMN last_name FORMAT A12
COLUMN email FORMAT A35
COLUMN phone FORMAT A15
COLUMN registration_source FORMAT A22
SELECT id, full_name, first_name, last_name, email, phone, registration_source, is_active, email_verified
FROM users
ORDER BY id;

PROMPT === ADMIN_USERS ===
COLUMN username FORMAT A25
COLUMN full_name FORMAT A25
COLUMN email FORMAT A35
SELECT id, username, full_name, email, is_active, created_at
FROM admin_users
ORDER BY id;

PROMPT === WORKERS ===
COLUMN worker_id FORMAT A20
COLUMN department FORMAT A20
SELECT id, worker_id, department, created_by_admin_id, is_active, last_login_at, created_at
FROM workers
ORDER BY id;

PROMPT === ISSUES ===
COLUMN complaint_number FORMAT A15
COLUMN title FORMAT A25
COLUMN category FORMAT A18
COLUMN status FORMAT A18
COLUMN location FORMAT A35
COLUMN assigned_department FORMAT A20
SELECT id, user_id, complaint_number, title, category, status, assigned_department, created_at
FROM issues
ORDER BY id;

PROMPT === WORKER_RESET_REQUESTS ===
COLUMN department FORMAT A20
COLUMN status FORMAT A18
SELECT id, worker_id, department, status, requested_at, resolved_at
FROM worker_reset_requests
ORDER BY id;

PROMPT === DEVICES ===
COLUMN device_identifier FORMAT A30
COLUMN device_name FORMAT A25
COLUMN device_type FORMAT A20
COLUMN login_email FORMAT A35
COLUMN login_phone FORMAT A15
SELECT id, user_id, device_identifier, device_name, device_type, login_email, login_phone, is_active, created_at
FROM devices
ORDER BY id;

PROMPT === SENSOR_READINGS ===
COLUMN device_identifier FORMAT A25
COLUMN sensor_name FORMAT A20
COLUMN sensor_label FORMAT A22
COLUMN reading_text FORMAT A15
COLUMN status FORMAT A20
SELECT id, device_identifier, sensor_name, sensor_label, current_reading, reading_text, status, recorded_at
FROM sensor_readings
ORDER BY id;
