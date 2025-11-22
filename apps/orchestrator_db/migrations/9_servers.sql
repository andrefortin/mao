-- ============================================================================
-- SERVERS TABLE
-- ============================================================================
-- Server definitions and configurations for environment synchronization
--
-- Dependencies: None
-- Constraints:
--   - hostname must be unique per orchestrator
--   - ip_address must be unique (no duplicate IPs)

CREATE TABLE IF NOT EXISTS servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    orchestrator_agent_id UUID NOT NULL REFERENCES orchestrator_agents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    hostname TEXT NOT NULL,
    ip_address INET NOT NULL,
    port INTEGER NOT NULL DEFAULT 22,
    connection_type TEXT NOT NULL CHECK (connection_type IN ('ssh', 'sftp', 'ftp', 'sftp_with_key', 'sftp_with_password')),
    username TEXT NOT NULL,
    password TEXT,  -- Encrypted password
    private_key_path TEXT,
    private_key_passphrase TEXT,  -- Encrypted passphrase
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    environment_type TEXT NOT NULL CHECK (environment_type IN ('development', 'staging', 'production', 'testing', 'local')),
    status TEXT NOT NULL DEFAULT 'inactive' CHECK (status IN ('active', 'inactive', 'maintenance', 'error')),
    health_check_url TEXT,
    health_check_interval INTEGER DEFAULT 300,  -- seconds
    last_health_check TIMESTAMPTZ,
    health_status TEXT DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'unhealthy', 'unknown')),
    connection_timeout INTEGER DEFAULT 30,
    max_parallel_operations INTEGER DEFAULT 5,
    backup_enabled BOOLEAN DEFAULT true,
    backup_retention_days INTEGER DEFAULT 30,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraints
    CONSTRAINT unique_hostname_per_orchestrator UNIQUE (orchestrator_agent_id, hostname),
    CONSTRAINT unique_ip_address UNIQUE (ip_address)
);

-- Table and column comments
COMMENT ON TABLE servers IS 'Server definitions and configurations for environment synchronization';
COMMENT ON COLUMN servers.id IS 'Unique server identifier';
COMMENT ON COLUMN servers.orchestrator_agent_id IS 'Foreign key to orchestrator_agents table';
COMMENT ON COLUMN servers.name IS 'Human-readable server name';
COMMENT ON COLUMN servers.hostname IS 'Server hostname (FQDN)';
COMMENT ON COLUMN servers.ip_address IS 'Server IP address (unique)';
COMMENT ON COLUMN servers.port IS 'Connection port (default: 22 for SSH/SFTP)';
COMMENT ON COLUMN servers.connection_type IS 'Connection method: ssh, sftp, ftp, sftp_with_key, sftp_with_password';
COMMENT ON COLUMN servers.username IS 'SSH/FTP username';
COMMENT ON COLUMN servers.password IS 'Encrypted password for authentication';
COMMENT ON COLUMN servers.private_key_path IS 'Path to private key file';
COMMENT ON COLUMN servers.private_key_passphrase IS 'Encrypted passphrase for private key';
COMMENT ON COLUMN servers.description IS 'Server description and purpose';
COMMENT ON COLUMN servers.tags IS 'Array of server tags for grouping and filtering';
COMMENT ON COLUMN servers.environment_type IS 'Environment type: development, staging, production, testing, local';
COMMENT ON COLUMN servers.status IS 'Server status: active, inactive, maintenance, error';
COMMENT ON COLUMN servers.health_check_url IS 'URL for health check endpoint';
COMMENT ON COLUMN servers.health_check_interval IS 'Health check interval in seconds';
COMMENT ON COLUMN servers.last_health_check IS 'Timestamp of last health check';
COMMENT ON COLUMN servers.health_status IS 'Health check result: healthy, unhealthy, unknown';
COMMENT ON COLUMN servers.connection_timeout IS 'Connection timeout in seconds';
COMMENT ON COLUMN servers.max_parallel_operations IS 'Maximum parallel sync operations';
COMMENT ON COLUMN servers.backup_enabled IS 'Whether automatic backups are enabled';
COMMENT ON COLUMN servers.backup_retention_days IS 'Number of days to retain backups';
COMMENT ON COLUMN servers.metadata IS 'Additional server configuration (JSONB)';
COMMENT ON COLUMN servers.created_at IS 'Server creation timestamp';
COMMENT ON COLUMN servers.updated_at IS 'Last update timestamp';

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_servers_orchestrator_agent_id ON servers(orchestrator_agent_id);
CREATE INDEX IF NOT EXISTS idx_servers_hostname ON servers(hostname);
CREATE INDEX IF NOT EXISTS idx_servers_ip_address ON servers(ip_address);
CREATE INDEX IF NOT EXISTS idx_servers_environment_type ON servers(environment_type);
CREATE INDEX IF NOT EXISTS idx_servers_status ON servers(status);
CREATE INDEX IF NOT EXISTS idx_servers_health_status ON servers(health_status);
CREATE INDEX IF NOT EXISTS idx_servers_tags ON servers USING GIN(tags);