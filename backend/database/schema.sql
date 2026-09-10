-- PyPDF Services Database Schema
-- SQLite database for user management, sessions, files, jobs, and audit logging

-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Users table: Account identity and access
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin', 'service')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'suspended', 'deleted')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    access_expires_at DATETIME,
    email_verified_at DATETIME,
    last_login_at DATETIME,
    deleted_at DATETIME
);

-- Index for user lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at);

-- Sessions table: Login sessions and logout/revocation
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    revoked_at DATETIME,
    last_seen_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for session lookups and cleanup
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_revoked_at ON sessions(revoked_at);

-- Files table: Uploaded and generated file records
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    storage_key TEXT NOT NULL UNIQUE,
    original_name TEXT NOT NULL,
    media_type TEXT NOT NULL DEFAULT 'application/pdf',
    size_bytes INTEGER NOT NULL DEFAULT 0,
    page_count INTEGER,
    status TEXT NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'completed', 'failed', 'deleted')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    deleted_at DATETIME,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for file lookups
CREATE INDEX IF NOT EXISTS idx_files_owner_id ON files(owner_id);
CREATE INDEX IF NOT EXISTS idx_files_storage_key ON files(storage_key);
CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);
CREATE INDEX IF NOT EXISTS idx_files_deleted_at ON files(deleted_at);

-- Jobs table: A requested conversion or document operation
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    tool_id TEXT NOT NULL,
    tool_version TEXT NOT NULL DEFAULT '1.0.0',
    options_json TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled')),
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    error_code TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    finished_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for job lookups
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);

-- Job Files junction table: Connect jobs to their input/output files
CREATE TABLE IF NOT EXISTS job_files (
    job_id INTEGER NOT NULL,
    file_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('input', 'output')),
    position INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (job_id, file_id, role),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Index for job file lookups
CREATE INDEX IF NOT EXISTS idx_job_files_job_id ON job_files(job_id);
CREATE INDEX IF NOT EXISTS idx_job_files_file_id ON job_files(file_id);

-- Audit Events table: Who did what, to which record, and when
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_user_id INTEGER,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('success', 'failure', 'partial')),
    details_json TEXT,
    request_id TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Index for audit lookups
CREATE INDEX IF NOT EXISTS idx_audit_actor_user_id ON audit_events(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_events(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_events(action);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_events(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_request_id ON audit_events(request_id);

-- ============================================================================
-- AUTHENTICATION TABLES
-- ============================================================================

-- Auth Challenges table: Email verification, password reset, confirming email changes
CREATE TABLE IF NOT EXISTS auth_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    purpose TEXT NOT NULL CHECK (purpose IN ('email_verification', 'password_reset', 'email_change', 'mfa_setup')),
    token_hash TEXT NOT NULL UNIQUE,
    pending_value TEXT,
    expires_at DATETIME NOT NULL,
    used_at DATETIME,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for challenge lookups
CREATE INDEX IF NOT EXISTS idx_auth_challenges_user_id ON auth_challenges(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_challenges_token_hash ON auth_challenges(token_hash);
CREATE INDEX IF NOT EXISTS idx_auth_challenges_purpose ON auth_challenges(purpose);
CREATE INDEX IF NOT EXISTS idx_auth_challenges_expires_at ON auth_challenges(expires_at);

-- MFA Methods table: Authenticator-based 2FA
CREATE TABLE IF NOT EXISTS mfa_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('totp', 'webauthn', 'recovery_code')),
    secret_encrypted TEXT,
    verified_at DATETIME,
    disabled_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for MFA lookups
CREATE INDEX IF NOT EXISTS idx_mfa_methods_user_id ON mfa_methods(user_id);
CREATE INDEX IF NOT EXISTS idx_mfa_methods_type ON mfa_methods(type);

-- Recovery Codes table: One-use recovery when a second factor is unavailable
CREATE TABLE IF NOT EXISTS recovery_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    code_hash TEXT NOT NULL,
    used_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for recovery code lookups
CREATE INDEX IF NOT EXISTS idx_recovery_codes_user_id ON recovery_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_recovery_codes_code_hash ON recovery_codes(code_hash);

-- External Identities table: Verified Telegram account association
CREATE TABLE IF NOT EXISTS external_identities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL CHECK (provider IN ('telegram', 'google', 'github', 'microsoft')),
    provider_user_id TEXT NOT NULL,
    verified_at DATETIME,
    UNIQUE (provider, provider_user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for external identity lookups
CREATE INDEX IF NOT EXISTS idx_external_identities_user_id ON external_identities(user_id);
CREATE INDEX IF NOT EXISTS idx_external_identities_provider ON external_identities(provider);
CREATE INDEX IF NOT EXISTS idx_external_identities_provider_user_id ON external_identities(provider_user_id);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Trigger to update updated_at timestamp on users table
CREATE TRIGGER IF NOT EXISTS update_users_updated_at
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for active sessions
CREATE VIEW IF NOT EXISTS active_sessions AS
SELECT 
    s.id,
    s.user_id,
    u.username,
    u.email,
    s.created_at,
    s.expires_at,
    s.last_seen_at
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE s.revoked_at IS NULL 
  AND s.expires_at > CURRENT_TIMESTAMP
  AND u.status = 'active';

-- View for active jobs with file counts
CREATE VIEW IF NOT EXISTS job_summary AS
SELECT 
    j.id,
    j.user_id,
    u.username,
    j.tool_id,
    j.tool_version,
    j.status,
    j.progress,
    j.error_code,
    j.created_at,
    j.started_at,
    j.finished_at,
    COUNT(DISTINCT CASE WHEN jf.role = 'input' THEN jf.file_id END) as input_file_count,
    COUNT(DISTINCT CASE WHEN jf.role = 'output' THEN jf.file_id END) as output_file_count
FROM jobs j
JOIN users u ON j.user_id = u.id
LEFT JOIN job_files jf ON j.id = jf.job_id
GROUP BY j.id;

-- View for user file statistics
CREATE VIEW IF NOT EXISTS user_file_stats AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(f.id) as total_files,
    SUM(f.size_bytes) as total_size_bytes,
    COUNT(CASE WHEN f.status = 'completed' THEN 1 END) as completed_files,
    COUNT(CASE WHEN f.status = 'processing' THEN 1 END) as processing_files,
    COUNT(CASE WHEN f.status = 'failed' THEN 1 END) as failed_files
FROM users u
LEFT JOIN files f ON u.id = f.owner_id AND f.deleted_at IS NULL
WHERE u.status != 'deleted'
GROUP BY u.id;

-- ============================================================================
-- INITIAL DATA (Optional - for development/testing)
-- ============================================================================

-- Insert a default admin user (password: admin123 - hash should be computed properly)
-- NOTE: In production, passwords should be hashed using bcrypt or argon2
INSERT OR IGNORE INTO users (username, email, password_hash, role, status, email_verified_at)
VALUES ('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu', 'admin', 'active', CURRENT_TIMESTAMP);

-- Insert a default test user (password: user123)
INSERT OR IGNORE INTO users (username, email, password_hash, role, status, email_verified_at)
VALUES ('user', 'user@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu', 'user', 'active', CURRENT_TIMESTAMP);
