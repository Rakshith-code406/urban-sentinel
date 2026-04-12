SET DEFINE OFF

PROMPT === Migrating legacy SQLite users into Oracle USERS table ===

MERGE INTO users u
USING (SELECT 'grandrakshith@gmail.com' AS email FROM dual) src
ON (u.email = src.email)
WHEN MATCHED THEN UPDATE SET
    u.full_name = 'Rakshith',
    u.phone = '8904723329',
    u.password_hash = 'scrypt$16384$8$1$272ccbdf59639a69142a46f81fc275a9$417158d7fdfd35611823b2fc2171f6053b2a07984d733a98fa7b7c538e14207f500e2b66c2f4a3d4991c43c749ba34ba8dc9697610340aa10ec228841edd5596',
    u.is_active = 1,
    u.reset_code_hash = 'f7fdb1bf2c9db4cc642b14023aeed28f51dac0e8e41fa412cf684482216a84ad',
    u.reset_code_expires_at = TO_TIMESTAMP('2026-03-30 17:01:33.766941', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    u.last_login_at = TO_TIMESTAMP('2026-03-30 15:35:31.498521', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    u.created_at = TO_TIMESTAMP('2026-03-07 16:26:11.262870', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    u.email_verified = 1,
    u.email_verification_code_hash = NULL,
    u.email_verification_expires_at = NULL
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
    'Rakshith',
    'grandrakshith@gmail.com',
    '8904723329',
    'scrypt$16384$8$1$272ccbdf59639a69142a46f81fc275a9$417158d7fdfd35611823b2fc2171f6053b2a07984d733a98fa7b7c538e14207f500e2b66c2f4a3d4991c43c749ba34ba8dc9697610340aa10ec228841edd5596',
    1,
    'f7fdb1bf2c9db4cc642b14023aeed28f51dac0e8e41fa412cf684482216a84ad',
    TO_TIMESTAMP('2026-03-30 17:01:33.766941', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-30 15:35:31.498521', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-07 16:26:11.262870', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    'legacy_sqlite_migration',
    1,
    NULL,
    NULL
);

MERGE INTO users u
USING (SELECT 'poorvikajnreddy606669@gmail.com' AS email FROM dual) src
ON (u.email = src.email)
WHEN MATCHED THEN UPDATE SET
    u.full_name = 'Poorvika J N',
    u.phone = '919071275469',
    u.password_hash = '8b7ac83608be9de68df68b589888dc2eff3f3b874ad29fa2ed0f886adc730963',
    u.is_active = 1,
    u.reset_code_hash = NULL,
    u.reset_code_expires_at = NULL,
    u.last_login_at = TO_TIMESTAMP('2026-03-17 13:01:22.018635', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    u.created_at = TO_TIMESTAMP('2026-03-10 13:49:54.930229', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    u.email_verified = 0,
    u.email_verification_code_hash = NULL,
    u.email_verification_expires_at = NULL
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
    'Poorvika J N',
    'poorvikajnreddy606669@gmail.com',
    '919071275469',
    '8b7ac83608be9de68df68b589888dc2eff3f3b874ad29fa2ed0f886adc730963',
    1,
    NULL,
    NULL,
    TO_TIMESTAMP('2026-03-17 13:01:22.018635', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-10 13:49:54.930229', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    'legacy_sqlite_migration',
    0,
    NULL,
    NULL
);

MERGE INTO users u
USING (SELECT 'abc@gmail.com' AS email FROM dual) src
ON (u.email = src.email)
WHEN MATCHED THEN UPDATE SET
    u.full_name = 'rakk',
    u.phone = '917896784445',
    u.password_hash = '09aee341b73a54b13076e97fac02fa9c56284067f4bd38c111fab281b9cd24cd',
    u.is_active = 1,
    u.reset_code_hash = NULL,
    u.reset_code_expires_at = NULL,
    u.last_login_at = NULL,
    u.created_at = TO_TIMESTAMP('2026-03-12 14:20:50.113333', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    u.email_verified = 0,
    u.email_verification_code_hash = NULL,
    u.email_verification_expires_at = NULL
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
    'rakk',
    'abc@gmail.com',
    '917896784445',
    '09aee341b73a54b13076e97fac02fa9c56284067f4bd38c111fab281b9cd24cd',
    1,
    NULL,
    NULL,
    NULL,
    TO_TIMESTAMP('2026-03-12 14:20:50.113333', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    'legacy_sqlite_migration',
    0,
    NULL,
    NULL
);

MERGE INTO users u
USING (SELECT 'rthjj@gmail.com' AS email FROM dual) src
ON (u.email = src.email)
WHEN MATCHED THEN UPDATE SET
    u.full_name = 'rakshith',
    u.phone = '918904723329',
    u.password_hash = '09aee341b73a54b13076e97fac02fa9c56284067f4bd38c111fab281b9cd24cd',
    u.is_active = 1,
    u.reset_code_hash = NULL,
    u.reset_code_expires_at = NULL,
    u.last_login_at = NULL,
    u.created_at = TO_TIMESTAMP('2026-03-12 14:22:04.790574', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    u.email_verified = 0,
    u.email_verification_code_hash = NULL,
    u.email_verification_expires_at = NULL
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
    'rakshith',
    'rthjj@gmail.com',
    '918904723329',
    '09aee341b73a54b13076e97fac02fa9c56284067f4bd38c111fab281b9cd24cd',
    1,
    NULL,
    NULL,
    NULL,
    TO_TIMESTAMP('2026-03-12 14:22:04.790574', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    'legacy_sqlite_migration',
    0,
    NULL,
    NULL
);

MERGE INTO users u
USING (SELECT 'sania.e07@gmail.com' AS email FROM dual) src
ON (u.email = src.email)
WHEN MATCHED THEN UPDATE SET
    u.full_name = 'sania.e',
    u.phone = '916364062075',
    u.password_hash = '7d6aee7b3a954144f9f8accb2c6a2da7bb65d2be27795bec8709944fba9cc81e',
    u.is_active = 1,
    u.reset_code_hash = NULL,
    u.reset_code_expires_at = NULL,
    u.last_login_at = TO_TIMESTAMP('2026-03-19 10:44:02.070969', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    u.created_at = TO_TIMESTAMP('2026-03-19 10:43:07.578596', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    u.email_verified = 0,
    u.email_verification_code_hash = NULL,
    u.email_verification_expires_at = NULL
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
    'sania.e',
    'sania.e07@gmail.com',
    '916364062075',
    '7d6aee7b3a954144f9f8accb2c6a2da7bb65d2be27795bec8709944fba9cc81e',
    1,
    NULL,
    NULL,
    TO_TIMESTAMP('2026-03-19 10:44:02.070969', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    TO_TIMESTAMP('2026-03-19 10:43:07.578596', 'YYYY-MM-DD HH24:MI:SS.FF6'),
    'legacy_sqlite_migration',
    0,
    NULL,
    NULL
);

COMMIT;

PROMPT === User migration complete ===

SELECT id, full_name, email, phone, registration_source, email_verified FROM users ORDER BY id;
