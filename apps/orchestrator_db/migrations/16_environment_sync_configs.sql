-- Migration: Create environment_sync_configs table
-- Description: Stores environment synchronization configurations and settings

-- Create environment_sync_configs table
CREATE TABLE IF NOT EXISTS environment_sync_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Global settings
    default_timeout INTEGER NOT NULL DEFAULT 30 CHECK (default_timeout >= 5 AND default_timeout <= 300),
    default_parallel_limit INTEGER NOT NULL DEFAULT 5 CHECK (default_parallel_limit >= 1 AND default_parallel_limit <= 20),
    default_backup_path VARCHAR(500) NOT NULL DEFAULT '/var/backups/env_sync',

    -- Security settings
    encryption_method VARCHAR(50) NOT NULL DEFAULT 'aes256_gcm' CHECK (encryption_method IN ('aes256_gcm', 'chacha20_poly1305')),
    require_approval_for_production BOOLEAN NOT NULL DEFAULT TRUE,
    audit_log_retention_days INTEGER NOT NULL DEFAULT 90 CHECK (audit_log_retention_days >= 7),

    -- Validation settings
    enforce_validation BOOLEAN NOT NULL DEFAULT TRUE,
    fail_on_validation_error BOOLEAN NOT NULL DEFAULT TRUE,

    -- Notification settings
    notify_on_success BOOLEAN NOT NULL DEFAULT TRUE,
    notify_on_failure BOOLEAN NOT NULL DEFAULT TRUE,
    notification_channels TEXT[] DEFAULT '{}',

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index on name for faster lookups
CREATE INDEX IF NOT EXISTS idx_environment_sync_configs_name ON environment_sync_configs(name);

-- Create index on created_at for ordering
CREATE INDEX IF NOT EXISTS idx_environment_sync_configs_created_at ON environment_sync_configs(created_at DESC);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_environment_sync_configs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_environment_sync_configs_updated_at ON environment_sync_configs;
CREATE TRIGGER trigger_update_environment_sync_configs_updated_at
    BEFORE UPDATE ON environment_sync_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_environment_sync_configs_updated_at();

-- Add comment
COMMENT ON TABLE environment_sync_configs IS 'Complete environment synchronization configuration settings';
COMMENT ON COLUMN environment_sync_configs.id IS 'Configuration UUID primary key';
COMMENT ON COLUMN environment_sync_configs.name IS 'Configuration name';
COMMENT ON COLUMN environment_sync_configs.description IS 'Configuration description';
COMMENT ON COLUMN environment_sync_configs.default_timeout IS 'Default operation timeout in seconds';
COMMENT ON COLUMN environment_sync_configs.default_parallel_limit IS 'Default parallel operations limit';
COMMENT ON COLUMN environment_sync_configs.default_backup_path IS 'Default backup directory path';
COMMENT ON COLUMN environment_sync_configs.encryption_method IS 'Default encryption method';
COMMENT ON COLUMN environment_sync_configs.require_approval_for_production IS 'Require approval for production changes';
COMMENT ON COLUMN environment_sync_configs.audit_log_retention_days IS 'Audit log retention period in days';
COMMENT ON COLUMN environment_sync_configs.enforce_validation IS 'Enforce configuration validation';
COMMENT ON COLUMN environment_sync_configs.fail_on_validation_error IS 'Fail operations on validation errors';
COMMENT ON COLUMN environment_sync_configs.notify_on_success IS 'Send notifications on successful sync';
COMMENT ON COLUMN environment_sync_configs.notify_on_failure IS 'Send notifications on sync failure';
COMMENT ON COLUMN environment_sync_configs.notification_channels IS 'Notification channels list';
COMMENT ON COLUMN environment_sync_configs.metadata IS 'Additional metadata in JSON format';
COMMENT ON COLUMN environment_sync_configs.created_at IS 'Creation timestamp';
COMMENT ON COLUMN environment_sync_configs.updated_at IS 'Last update timestamp';