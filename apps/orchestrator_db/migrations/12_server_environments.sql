-- ============================================================================
-- SERVER_ENVIRONMENTS TABLE
-- ============================================================================
-- Environment variable storage for servers
--
-- Dependencies: servers (9_servers.sql)
-- Constraints:
--   - variable_name must be unique per server (with optional environment_type)

CREATE TABLE IF NOT EXISTS server_environments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
    variable_name TEXT NOT NULL,
    variable_value TEXT NOT NULL,
    environment_type TEXT DEFAULT 'default' CHECK (environment_type IN ('default', 'development', 'staging', 'production', 'testing', 'custom')),
    is_encrypted BOOLEAN DEFAULT false,
    is_sensitive BOOLEAN DEFAULT false,
    description TEXT,
    variable_type TEXT DEFAULT 'string' CHECK (variable_type IN ('string', 'number', 'boolean', 'json', 'url', 'email', 'path', 'port')),
    is_required BOOLEAN DEFAULT false,
    default_value TEXT,
    validation_pattern TEXT,  -- Regex pattern for validation
    source TEXT DEFAULT 'manual' CHECK (source IN ('manual', 'imported', 'synced', 'generated', 'discovered')),
    last_synced_at TIMESTAMPTZ,
    sync_status TEXT DEFAULT 'synced' CHECK (sync_status IN ('synced', 'pending_sync', 'sync_failed', 'local_only')),
    checksum TEXT,  -- MD5 checksum for change detection
    version INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraints
    CONSTRAINT unique_variable_name_per_server UNIQUE (server_id, variable_name, environment_type)
);

-- Table for environment variable groups
CREATE TABLE IF NOT EXISTS environment_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID NOT NULL REFERENCES servers(id) ON DELETE CASCADE,
    group_name TEXT NOT NULL,
    description TEXT,
    group_type TEXT DEFAULT 'custom' CHECK (group_type IN ('application', 'database', 'infrastructure', 'security', 'monitoring', 'custom')),
    is_active BOOLEAN DEFAULT true,
    auto_sync_enabled BOOLEAN DEFAULT true,
    sync_priority INTEGER DEFAULT 5 CHECK (sync_priority BETWEEN 1 AND 10),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint
    CONSTRAINT unique_group_name_per_server UNIQUE (server_id, group_name)
);

-- Junction table for environment variable to group relationships
CREATE TABLE IF NOT EXISTS environment_group_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    environment_group_id UUID NOT NULL REFERENCES environment_groups(id) ON DELETE CASCADE,
    environment_variable_id UUID NOT NULL REFERENCES server_environments(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    added_by TEXT,  -- Who added this variable to the group

    -- Unique constraint
    CONSTRAINT unique_group_member UNIQUE (environment_group_id, environment_variable_id)
);

-- Table and column comments
COMMENT ON TABLE server_environments IS 'Environment variable storage for servers';
COMMENT ON COLUMN server_environments.id IS 'Unique environment variable identifier';
COMMENT ON COLUMN server_environments.server_id IS 'Foreign key to servers table';
COMMENT ON COLUMN server_environments.variable_name IS 'Environment variable name';
COMMENT ON COLUMN server_environments.variable_value IS 'Environment variable value (encrypted if sensitive)';
COMMENT ON COLUMN server_environments.environment_type IS 'Environment type: default, development, staging, production, testing, custom';
COMMENT ON COLUMN server_environments.is_encrypted IS 'Whether the value is encrypted at rest';
COMMENT ON COLUMN server_environments.is_sensitive IS 'Whether the variable contains sensitive data';
COMMENT ON COLUMN server_environments.description IS 'Variable description and purpose';
COMMENT ON COLUMN server_environments.variable_type IS 'Variable type: string, number, boolean, json, url, email, path, port';
COMMENT ON COLUMN server_environments.is_required IS 'Whether the variable is required for operation';
COMMENT ON COLUMN server_environments.default_value IS 'Default value if not set';
COMMENT ON COLUMN server_environments.validation_pattern IS 'Regex pattern for validation';
COMMENT ON COLUMN server_environments.source IS 'Source of the variable: manual, imported, synced, generated, discovered';
COMMENT ON COLUMN server_environments.last_synced_at IS 'Last synchronization timestamp';
COMMENT ON COLUMN server_environments.sync_status IS 'Sync status: synced, pending_sync, sync_failed, local_only';
COMMENT ON COLUMN server_environments.checksum IS 'MD5 checksum for change detection';
COMMENT ON COLUMN server_environments.version IS 'Version number for tracking changes';
COMMENT ON COLUMN server_environments.metadata IS 'Additional variable metadata (JSONB)';
COMMENT ON COLUMN server_environments.created_at IS 'Variable creation timestamp';
COMMENT ON COLUMN server_environments.updated_at IS 'Last update timestamp';

COMMENT ON TABLE environment_groups IS 'Groups for organizing environment variables';
COMMENT ON COLUMN environment_groups.id IS 'Unique group identifier';
COMMENT ON COLUMN environment_groups.server_id IS 'Foreign key to servers table';
COMMENT ON COLUMN environment_groups.group_name IS 'Group name (unique per server)';
COMMENT ON COLUMN environment_groups.description IS 'Group description and purpose';
COMMENT ON COLUMN environment_groups.group_type IS 'Group type: application, database, infrastructure, security, monitoring, custom';
COMMENT ON COLUMN environment_groups.is_active IS 'Whether the group is active';
COMMENT ON COLUMN environment_groups.auto_sync_enabled IS 'Whether automatic sync is enabled for this group';
COMMENT ON COLUMN environment_groups.sync_priority IS 'Sync priority (1-10, lower number = higher priority)';
COMMENT ON COLUMN environment_groups.metadata IS 'Additional group metadata (JSONB)';
COMMENT ON COLUMN environment_groups.created_at IS 'Group creation timestamp';
COMMENT ON COLUMN environment_groups.updated_at IS 'Last update timestamp';

COMMENT ON TABLE environment_group_members IS 'Junction table linking environment variables to groups';
COMMENT ON COLUMN environment_group_members.id IS 'Unique group member identifier';
COMMENT ON COLUMN environment_group_members.environment_group_id IS 'Foreign key to environment_groups table';
COMMENT ON COLUMN environment_group_members.environment_variable_id IS 'Foreign key to server_environments table';
COMMENT ON COLUMN environment_group_members.added_at IS 'Timestamp when variable was added to group';
COMMENT ON COLUMN environment_group_members.added_by IS 'Who added this variable to the group';

-- Indexes for server_environments
CREATE INDEX IF NOT EXISTS idx_server_environments_server_id ON server_environments(server_id);
CREATE INDEX IF NOT EXISTS idx_server_environments_variable_name ON server_environments(variable_name);
CREATE INDEX IF NOT EXISTS idx_server_environments_environment_type ON server_environments(environment_type);
CREATE INDEX IF NOT EXISTS idx_server_environments_is_encrypted ON server_environments(is_encrypted);
CREATE INDEX IF NOT EXISTS idx_server_environments_is_sensitive ON server_environments(is_sensitive);
CREATE INDEX IF NOT EXISTS idx_server_environments_sync_status ON server_environments(sync_status);
CREATE INDEX IF NOT EXISTS idx_server_environments_updated_at ON server_environments(updated_at);
CREATE INDEX IF NOT EXISTS idx_server_environments_source ON server_environments(source);

-- Indexes for environment_groups
CREATE INDEX IF NOT EXISTS idx_environment_groups_server_id ON environment_groups(server_id);
CREATE INDEX IF NOT EXISTS idx_environment_groups_group_name ON environment_groups(group_name);
CREATE INDEX IF NOT EXISTS idx_environment_groups_group_type ON environment_groups(group_type);
CREATE INDEX IF NOT EXISTS idx_environment_groups_is_active ON environment_groups(is_active);
CREATE INDEX IF NOT EXISTS idx_environment_groups_sync_priority ON environment_groups(sync_priority);

-- Indexes for environment_group_members
CREATE INDEX IF NOT EXISTS idx_environment_group_members_group_id ON environment_group_members(environment_group_id);
CREATE INDEX IF NOT EXISTS idx_environment_group_members_variable_id ON environment_group_members(environment_variable_id);