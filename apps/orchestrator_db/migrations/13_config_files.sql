-- ============================================================================
-- CONFIG_FILES TABLE
-- ============================================================================
-- Configuration file management
--
-- Dependencies: servers (9_servers.sql)
-- Constraints:
--   - file_path must be unique per server

CREATE TABLE IF NOT EXISTS config_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_extension TEXT,
    file_size_bytes BIGINT,
    file_hash TEXT,  -- SHA-256 hash for integrity checking
    file_content TEXT,  -- File content (for small files)
    file_content_type TEXT DEFAULT 'text' CHECK (file_content_type IN ('text', 'binary', 'json', 'yaml', 'xml', 'ini', 'env')),
    encoding TEXT DEFAULT 'utf-8',
    mime_type TEXT,
    config_type TEXT DEFAULT 'custom' CHECK (config_type IN ('application', 'database', 'web_server', 'security', 'logging', 'environment', 'deployment', 'custom')),
    backup_enabled BOOLEAN DEFAULT true,
    backup_retention_count INTEGER DEFAULT 10,
    version_control_enabled BOOLEAN DEFAULT false,
    sync_enabled BOOLEAN DEFAULT true,
    sync_direction TEXT DEFAULT 'bidirectional' CHECK (sync_direction IN ('upload', 'download', 'bidirectional')),
    validation_enabled BOOLEAN DEFAULT true,
    validation_schema JSONB,  -- JSON schema for validation
    encryption_enabled BOOLEAN DEFAULT false,
    compression_enabled BOOLEAN DEFAULT false,
    is_template BOOLEAN DEFAULT false,
    template_variables JSONB DEFAULT '[]'::jsonb,
    auto_reload_services TEXT[],  -- Services to reload after file change
    file_permissions TEXT,  -- File permissions (e.g., '644', '755')
    file_owner TEXT,  -- File owner (user:group)
    last_modified_at TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ,
    sync_status TEXT DEFAULT 'synced' CHECK (sync_status IN ('synced', 'pending_sync', 'sync_failed', 'local_only', 'remote_only', 'conflict')),
    sync_error_message TEXT,
    sync_error_details JSONB,
    checksum TEXT,  -- MD5 checksum for change detection
    version INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint
    CONSTRAINT unique_file_path_per_server UNIQUE (server_id, file_path)
);

-- Table for config file versions/history
CREATE TABLE IF NOT EXISTS config_file_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_file_id UUID NOT NULL REFERENCES config_files(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    file_content TEXT,
    file_size_bytes BIGINT,
    file_hash TEXT,
    change_description TEXT,
    change_type TEXT NOT NULL CHECK (change_type IN ('create', 'update', 'delete', 'restore', 'merge')),
    changed_by TEXT,
    change_reason TEXT,
    backup_location TEXT,  -- Path to backup file if stored externally
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint
    CONSTRAINT unique_version_per_file UNIQUE (config_file_id, version_number)
);

-- Table for config file dependencies
CREATE TABLE IF NOT EXISTS config_file_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_file_id UUID NOT NULL REFERENCES config_files(id) ON DELETE CASCADE,
    dependency_type TEXT NOT NULL CHECK (dependency_type IN ('includes', 'imports', 'references', 'requires', 'extends')),
    dependency_value TEXT NOT NULL,
    dependency_path TEXT,
    is_optional BOOLEAN DEFAULT false,
    validation_enabled BOOLEAN DEFAULT true,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint
    CONSTRAINT unique_dependency UNIQUE (config_file_id, dependency_type, dependency_value)
);

-- Table and column comments
COMMENT ON TABLE config_files IS 'Configuration file management and synchronization';
COMMENT ON COLUMN config_files.id IS 'Unique config file identifier';
COMMENT ON COLUMN config_files.server_id IS 'Foreign key to servers table';
COMMENT ON COLUMN config_files.file_path IS 'Full file path on server';
COMMENT ON COLUMN config_files.file_name IS 'File name without path';
COMMENT ON COLUMN config_files.file_extension IS 'File extension';
COMMENT ON COLUMN config_files.file_size_bytes IS 'File size in bytes';
COMMENT ON COLUMN config_files.file_hash IS 'SHA-256 hash for integrity checking';
COMMENT ON COLUMN config_files.file_content IS 'File content (for small files, otherwise stored externally)';
COMMENT ON COLUMN config_files.file_content_type IS 'Content type: text, binary, json, yaml, xml, ini, env';
COMMENT ON COLUMN config_files.encoding IS 'File encoding (default: utf-8)';
COMMENT ON COLUMN config_files.mime_type IS 'MIME type of the file';
COMMENT ON COLUMN config_files.config_type IS 'Config type: application, database, web_server, security, logging, environment, deployment, custom';
COMMENT ON COLUMN config_files.backup_enabled IS 'Whether automatic backup is enabled';
COMMENT ON COLUMN config_files.backup_retention_count IS 'Number of backup versions to retain';
COMMENT ON COLUMN config_files.version_control_enabled IS 'Whether version control is enabled';
COMMENT ON COLUMN config_files.sync_enabled IS 'Whether synchronization is enabled';
COMMENT ON COLUMN config_files.sync_direction IS 'Sync direction: upload, download, bidirectional';
COMMENT ON COLUMN config_files.validation_enabled IS 'Whether validation is enabled';
COMMENT ON COLUMN config_files.validation_schema IS 'JSON schema for validation';
COMMENT ON COLUMN config_files.encryption_enabled IS 'Whether encryption is enabled for the file';
COMMENT ON COLUMN config_files.compression_enabled IS 'Whether compression is enabled';
COMMENT ON COLUMN config_files.is_template IS 'Whether this is a template file';
COMMENT ON COLUMN config_files.template_variables IS 'Array of template variables (JSONB)';
COMMENT ON COLUMN config_files.auto_reload_services IS 'Services to reload after file change';
COMMENT ON COLUMN config_files.file_permissions IS 'File permissions (e.g., 644, 755)';
COMMENT ON COLUMN config_files.file_owner IS 'File owner (user:group)';
COMMENT ON COLUMN config_files.last_modified_at IS 'Last modification timestamp on server';
COMMENT ON COLUMN config_files.last_synced_at IS 'Last synchronization timestamp';
COMMENT ON COLUMN config_files.sync_status IS 'Sync status: synced, pending_sync, sync_failed, local_only, remote_only, conflict';
COMMENT ON COLUMN config_files.sync_error_message IS 'Sync error message (if failed)';
COMMENT ON COLUMN config_files.sync_error_details IS 'Detailed sync error information (JSONB)';
COMMENT ON COLUMN config_files.checksum IS 'MD5 checksum for change detection';
COMMENT ON COLUMN config_files.version IS 'Current version number';
COMMENT ON COLUMN config_files.metadata IS 'Additional file metadata (JSONB)';
COMMENT ON COLUMN config_files.created_at IS 'File record creation timestamp';
COMMENT ON COLUMN config_files.updated_at IS 'Last update timestamp';

COMMENT ON TABLE config_file_versions IS 'Version history for configuration files';
COMMENT ON COLUMN config_file_versions.id IS 'Unique version identifier';
COMMENT ON COLUMN config_file_versions.config_file_id IS 'Foreign key to config_files table';
COMMENT ON COLUMN config_file_versions.version_number IS 'Version number';
COMMENT ON COLUMN config_file_versions.file_content IS 'File content at this version';
COMMENT ON COLUMN config_file_versions.file_size_bytes IS 'File size at this version';
COMMENT ON COLUMN config_file_versions.file_hash IS 'File hash at this version';
COMMENT ON COLUMN config_file_versions.change_description IS 'Description of changes';
COMMENT ON COLUMN config_file_versions.change_type IS 'Change type: create, update, delete, restore, merge';
COMMENT ON COLUMN config_file_versions.changed_by IS 'Who made the change';
COMMENT ON COLUMN config_file_versions.change_reason IS 'Reason for the change';
COMMENT ON COLUMN config_file_versions.backup_location IS 'Path to backup file if stored externally';
COMMENT ON COLUMN config_file_versions.metadata IS 'Additional version metadata (JSONB)';
COMMENT ON COLUMN config_file_versions.created_at IS 'Version creation timestamp';

COMMENT ON TABLE config_file_dependencies IS 'Dependencies between configuration files';
COMMENT ON COLUMN config_file_dependencies.id IS 'Unique dependency identifier';
COMMENT ON COLUMN config_file_dependencies.config_file_id IS 'Foreign key to config_files table';
COMMENT ON COLUMN config_file_dependencies.dependency_type IS 'Dependency type: includes, imports, references, requires, extends';
COMMENT ON COLUMN config_file_dependencies.dependency_value IS 'Dependency value';
COMMENT ON COLUMN config_file_dependencies.dependency_path IS 'Dependency path if applicable';
COMMENT ON COLUMN config_file_dependencies.is_optional IS 'Whether the dependency is optional';
COMMENT ON COLUMN config_file_dependencies.validation_enabled IS 'Whether dependency validation is enabled';
COMMENT ON COLUMN config_file_dependencies.description IS 'Dependency description';
COMMENT ON COLUMN config_file_dependencies.created_at IS 'Dependency creation timestamp';

-- Indexes for config_files
CREATE INDEX IF NOT EXISTS idx_config_files_server_id ON config_files(server_id);
CREATE INDEX IF NOT EXISTS idx_config_files_file_path ON config_files(file_path);
CREATE INDEX IF NOT EXISTS idx_config_files_file_name ON config_files(file_name);
CREATE INDEX IF NOT EXISTS idx_config_files_file_extension ON config_files(file_extension);
CREATE INDEX IF NOT EXISTS idx_config_files_config_type ON config_files(config_type);
CREATE INDEX IF NOT EXISTS idx_config_files_sync_enabled ON config_files(sync_enabled);
CREATE INDEX IF NOT EXISTS idx_config_files_sync_status ON config_files(sync_status);
CREATE INDEX IF NOT EXISTS idx_config_files_last_synced_at ON config_files(last_synced_at);
CREATE INDEX IF NOT EXISTS idx_config_files_updated_at ON config_files(updated_at);
CREATE INDEX IF NOT EXISTS idx_config_files_is_template ON config_files(is_template);

-- Indexes for config_file_versions
CREATE INDEX IF NOT EXISTS idx_config_file_versions_config_file_id ON config_file_versions(config_file_id);
CREATE INDEX IF NOT EXISTS idx_config_file_versions_version_number ON config_file_versions(version_number);
CREATE INDEX IF NOT EXISTS idx_config_file_versions_created_at ON config_file_versions(created_at);
CREATE INDEX IF NOT EXISTS idx_config_file_versions_change_type ON config_file_versions(change_type);

-- Indexes for config_file_dependencies
CREATE INDEX IF NOT EXISTS idx_config_file_dependencies_config_file_id ON config_file_dependencies(config_file_id);
CREATE INDEX IF NOT EXISTS idx_config_file_dependencies_dependency_type ON config_file_dependencies(dependency_type);