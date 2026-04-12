SET PAGESIZE 200
SET LINESIZE 220
COLUMN table_name FORMAT A30
COLUMN full_name FORMAT A25
COLUMN email FORMAT A30
COLUMN phone FORMAT A18
COLUMN device_identifier FORMAT A32
COLUMN device_name FORMAT A28
COLUMN device_type FORMAT A20
COLUMN sensor_name FORMAT A22
COLUMN sensor_label FORMAT A28
COLUMN reading_text FORMAT A16
COLUMN status FORMAT A18

PROMPT === TABLES CREATED FOR URBAN SENTINEL ===
SELECT table_name
FROM user_tables
WHERE table_name IN (
  'USERS',
  'ADMIN_USERS',
  'WORKERS',
  'ISSUES',
  'WORKER_RESET_REQUESTS',
  'DEVICES',
  'SENSOR_READINGS'
)
ORDER BY table_name;

PROMPT === REGISTERED USERS ===
SELECT id, full_name, email, phone, registration_source, registered_device_identifier
FROM users
ORDER BY id;

PROMPT === REGISTERED DEVICES ===
SELECT id, user_id, device_identifier, device_name, device_type, login_email, login_phone, last_seen_at
FROM devices
ORDER BY id;

PROMPT === LIVE SENSOR READING ROWS ===
SELECT id, device_identifier, sensor_name, sensor_label, current_reading, reading_text, status, recorded_at
FROM sensor_readings
ORDER BY id;
