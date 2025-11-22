-- ============================================================================
-- SERVER_BACKUPS TABLE
-- ============================================================================
-- Backup tracking for servers and configurations
--
-- Dependencies: servers (9_servers.sql), sync_operations (10_sync_operations.sql)
-- Constraints: None (this is a tracking table)

CREATE TABLE IF NOT EXISTS server_backups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
    sync_operation_id UUID REFERENCES sync_operations(id) ON DELETE SET NULL,
    backup_name TEXT NOT NULL,
    backup_type TEXT NOT NULL CHECK (backup_type IN ('full', 'incremental', 'differential', 'config_only', 'environment_only', 'database', 'custom')),
    backup_method TEXT NOT NULL CHECK (backup_method IN ('rsync', 'tar', 'zip', 'snapshot', 'database_dump', 'custom_script', 'cloud_backup')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled', 'expired', 'restoring')),
    source_paths TEXT[] DEFAULT '{}',
    destination_path TEXT,
    backup_format TEXT DEFAULT 'tar.gz' CHECK (backup_format IN ('tar', 'tar.gz', 'tar.bz2', 'zip', '7z', 'rsync', 'native')),
    compression_enabled BOOLEAN DEFAULT true,
    compression_level INTEGER DEFAULT 6 CHECK (compression_level BETWEEN 1 AND 9),
    encryption_enabled BOOLEAN DEFAULT false,
    encryption_algorithm TEXT DEFAULT 'aes256',
    checksum_algorithm TEXT DEFAULT 'sha256',
    file_count BIGINT,
    total_size_bytes BIGINT,
    compressed_size_bytes BIGINT,
    compression_ratio NUMERIC(5,2),
    backup_size_limit_gb NUMERIC(10,2),
    retention_days INTEGER DEFAULT 30,
    retention_policy JSONB DEFAULT '{
        "keep_daily": 7,
        "keep_weekly": 4,
        "keep_monthly": 12,
        "keep_yearly": 5,
        "auto_cleanup": true
    }'::jsonb,
    backup_schedule TEXT,  -- Cron expression
    last_backup_at TIMESTAMPTZ,
    next_backup_at TIMESTAMPTZ,
    backup_duration_seconds BIGINT,
    backup_throughput_mbps NUMERIC(10,2),
    verification_enabled BOOLEAN DEFAULT true,
    verification_status TEXT DEFAULT 'pending' CHECK (verification_status IN ('pending', 'in_progress', 'passed', 'failed', 'skipped')),
    verification_result JSONB,
    auto_restore_enabled BOOLEAN DEFAULT false,
    restore_test_enabled BOOLEAN DEFAULT false,
    last_restore_test_at TIMESTAMPTZ,
    restore_test_result JSONB,
    backup_metadata JSONB DEFAULT '{}'::jsonb,
    includes_database BOOLEAN DEFAULT false,
    includes_config_files BOOLEAN DEFAULT true,
    includes_environment_variables BOOLEAN DEFAULT true,
    includes_user_data BOOLEAN DEFAULT false,
    exclude_patterns TEXT[] DEFAULT '{}',
    include_patterns TEXT[] DEFAULT '{}',
    backup_tags TEXT[] DEFAULT '{}',
    error_message TEXT,
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    notification_enabled BOOLEAN DEFAULT true,
    notification_channels TEXT[],
    storage_location_type TEXT CHECK (storage_location_type IN ('local', 'network', 'cloud', 'tape')),
    storage_location_path TEXT,
    cloud_provider TEXT,
    cloud_bucket TEXT,
    cloud_region TEXT,
    access_url TEXT,  -- URL to access backup if in cloud storage
    is_encrypted_at_rest BOOLEAN DEFAULT false,
    data_classification TEXT DEFAULT 'confidential' CHECK (data_classification IN ('public', 'internal', 'confidential', 'restricted')),
    compliance_tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

-- Table for backup restoration records
CREATE TABLE IF NOT EXISTS backup_restorations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_backup_id UUID NOT NULL REFERENCES server_backups(id) ON DELETE CASCADE,
    target_server_id UUID REFERENCES servers(id) ON DELETE CASCADE,
    restore_name TEXT NOT NULL,
    restore_type TEXT NOT NULL CHECK (restore_type IN ('full', 'partial', 'selective', 'file_level', 'database_only', 'config_only', 'environment_only')),
    restore_mode TEXT NOT NULL CHECK (restore_mode IN ('overwrite', 'merge', 'preview_only', 'dry_run')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled', 'rolled_back')),
    target_paths TEXT[] DEFAULT '{}',
    restore_paths JSONB DEFAULT '[]'::jsonb,  -- Specific paths to restore
    exclude_restore_paths JSONB DEFAULT '[]'::jsonb,  -- Paths to exclude from restore
    preserve_permissions BOOLEAN DEFAULT true,
    preserve_ownership BOOLEAN DEFAULT true,
    preserve_timestamps BOOLEAN DEFAULT true,
    verification_enabled BOOLEAN DEFAULT true,
    verification_status TEXT DEFAULT 'pending' CHECK (verification_status IN ('pending', 'in_progress', 'passed', 'failed', 'skipped')),
    verification_result JSONB,
    restore_duration_seconds BIGINT,
    files_restored BIGINT,
    bytes_restored BIGINT,
    restore_throughput_mbps NUMERIC(10,2),
    backup_checksum TEXT,
    restore_checksum TEXT,
    checksum_match BOOLEAN,
    rollback_enabled BOOLEAN DEFAULT false,
    rollback_status TEXT CHECK (rollback_status IN ('not_needed', 'in_progress', 'completed', 'failed')),
    rollback_details JSONB,
    restore_metadata JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    notification_enabled BOOLEAN DEFAULT true,
    notification_channels TEXT[],
    requested_by TEXT,
    approval_required BOOLEAN DEFAULT false,
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Table for backup verification and integrity checks
CREATE TABLE IF NOT EXISTS backup_integrity_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_backup_id UUID NOT NULL REFERENCES server_backups(id) ON DELETE CASCADE,
    check_type TEXT NOT NULL CHECK (check_type IN ('checksum', 'file_count', 'size_verification', 'data_integrity', 'restore_test', 'encryption_verification')),
    check_status TEXT NOT NULL DEFAULT 'pending' CHECK (check_status IN ('pending', 'in_progress', 'passed', 'failed', 'warning', 'skipped')),
    expected_value TEXT,
    actual_value TEXT,
    is_match BOOLEAN,
    check_details JSONB DEFAULT '{}'::jsonb,
    check_duration_seconds BIGINT,
    check_result JSONB,
    warning_threshold NUMERIC(10,2),
    error_threshold NUMERIC(10,2),
    auto_check_enabled BOOLEAN DEFAULT true,
    check_frequency TEXT DEFAULT 'daily',  -- daily, weekly, monthly
    last_check_at TIMESTAMPTZ,
    next_check_at TIMESTAMPTZ,
    consecutive_failures INTEGER DEFAULT 0,
    alert_on_failure BOOLEAN DEFAULT true,
    alert_sent BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table and column comments
COMMENT ON TABLE server_backups IS 'Backup tracking for servers and configurations';
COMMENT ON COLUMN server_backups.id IS 'Unique backup identifier';
COMMENT ON COLUMN server_backups.server_id IS 'Foreign key to servers table';
COMMENT ON COLUMN server_backups.sync_operation_id IS 'Foreign key to sync_operations table if created by sync operation';
COMMENT ON COLUMN server_backups.backup_name IS 'Human-readable backup name';
COMMENT ON COLUMN server_backups.backup_type IS 'Backup type: full, incremental, differential, config_only, environment_only, database, custom';
COMMENT ON COLUMN server_backups.backup_method IS 'Backup method: rsync, tar, zip, snapshot, database_dump, custom_script, cloud_backup';
COMMENT ON COLUMN server_backups.status IS 'Backup status: pending, in_progress, completed, failed, cancelled, expired, restoring';
COMMENT ON COLUMN server_backups.source_paths IS 'Array of source paths to backup';
COMMENT ON COLUMN server_backups.destination_path IS 'Destination path for backup';
COMMENT ON COLUMN server_backups.backup_format IS 'Backup format: tar, tar.gz, tar.bz2, zip, 7z, rsync, native';
COMMENT ON COLUMN server_backups.compression_enabled IS 'Whether compression is enabled';
COMMENT ON COLUMN server_backups.compression_level IS 'Compression level (1-9)';
COMMENT ON COLUMN server_backups.encryption_enabled IS 'Whether encryption is enabled';
COMMENT ON COLUMN server_backups.encryption_algorithm IS 'Encryption algorithm (default: aes256)';
COMMENT ON COLUMN server_backups.checksum_algorithm IS 'Checksum algorithm (default: sha256)';
COMMENT ON COLUMN server_backups.file_count IS 'Number of files in backup';
COMMENT ON COLUMN server_backups.total_size_bytes IS 'Total uncompressed backup size in bytes';
COMMENT ON COLUMN server_backups.compressed_size_bytes IS 'Compressed backup size in bytes';
COMMENT ON COLUMN server_backups.compression_ratio IS 'Compression ratio percentage';
COMMENT ON COLUMN server_backups.backup_size_limit_gb IS 'Maximum backup size limit in GB';
COMMENT ON COLUMN server_backups.retention_days IS 'Number of days to retain backup';
COMMENT ON COLUMN server_backups.retention_policy IS 'Retention policy configuration (JSONB)';
COMMENT ON COLUMN server_backups.backup_schedule IS 'Cron expression for scheduled backups';
COMMENT ON COLUMN server_backups.last_backup_at IS 'Last backup timestamp';
COMMENT ON COLUMN server_backups.next_backup_at IS 'Next scheduled backup timestamp';
COMMENT ON COLUMN server_backups.backup_duration_seconds IS 'Backup duration in seconds';
COMMENT ON COLUMN server_backups.backup_throughput_mbps IS 'Backup throughput in MB/s';
COMMENT ON COLUMN server_backups.verification_enabled IS 'Whether backup verification is enabled';
COMMENT ON COLUMN server_backups.verification_status IS 'Verification status: pending, in_progress, passed, failed, skipped';
COMMENT ON COLUMN server_backups.verification_result IS 'Verification result details (JSONB)';
COMMENT ON COLUMN server_backups.auto_restore_enabled IS 'Whether automatic restore is enabled';
COMMENT ON COLUMN server_backups.restore_test_enabled IS 'Whether restore testing is enabled';
COMMENT ON COLUMN server_backups.last_restore_test_at IS 'Last restore test timestamp';
COMMENT ON COLUMN server_backups.restore_test_result IS 'Restore test result (JSONB)';
COMMENT ON COLUMN server_backups.backup_metadata IS 'Backup metadata (JSONB)';
COMMENT ON COLUMN server_backups.includes_database IS 'Whether backup includes database';
COMMENT ON COLUMN server_backups.includes_config_files IS 'Whether backup includes config files';
COMMENT ON COLUMN server_backups.includes_environment_variables IS 'Whether backup includes environment variables';
COMMENT ON COLUMN server_backups.includes_user_data IS 'Whether backup includes user data';
COMMENT ON COLUMN server_backups.exclude_patterns IS 'Array of exclude patterns';
COMMENT ON COLUMN server_backups.include_patterns IS 'Array of include patterns';
COMMENT ON COLUMN server_backups.backup_tags IS 'Array of backup tags';
COMMENT ON COLUMN server_backups.error_message IS 'Error message if backup failed';
COMMENT ON COLUMN server_backups.error_details IS 'Detailed error information (JSONB)';
COMMENT ON COLUMN server_backups.retry_count IS 'Current retry count';
COMMENT ON COLUMN server_backups.max_retries IS 'Maximum retry attempts';
COMMENT ON COLUMN server_backups.notification_enabled IS 'Whether notifications are enabled';
COMMENT ON COLUMN server_backups.notification_channels IS 'Notification channels';
COMMENT ON COLUMN server_backups.storage_location_type IS 'Storage type: local, network, cloud, tape';
COMMENT ON COLUMN server_backups.storage_location_path IS 'Storage location path';
COMMENT ON COLUMN server_backups.cloud_provider IS 'Cloud provider (AWS, GCP, Azure, etc.)';
COMMENT ON COLUMN server_backups.cloud_bucket IS 'Cloud storage bucket name';
COMMENT ON COLUMN server_backups.cloud_region IS 'Cloud storage region';
COMMENT ON COLUMN server_backups.access_url IS 'URL to access backup if in cloud storage';
COMMENT ON COLUMN server_backups.is_encrypted_at_rest IS 'Whether backup is encrypted at rest';
COMMENT ON COLUMN server_backups.data_classification IS 'Data classification: public, internal, confidential, restricted';
COMMENT ON COLUMN server_backups.compliance_tags IS 'Compliance tags array';
COMMENT ON COLUMN server_backups.created_at IS 'Backup creation timestamp';
COMMENT ON COLUMN server_backups.updated_at IS 'Last update timestamp';
COMMENT ON COLUMN server_backups.expires_at IS 'Backup expiration timestamp';
COMMENT ON COLUMN server_backups.deleted_at IS 'Soft delete timestamp';

COMMENT ON TABLE backup_restorations IS 'Backup restoration records';
COMMENT ON COLUMN backup_restorations.id IS 'Unique restore identifier';
COMMENT ON COLUMN backup_restorations.server_backup_id IS 'Foreign key to server_backups table';
COMMENT ON COLUMN backup_restorations.target_server_id IS 'Foreign key to servers table (target server)';
COMMENT ON COLUMN backup_restorations.restore_name IS 'Human-readable restore name';
COMMENT ON COLUMN backup_restorations.restore_type IS 'Restore type: full, partial, selective, file_level, database_only, config_only, environment_only';
COMMENT ON COLUMN backup_restorations.restore_mode IS 'Restore mode: overwrite, merge, preview_only, dry_run';
COMMENT ON COLUMN backup_restorations.status IS 'Restore status: pending, in_progress, completed, failed, cancelled, rolled_back';
COMMENT ON COLUMN backup_restorations.target_paths IS 'Array of target paths for restore';
COMMENT ON COLUMN backup_restorations.restore_paths IS 'Specific paths to restore (JSONB)';
COMMENT ON COLUMN backup_restorations.exclude_restore_paths IS 'Paths to exclude from restore (JSONB)';
COMMENT ON COLUMN backup_restorations.preserve_permissions IS 'Whether to preserve file permissions';
COMMENT ON COLUMN backup_restorations.preserve_ownership IS 'Whether to preserve file ownership';
COMMENT ON COLUMN backup_restorations.preserve_timestamps IS 'Whether to preserve file timestamps';
COMMENT ON COLUMN backup_restorations.verification_enabled IS 'Whether restore verification is enabled';
COMMENT ON COLUMN backup_restorations.verification_status IS 'Verification status: pending, in_progress, passed, failed, skipped';
COMMENT ON COLUMN backup_restorations.verification_result IS 'Verification result details (JSONB)';
COMMENT ON COLUMN backup_restorations.restore_duration_seconds IS 'Restore duration in seconds';
COMMENT ON COLUMN backup_restorations.files_restored IS 'Number of files restored';
COMMENT ON COLUMN backup_restorations.bytes_restored IS 'Number of bytes restored';
COMMENT ON COLUMN backup_restorations.restore_throughput_mbps IS 'Restore throughput in MB/s';
COMMENT ON COLUMN backup_restorations.backup_checksum IS 'Original backup checksum';
COMMENT ON COLUMN backup_restorations.restore_checksum IS 'Checksum of restored data';
COMMENT ON COLUMN backup_restorations.checksum_match IS 'Whether checksums match';
COMMENT ON COLUMN backup_restorations.rollback_enabled IS 'Whether rollback is enabled';
COMMENT ON COLUMN backup_restorations.rollback_status IS 'Rollback status: not_needed, in_progress, completed, failed';
COMMENT ON COLUMN backup_restorations.rollback_details IS 'Rollback details (JSONB)';
COMMENT ON COLUMN backup_restorations.restore_metadata IS 'Restore metadata (JSONB)';
COMMENT ON COLUMN backup_restorations.error_message IS 'Error message if restore failed';
COMMENT ON COLUMN backup_restorations.error_details IS 'Detailed error information (JSONB)';
COMMENT ON COLUMN backup_restorations.retry_count IS 'Current retry count';
COMMENT ON COLUMN backup_restorations.max_retries IS 'Maximum retry attempts';
COMMENT ON COLUMN backup_restorations.notification_enabled IS 'Whether notifications are enabled';
COMMENT ON COLUMN backup_restorations.notification_channels IS 'Notification channels';
COMMENT ON COLUMN backup_restorations.requested_by IS 'Who requested the restore';
COMMENT ON COLUMN backup_restorations.approval_required IS 'Whether approval is required';
COMMENT ON COLUMN backup_restorations.approved_by IS 'Who approved the restore';
COMMENT ON COLUMN backup_restorations.approved_at IS 'Approval timestamp';
COMMENT ON COLUMN backup_restorations.created_at IS 'Restore creation timestamp';
COMMENT ON COLUMN backup_restorations.updated_at IS 'Last update timestamp';
COMMENT ON COLUMN backup_restorations.started_at IS 'Restore start timestamp';
COMMENT ON COLUMN backup_restorations.completed_at IS 'Restore completion timestamp';

COMMENT ON TABLE backup_integrity_checks IS 'Backup verification and integrity checks';
COMMENT ON COLUMN backup_integrity_checks.id IS 'Unique integrity check identifier';
COMMENT ON COLUMN backup_integrity_checks.server_backup_id IS 'Foreign key to server_backups table';
COMMENT ON COLUMN backup_integrity_checks.check_type IS 'Check type: checksum, file_count, size_verification, data_integrity, restore_test, encryption_verification';
COMMENT ON COLUMN backup_integrity_checks.check_status IS 'Check status: pending, in_progress, passed, failed, warning, skipped';
COMMENT ON COLUMN backup_integrity_checks.expected_value IS 'Expected value for the check';
COMMENT ON COLUMN backup_integrity_checks.actual_value IS 'Actual value from the check';
COMMENT ON COLUMN backup_integrity_checks.is_match IS 'Whether expected and actual values match';
COMMENT ON COLUMN backup_integrity_checks.check_details IS 'Check details (JSONB)';
COMMENT ON COLUMN backup_integrity_checks.check_duration_seconds IS 'Check duration in seconds';
COMMENT ON COLUMN backup_integrity_checks.check_result IS 'Check result (JSONB)';
COMMENT ON COLUMN backup_integrity_checks.warning_threshold IS 'Warning threshold for numeric checks';
COMMENT ON COLUMN backup_integrity_checks.error_threshold IS 'Error threshold for numeric checks';
COMMENT ON COLUMN backup_integrity_checks.auto_check_enabled IS 'Whether automatic checks are enabled';
COMMENT ON COLUMN backup_integrity_checks.check_frequency IS 'Check frequency: daily, weekly, monthly';
COMMENT ON COLUMN backup_integrity_checks.last_check_at IS 'Last check timestamp';
COMMENT ON COLUMN backup_integrity_checks.next_check_at IS 'Next scheduled check timestamp';
COMMENT ON COLUMN backup_integrity_checks.consecutive_failures IS 'Number of consecutive failures';
COMMENT ON COLUMN backup_integrity_checks.alert_on_failure IS 'Whether to alert on failure';
COMMENT ON COLUMN backup_integrity_checks.alert_sent IS 'Whether alert has been sent';
COMMENT ON COLUMN backup_integrity_checks.metadata IS 'Additional check metadata (JSONB)';
COMMENT ON COLUMN backup_integrity_checks.created_at IS 'Check creation timestamp';
COMMENT ON COLUMN backup_integrity_checks.updated_at IS 'Last update timestamp';

-- Indexes for server_backups
CREATE INDEX IF NOT EXISTS idx_server_backups_server_id ON server_backups(server_id);
CREATE INDEX IF NOT EXISTS idx_server_backups_sync_operation_id ON server_backups(sync_operation_id);
CREATE INDEX IF NOT EXISTS idx_server_backups_status ON server_backups(status);
CREATE INDEX IF NOT EXISTS idx_server_backups_backup_type ON server_backups(backup_type);
CREATE INDEX IF NOT EXISTS idx_server_backups_next_backup_at ON server_backups(next_backup_at) WHERE next_backup_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_server_backups_expires_at ON server_backups(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_server_backups_created_at ON server_backups(created_at);
CREATE INDEX IF NOT EXISTS idx_server_backups_backup_tags ON server_backups USING GIN(backup_tags);

-- Indexes for backup_restorations
CREATE INDEX IF NOT EXISTS idx_backup_restorations_server_backup_id ON backup_restorations(server_backup_id);
CREATE INDEX IF NOT EXISTS idx_backup_restorations_target_server_id ON backup_restorations(target_server_id);
CREATE INDEX IF NOT EXISTS idx_backup_restorations_status ON backup_restorations(status);
CREATE INDEX IF NOT EXISTS idx_backup_restorations_restore_type ON backup_restorations(restore_type);
CREATE INDEX IF NOT EXISTS idx_backup_restorations_requested_by ON backup_restorations(requested_by) WHERE requested_by IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_backup_restorations_created_at ON backup_restorations(created_at);
CREATE INDEX IF NOT EXISTS idx_backup_restorations_started_at ON backup_restorations(started_at) WHERE started_at IS NOT NULL;

-- Indexes for backup_integrity_checks
CREATE INDEX IF NOT EXISTS idx_backup_integrity_checks_server_backup_id ON backup_integrity_checks(server_backup_id);
CREATE INDEX IF NOT EXISTS idx_backup_integrity_checks_check_type ON backup_integrity_checks(check_type);
CREATE INDEX IF NOT EXISTS idx_backup_integrity_checks_check_status ON backup_integrity_checks(check_status);
CREATE INDEX IF NOT EXISTS idx_backup_integrity_checks_next_check_at ON backup_integrity_checks(next_check_at) WHERE next_check_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_backup_integrity_checks_last_check_at ON backup_integrity_checks(last_check_at);
CREATE INDEX IF NOT EXISTS idx_backup_integrity_checks_consecutive_failures ON backup_integrity_checks(consecutive_failures) WHERE consecutive_failures > 0;