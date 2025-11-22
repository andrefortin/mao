-- ============================================================================
-- SYNC_OPERATIONS TABLE
-- ============================================================================
-- Individual sync operation tracking
--
-- Dependencies: servers (9_servers.sql)
-- Constraints:
--   - operation_name must be unique per server

CREATE TABLE IF NOT EXISTS sync_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
    operation_name TEXT NOT NULL,
    sync_type TEXT NOT NULL CHECK (sync_type IN ('full_sync', 'incremental_sync', 'file_sync', 'env_sync', 'config_sync', 'backup_sync')),
    source_path TEXT,
    destination_path TEXT,
    operation_direction TEXT NOT NULL CHECK (operation_direction IN ('upload', 'download', 'bidirectional')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled', 'paused')),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    schedule_expression TEXT,  -- Cron expression for scheduled syncs
    next_run TIMESTAMPTZ,
    last_run TIMESTAMPTZ,
    run_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    total_files_transferred BIGINT DEFAULT 0,
    total_bytes_transferred BIGINT DEFAULT 0,
    sync_options JSONB DEFAULT '{
        "preserve_permissions": true,
        "preserve_timestamps": true,
        "follow_symlinks": false,
        "compression": true,
        "encryption": false,
        "exclude_patterns": [],
        "include_patterns": [],
        "checksum_verification": true,
        "max_file_size": null,
        "max_file_age": null,
        "dry_run": false
    }'::jsonb,
    error_message TEXT,
    error_details JSONB,
    progress_percentage NUMERIC(5,2) DEFAULT 0.00 CHECK (progress_percentage BETWEEN 0 AND 100),
    estimated_completion TIMESTAMPTZ,
    auto_retry_enabled BOOLEAN DEFAULT true,
    max_retry_attempts INTEGER DEFAULT 3,
    retry_count INTEGER DEFAULT 0,
    retry_delay_seconds INTEGER DEFAULT 300,
    notification_enabled BOOLEAN DEFAULT true,
    notification_emails TEXT[],
    notification_webhooks TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Unique constraint
    CONSTRAINT unique_operation_name_per_server UNIQUE (server_id, operation_name)
);

-- Table and column comments
COMMENT ON TABLE sync_operations IS 'Individual sync operation tracking and configuration';
COMMENT ON COLUMN sync_operations.id IS 'Unique sync operation identifier';
COMMENT ON COLUMN sync_operations.server_id IS 'Foreign key to servers table';
COMMENT ON COLUMN sync_operations.operation_name IS 'Human-readable operation name (unique per server)';
COMMENT ON COLUMN sync_operations.sync_type IS 'Type of sync operation: full_sync, incremental_sync, file_sync, env_sync, config_sync, backup_sync';
COMMENT ON COLUMN sync_operations.source_path IS 'Source path for sync operation';
COMMENT ON COLUMN sync_operations.destination_path IS 'Destination path for sync operation';
COMMENT ON COLUMN sync_operations.operation_direction IS 'Direction: upload, download, bidirectional';
COMMENT ON COLUMN sync_operations.status IS 'Operation status: pending, in_progress, completed, failed, cancelled, paused';
COMMENT ON COLUMN sync_operations.priority IS 'Operation priority (1-10, lower number = higher priority)';
COMMENT ON COLUMN sync_operations.schedule_expression IS 'Cron expression for scheduled operations';
COMMENT ON COLUMN sync_operations.next_run IS 'Next scheduled run time';
COMMENT ON COLUMN sync_operations.last_run IS 'Last run timestamp';
COMMENT ON COLUMN sync_operations.run_count IS 'Total number of times operation has run';
COMMENT ON COLUMN sync_operations.success_count IS 'Number of successful runs';
COMMENT ON COLUMN sync_operations.failure_count IS 'Number of failed runs';
COMMENT ON COLUMN sync_operations.total_files_transferred IS 'Total files transferred across all runs';
COMMENT ON COLUMN sync_operations.total_bytes_transferred IS 'Total bytes transferred across all runs';
COMMENT ON COLUMN sync_operations.sync_options IS 'Sync configuration options (JSONB)';
COMMENT ON COLUMN sync_operations.error_message IS 'Last error message (if failed)';
COMMENT ON COLUMN sync_operations.error_details IS 'Detailed error information (JSONB)';
COMMENT ON COLUMN sync_operations.progress_percentage IS 'Current progress percentage (0-100)';
COMMENT ON COLUMN sync_operations.estimated_completion IS 'Estimated completion time';
COMMENT ON COLUMN sync_operations.auto_retry_enabled IS 'Whether automatic retry is enabled';
COMMENT ON COLUMN sync_operations.max_retry_attempts IS 'Maximum number of retry attempts';
COMMENT ON COLUMN sync_operations.retry_count IS 'Current retry count';
COMMENT ON COLUMN sync_operations.retry_delay_seconds IS 'Delay between retry attempts in seconds';
COMMENT ON COLUMN sync_operations.notification_enabled IS 'Whether notifications are enabled';
COMMENT ON COLUMN sync_operations.notification_emails IS 'Email addresses for notifications';
COMMENT ON COLUMN sync_operations.notification_webhooks IS 'Webhook URLs for notifications';
COMMENT ON COLUMN sync_operations.metadata IS 'Additional operation metadata (JSONB)';
COMMENT ON COLUMN sync_operations.created_at IS 'Operation creation timestamp';
COMMENT ON COLUMN sync_operations.updated_at IS 'Last update timestamp';
COMMENT ON COLUMN sync_operations.completed_at IS 'Operation completion timestamp';

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sync_operations_server_id ON sync_operations(server_id);
CREATE INDEX IF NOT EXISTS idx_sync_operations_status ON sync_operations(status);
CREATE INDEX IF NOT EXISTS idx_sync_operations_sync_type ON sync_operations(sync_type);
CREATE INDEX IF NOT EXISTS idx_sync_operations_priority ON sync_operations(priority);
CREATE INDEX IF NOT EXISTS idx_sync_operations_next_run ON sync_operations(next_run) WHERE next_run IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sync_operations_created_at ON sync_operations(created_at);
CREATE INDEX IF NOT EXISTS idx_sync_operations_updated_at ON sync_operations(updated_at);