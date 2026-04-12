SET DEFINE OFF

PROMPT === Migrating legacy SQLite admin_users, workers, issues, worker_reset_requests into Oracle ===

MERGE INTO admin_users a
USING (SELECT 'rakshith.e07@gmail.com' AS username FROM dual) src
ON (a.username = src.username)
WHEN MATCHED THEN UPDATE SET
    a.password_hash = '32cc62e2a83a6ceead56617ef0229d4dbc329477c89eb558f7baae103b24849d',
    a.full_name = NULL,
    a.email = NULL,
    a.is_active = 1,
    a.created_at = TO_TIMESTAMP('2026-03-10 07:02:36.191155', 'YYYY-MM-DD HH24:MI:SS.FF6')
WHEN NOT MATCHED THEN INSERT (
    id, username, password_hash, full_name, email, is_active, created_at
) VALUES (
    admin_users_seq.NEXTVAL,
    'rakshith.e07@gmail.com',
    '32cc62e2a83a6ceead56617ef0229d4dbc329477c89eb558f7baae103b24849d',
    NULL,
    NULL,
    1,
    TO_TIMESTAMP('2026-03-10 07:02:36.191155', 'YYYY-MM-DD HH24:MI:SS.FF6')
);

MERGE INTO workers w
USING (SELECT 'GB001' AS worker_id FROM dual) src
ON (w.worker_id = src.worker_id)
WHEN MATCHED THEN UPDATE SET
    w.department = 'Garbage',
    w.password_hash = '59ccb316509a0ae4df269a6e5855cc54caad9f05fd34fdc3ee07161555ff8c89',
    w.password_plaintext = NULL,
    w.created_by_admin_id = 1,
    w.is_active = 1,
    w.last_login_at = TO_TIMESTAMP('2026-04-01 09:41:10.896803', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    w.created_at = TO_TIMESTAMP('2026-03-13 17:05:37.650125', 'YYYY-MM-DD HH24:MI:SS.FF6')
WHEN NOT MATCHED THEN INSERT (
    id, worker_id, department, password_hash, password_plaintext, created_by_admin_id, is_active, last_login_at, created_at
) VALUES (
    workers_seq.NEXTVAL,
    'GB001',
    'Garbage',
    '59ccb316509a0ae4df269a6e5855cc54caad9f05fd34fdc3ee07161555ff8c89',
    NULL,
    1,
    1,
    TO_TIMESTAMP('2026-04-01 09:41:10.896803', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-13 17:05:37.650125', 'YYYY-MM-DD HH24:MI:SS.FF6')
);

MERGE INTO workers w
USING (SELECT 'RD001' AS worker_id FROM dual) src
ON (w.worker_id = src.worker_id)
WHEN MATCHED THEN UPDATE SET
    w.department = 'Road Damage',
    w.password_hash = '3fcc41ccb8209c55b817b8c6ec76016b1ff6bcb2ba899c769cd64b880e85b986',
    w.password_plaintext = NULL,
    w.created_by_admin_id = 1,
    w.is_active = 1,
    w.last_login_at = TO_TIMESTAMP('2026-03-13 17:31:22.615737', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    w.created_at = TO_TIMESTAMP('2026-03-13 17:28:45.819725', 'YYYY-MM-DD HH24:MI:SS.FF6')
WHEN NOT MATCHED THEN INSERT (
    id, worker_id, department, password_hash, password_plaintext, created_by_admin_id, is_active, last_login_at, created_at
) VALUES (
    workers_seq.NEXTVAL,
    'RD001',
    'Road Damage',
    '3fcc41ccb8209c55b817b8c6ec76016b1ff6bcb2ba899c769cd64b880e85b986',
    NULL,
    1,
    1,
    TO_TIMESTAMP('2026-03-13 17:31:22.615737', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-13 17:28:45.819725', 'YYYY-MM-DD HH24:MI:SS.FF6')
);

MERGE INTO workers w
USING (SELECT 'RD002' AS worker_id FROM dual) src
ON (w.worker_id = src.worker_id)
WHEN MATCHED THEN UPDATE SET
    w.department = 'Road Damage',
    w.password_hash = '00fb93f2531565d203fa78a4a75f68cfacf805a88c7af916bb85a364000c7df4',
    w.password_plaintext = NULL,
    w.created_by_admin_id = 1,
    w.is_active = 1,
    w.last_login_at = TO_TIMESTAMP('2026-03-14 15:56:25.830954', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    w.created_at = TO_TIMESTAMP('2026-03-14 15:51:18.510767', 'YYYY-MM-DD HH24:MI:SS.FF6')
WHEN NOT MATCHED THEN INSERT (
    id, worker_id, department, password_hash, password_plaintext, created_by_admin_id, is_active, last_login_at, created_at
) VALUES (
    workers_seq.NEXTVAL,
    'RD002',
    'Road Damage',
    '00fb93f2531565d203fa78a4a75f68cfacf805a88c7af916bb85a364000c7df4',
    NULL,
    1,
    1,
    TO_TIMESTAMP('2026-03-14 15:56:25.830954', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-14 15:51:18.510767', 'YYYY-MM-DD HH24:MI:SS.FF6')
);

MERGE INTO workers w
USING (SELECT 'RD003' AS worker_id FROM dual) src
ON (w.worker_id = src.worker_id)
WHEN MATCHED THEN UPDATE SET
    w.department = 'Road Damage',
    w.password_hash = '3e9b3796701c8082b7144ddf8bea6fd3f338b54f6f6ac1fc33da3b90fa1c1f0a',
    w.password_plaintext = NULL,
    w.created_by_admin_id = 1,
    w.is_active = 1,
    w.last_login_at = NULL,
    w.created_at = TO_TIMESTAMP('2026-03-19 10:53:05.439828', 'YYYY-MM-DD HH24:MI:SS.FF6')
WHEN NOT MATCHED THEN INSERT (
    id, worker_id, department, password_hash, password_plaintext, created_by_admin_id, is_active, last_login_at, created_at
) VALUES (
    workers_seq.NEXTVAL,
    'RD003',
    'Road Damage',
    '3e9b3796701c8082b7144ddf8bea6fd3f338b54f6f6ac1fc33da3b90fa1c1f0a',
    NULL,
    1,
    1,
    NULL,
    TO_TIMESTAMP('2026-03-19 10:53:05.439828', 'YYYY-MM-DD HH24:MI:SS.FF6')
);

MERGE INTO workers w
USING (SELECT 'WL001' AS worker_id FROM dual) src
ON (w.worker_id = src.worker_id)
WHEN MATCHED THEN UPDATE SET
    w.department = 'Water Leakage',
    w.password_hash = '8cdf2b1f160de4da5e3fc93fc6eddb3ffe6d1e3a3c7f77c3dc9ca9d2e7264e38',
    w.password_plaintext = NULL,
    w.created_by_admin_id = 1,
    w.is_active = 1,
    w.last_login_at = TO_TIMESTAMP('2026-03-19 10:56:07.927216', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    w.created_at = TO_TIMESTAMP('2026-03-19 10:53:37.820857', 'YYYY-MM-DD HH24:MI:SS.FF6')
WHEN NOT MATCHED THEN INSERT (
    id, worker_id, department, password_hash, password_plaintext, created_by_admin_id, is_active, last_login_at, created_at
) VALUES (
    workers_seq.NEXTVAL,
    'WL001',
    'Water Leakage',
    '8cdf2b1f160de4da5e3fc93fc6eddb3ffe6d1e3a3c7f77c3dc9ca9d2e7264e38',
    NULL,
    1,
    1,
    TO_TIMESTAMP('2026-03-19 10:56:07.927216', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-19 10:53:37.820857', 'YYYY-MM-DD HH24:MI:SS.FF6')
);

MERGE INTO workers w
USING (SELECT 'EM001' AS worker_id FROM dual) src
ON (w.worker_id = src.worker_id)
WHEN MATCHED THEN UPDATE SET
    w.department = 'Emergency',
    w.password_hash = '59ccb316509a0ae4df269a6e5855cc54caad9f05fd34fdc3ee07161555ff8c89',
    w.password_plaintext = NULL,
    w.created_by_admin_id = 1,
    w.is_active = 1,
    w.last_login_at = TO_TIMESTAMP('2026-04-01 13:27:46.617603', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    w.created_at = TO_TIMESTAMP('2026-04-01 09:10:14.950648', 'YYYY-MM-DD HH24:MI:SS.FF6')
WHEN NOT MATCHED THEN INSERT (
    id, worker_id, department, password_hash, password_plaintext, created_by_admin_id, is_active, last_login_at, created_at
) VALUES (
    workers_seq.NEXTVAL,
    'EM001',
    'Emergency',
    '59ccb316509a0ae4df269a6e5855cc54caad9f05fd34fdc3ee07161555ff8c89',
    NULL,
    1,
    1,
    TO_TIMESTAMP('2026-04-01 13:27:46.617603', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-04-01 09:10:14.950648', 'YYYY-MM-DD HH24:MI:SS.FF6')
);

MERGE INTO workers w
USING (SELECT 'SL001' AS worker_id FROM dual) src
ON (w.worker_id = src.worker_id)
WHEN MATCHED THEN UPDATE SET
    w.department = 'Street Light Issue',
    w.password_hash = '59ccb316509a0ae4df269a6e5855cc54caad9f05fd34fdc3ee07161555ff8c89',
    w.password_plaintext = NULL,
    w.created_by_admin_id = 1,
    w.is_active = 1,
    w.last_login_at = TO_TIMESTAMP('2026-04-01 09:41:46.589589', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    w.created_at = TO_TIMESTAMP('2026-04-01 09:41:40.674781', 'YYYY-MM-DD HH24:MI:SS.FF6')
WHEN NOT MATCHED THEN INSERT (
    id, worker_id, department, password_hash, password_plaintext, created_by_admin_id, is_active, last_login_at, created_at
) VALUES (
    workers_seq.NEXTVAL,
    'SL001',
    'Street Light Issue',
    '59ccb316509a0ae4df269a6e5855cc54caad9f05fd34fdc3ee07161555ff8c89',
    NULL,
    1,
    1,
    TO_TIMESTAMP('2026-04-01 09:41:46.589589', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-04-01 09:41:40.674781', 'YYYY-MM-DD HH24:MI:SS.FF6')
);

MERGE INTO issues i
USING (SELECT 'US-0007' AS complaint_number FROM dual) src
ON (i.complaint_number = src.complaint_number)
WHEN MATCHED THEN UPDATE SET
    i.user_id = 1,
    i.title = 'Garbage',
    i.description = 'garbage',
    i.location = 'Bidarahalli, Bangalore East, Bengaluru Urban, Karnataka, 560049, India',
    i.category = 'Garbage',
    i.media_urls = '"6ec9bc83-5477-42d7-b695-b66363c84c7b_camera-1.png,9d560583-fffb-4922-bbcb-594546b87e67_camera-2.png"',
    i.status = 'Resolved',
    i.assigned_department = NULL,
    i.assignment_deadline = NULL,
    i.assignment_duration_label = NULL,
    i.assigned_by_admin_id = NULL,
    i.worker_status = NULL,
    i.worker_resolution_requested_at = NULL,
    i.created_at = TO_TIMESTAMP('2026-03-10 06:22:28.426100', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    i.updated_at = TO_TIMESTAMP('2026-03-10 06:22:28.426100', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    i.assigned_at = NULL
WHEN NOT MATCHED THEN INSERT (
    id, user_id, complaint_number, title, description, location, category, media_urls, status,
    assigned_department, assignment_deadline, assignment_duration_label, assigned_by_admin_id,
    worker_status, worker_resolution_requested_at, created_at, updated_at, assigned_at
) VALUES (
    issues_seq.NEXTVAL,
    1,
    'US-0007',
    'Garbage',
    'garbage',
    'Bidarahalli, Bangalore East, Bengaluru Urban, Karnataka, 560049, India',
    'Garbage',
    '"6ec9bc83-5477-42d7-b695-b66363c84c7b_camera-1.png,9d560583-fffb-4922-bbcb-594546b87e67_camera-2.png"',
    'Resolved',
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    TO_TIMESTAMP('2026-03-10 06:22:28.426100', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-10 06:22:28.426100', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    NULL
);

MERGE INTO issues i
USING (SELECT 'US-0008' AS complaint_number FROM dual) src
ON (i.complaint_number = src.complaint_number)
WHEN MATCHED THEN UPDATE SET
    i.user_id = 2,
    i.title = 'Street Light Issue',
    i.description = 'waste street light no lights in street',
    i.location = 'Yelahanka Road, Nyayanga Badavane, Bengaluru North City Corporation, Bengaluru, Yelahanka taluku, Bengaluru Urban, Karnataka, 560064, India',
    i.category = 'Street Light Issue',
    i.media_urls = '"7df7e4a2-2832-4b20-a21d-5f366718b7f5_camera-1.png,77ad0e64-0f12-467a-8f0b-a65fa6f7a457_camera-2.png"',
    i.status = 'Resolved',
    i.assigned_department = NULL,
    i.assignment_deadline = NULL,
    i.assignment_duration_label = NULL,
    i.assigned_by_admin_id = NULL,
    i.worker_status = NULL,
    i.worker_resolution_requested_at = NULL,
    i.created_at = TO_TIMESTAMP('2026-03-10 13:52:43.609364', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    i.updated_at = TO_TIMESTAMP('2026-03-10 13:52:43.609364', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    i.assigned_at = NULL
WHEN NOT MATCHED THEN INSERT (
    id, user_id, complaint_number, title, description, location, category, media_urls, status,
    assigned_department, assignment_deadline, assignment_duration_label, assigned_by_admin_id,
    worker_status, worker_resolution_requested_at, created_at, updated_at, assigned_at
) VALUES (
    issues_seq.NEXTVAL,
    2,
    'US-0008',
    'Street Light Issue',
    'waste street light no lights in street',
    'Yelahanka Road, Nyayanga Badavane, Bengaluru North City Corporation, Bengaluru, Yelahanka taluku, Bengaluru Urban, Karnataka, 560064, India',
    'Street Light Issue',
    '"7df7e4a2-2832-4b20-a21d-5f366718b7f5_camera-1.png,77ad0e64-0f12-467a-8f0b-a65fa6f7a457_camera-2.png"',
    'Resolved',
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    TO_TIMESTAMP('2026-03-10 13:52:43.609364', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-10 13:52:43.609364', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    NULL
);

MERGE INTO issues i
USING (SELECT 'US-0009' AS complaint_number FROM dual) src
ON (i.complaint_number = src.complaint_number)
WHEN MATCHED THEN UPDATE SET
    i.user_id = 2,
    i.title = 'Road Damage',
    i.description = 'fff',
    i.location = 'Bidarahalli, Bangalore East, Bengaluru Urban, Karnataka, 560049, India',
    i.category = 'Road Damage',
    i.media_urls = '"feca9407-735a-4bf7-ba8c-dd83c59e8c13_camera-1.png"',
    i.status = 'Rejected',
    i.assigned_department = 'Road Damage',
    i.assignment_deadline = TO_TIMESTAMP('2026-03-14 17:28:04.359479', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    i.assignment_duration_label = '1 day',
    i.assigned_by_admin_id = 1,
    i.worker_status = 'Resolved',
    i.worker_resolution_requested_at = TO_TIMESTAMP('2026-03-14 15:56:32.409666', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    i.created_at = TO_TIMESTAMP('2026-03-13 14:22:22.196574', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    i.updated_at = TO_TIMESTAMP('2026-03-13 14:22:22.196574', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    i.assigned_at = NULL
WHEN NOT MATCHED THEN INSERT (
    id, user_id, complaint_number, title, description, location, category, media_urls, status,
    assigned_department, assignment_deadline, assignment_duration_label, assigned_by_admin_id,
    worker_status, worker_resolution_requested_at, created_at, updated_at, assigned_at
) VALUES (
    issues_seq.NEXTVAL,
    2,
    'US-0009',
    'Road Damage',
    'fff',
    'Bidarahalli, Bangalore East, Bengaluru Urban, Karnataka, 560049, India',
    'Road Damage',
    '"feca9407-735a-4bf7-ba8c-dd83c59e8c13_camera-1.png"',
    'Rejected',
    'Road Damage',
    TO_TIMESTAMP('2026-03-14 17:28:04.359479', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    '1 day',
    1,
    'Resolved',
    TO_TIMESTAMP('2026-03-14 15:56:32.409666', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-13 14:22:22.196574', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-13 14:22:22.196574', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    NULL
);

MERGE INTO issues i
USING (SELECT 'US-0010' AS complaint_number FROM dual) src
ON (i.complaint_number = src.complaint_number)
WHEN MATCHED THEN UPDATE SET
    i.user_id = 5,
    i.title = 'Water Leakage',
    i.description = 'asccbvhgfjgkjlg',
    i.location = 'Sejin Building, 67, Changgyeonggung-ro, Jugyo-dong, Euljiro-dong, Jung-gu, Seoul, 04545, South Korea',
    i.category = 'Water Leakage',
    i.media_urls = '"bd8c2ae6-8992-4fcf-910f-bbcd5ea38568_camera-1.png,f2ea08f1-60fe-4bc1-833d-0c73fbcba113_camera-2.png"',
    i.status = 'Resolved',
    i.assigned_department = 'Water Leakage',
    i.assignment_deadline = TO_TIMESTAMP('2026-03-20 10:55:47.548016', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    i.assignment_duration_label = '1 day',
    i.assigned_by_admin_id = 1,
    i.worker_status = 'Resolved',
    i.worker_resolution_requested_at = TO_TIMESTAMP('2026-03-19 10:56:24.678329', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    i.created_at = TO_TIMESTAMP('2026-03-19 10:50:38.370376', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    i.updated_at = TO_TIMESTAMP('2026-03-19 10:50:38.370376', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    i.assigned_at = NULL
WHEN NOT MATCHED THEN INSERT (
    id, user_id, complaint_number, title, description, location, category, media_urls, status,
    assigned_department, assignment_deadline, assignment_duration_label, assigned_by_admin_id,
    worker_status, worker_resolution_requested_at, created_at, updated_at, assigned_at
) VALUES (
    issues_seq.NEXTVAL,
    5,
    'US-0010',
    'Water Leakage',
    'asccbvhgfjgkjlg',
    'Sejin Building, 67, Changgyeonggung-ro, Jugyo-dong, Euljiro-dong, Jung-gu, Seoul, 04545, South Korea',
    'Water Leakage',
    '"bd8c2ae6-8992-4fcf-910f-bbcd5ea38568_camera-1.png,f2ea08f1-60fe-4bc1-833d-0c73fbcba113_camera-2.png"',
    'Resolved',
    'Water Leakage',
    TO_TIMESTAMP('2026-03-20 10:55:47.548016', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    '1 day',
    1,
    'Resolved',
    TO_TIMESTAMP('2026-03-19 10:56:24.678329', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-19 10:50:38.370376', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-19 10:50:38.370376', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    NULL
);

COMMIT;

PROMPT === Remaining table migration complete ===

SELECT COUNT(*) AS admin_count FROM admin_users;

SELECT COUNT(*) AS worker_count FROM workers;

SELECT COUNT(*) AS issue_count FROM issues;

SELECT COUNT(*) AS reset_count FROM worker_reset_requests;
