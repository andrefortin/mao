-- ============================================================================
-- SYNC_OPERATION_LOGS TABLE
-- ============================================================================
-- Detailed operation logging for sync activities
--
-- Dependencies: sync_operations (10_sync_operations.sql), servers (9_servers.sql)
-- Constraints: None (this is a log table)

CREATE TABLE IF NOT EXISTS sync_operation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_operation_id UUID REFERENCES sync_operations(id) ON DELETE CASCADE,
    server_id UUID REFERENCES servers(id) ON DELETE CASCADE,
    batch_operation_id UUID REFERENCES batch_operations(id) ON DELETE SET NULL,
    log_level TEXT NOT NULL CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    log_category TEXT NOT NULL CHECK (log_category IN ('connection', 'authentication', 'file_transfer', 'validation', 'backup', 'cleanup', 'system', 'performance', 'security')),
    log_type TEXT NOT NULL,
    message TEXT NOT NULL,
    message_details JSONB DEFAULT '{}'::jsonb,
    source_component TEXT,  -- Which component generated the log
    source_function TEXT,  -- Which function generated the log
    file_path TEXT,  -- File path if log is file-specific
    operation_step TEXT,  -- Current step in the operation
    step_status TEXT CHECK (step_status IN ('started', 'in_progress', 'completed', 'failed', 'skipped')),
    execution_time_ms BIGINT,
    bytes_transferred BIGINT,
    files_transferred INTEGER,
    transfer_rate_mbps NUMERIC(10,2),
    error_code TEXT,
    error_severity TEXT CHECK (error_severity IN ('low', 'medium', 'high', 'critical')),
    stack_trace TEXT,
    context_data JSONB DEFAULT '{}'::jsonb,
    performance_metrics JSONB DEFAULT '{}'::jsonb,
    network_info JSONB DEFAULT '{}'::jsonb,
    system_info JSONB DEFAULT '{}'::jsonb,
    retry_attempt INTEGER,
    retry_reason TEXT,
    session_id TEXT,
    correlation_id TEXT,  -- For tracing related logs across operations
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table for operation metrics and statistics
CREATE TABLE IF NOT EXISTS operation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_operation_id UUID NOT NULL REFERENCES sync_operations(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL CHECK (metric_type IN ('duration', 'throughput', 'success_rate', 'error_rate', 'resource_usage', 'network_quality')),
    metric_name TEXT NOT NULL,
    metric_value NUMERIC(15,4) NOT NULL,
    metric_unit TEXT,  -- e.g., 'seconds', 'MB/s', 'percentage', 'count'
    measurement_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    comparison_value NUMERIC(15,4),  -- For comparison with baseline or previous value
    comparison_percentage NUMERIC(5,2),  -- Percentage change from comparison value
    is_anomaly BOOLEAN DEFAULT false,
    anomaly_score NUMERIC(3,2),  -- Anomaly score (0-1)
    threshold_value NUMERIC(15,4),  -- Threshold for alerting
    threshold_breached BOOLEAN DEFAULT false,
    alert_sent BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table for operation events (significant milestones)
CREATE TABLE IF NOT EXISTS operation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_operation_id UUID NOT NULL REFERENCES sync_operations(id) ON DELETE CASCADE,
    server_id UUID REFERENCES servers(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('started', 'connected', 'authenticated', 'transfer_started', 'transfer_completed', 'validation_started', 'validation_completed', 'backup_created', 'cleanup_started', 'cleanup_completed', 'error_occurred', 'retry_started', 'operation_completed', 'operation_cancelled', 'operation_paused', 'operation_resumed')),
    event_name TEXT NOT NULL,
    event_description TEXT,
    event_severity TEXT DEFAULT 'info' CHECK (event_severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    event_data JSONB DEFAULT '{}'::jsonb,
    previous_state TEXT,
    current_state TEXT,
    duration_seconds BIGINT,
    progress_percentage NUMERIC(5,2) CHECK (progress_percentage BETWEEN 0 AND 100),
    affected_items JSONB DEFAULT '[]'::jsonb,  -- List of affected files, directories, etc.
    automated_action BOOLEAN DEFAULT false,
    action_taken TEXT,
    action_result TEXT,
    notification_sent BOOLEAN DEFAULT false,
    notification_channels TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table and column comments
COMMENT ON TABLE sync_operation_logs IS 'Detailed operation logging for sync activities';
COMMENT ON COLUMN sync_operation_logs.id IS 'Unique log entry identifier';
COMMENT ON COLUMN sync_operation_logs.sync_operation_id IS 'Foreign key to sync_operations table';
COMMENT ON COLUMN sync_operation_logs.server_id IS 'Foreign key to servers table';
COMMENT ON COLUMN sync_operation_logs.batch_operation_id IS 'Foreign key to batch_operations table';
COMMENT ON COLUMN sync_operation_logs.log_level IS 'Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL';
COMMENT ON COLUMN sync_operation_logs.log_category IS 'Log category: connection, authentication, file_transfer, validation, backup, cleanup, system, performance, security';
COMMENT ON COLUMN sync_operation_logs.log_type IS 'Specific log type within the category';
COMMENT ON COLUMN sync_operation_logs.message IS 'Log message';
COMMENT ON COLUMN sync_operation_logs.message_details IS 'Detailed log message information (JSONB)';
COMMENT ON COLUMN sync_operation_logs.source_component IS 'Component that generated the log';
COMMENT ON COLUMN sync_operation_logs.source_function IS 'Function that generated the log';
COMMENT ON COLUMN sync_operation_logs.file_path IS 'File path if log is file-specific';
COMMENT ON COLUMN sync_operation_logs.operation_step IS 'Current step in the operation';
COMMENT ON COLUMN sync_operation_logs.step_status IS 'Step status: started, in_progress, completed, failed, skipped';
COMMENT ON COLUMN sync_operation_logs.execution_time_ms IS 'Execution time in milliseconds';
COMMENT ON COLUMN sync_operation_logs.bytes_transferred IS 'Number of bytes transferred';
COMMENT ON COLUMN sync_operation_logs.files_transferred IS 'Number of files transferred';
COMMENT ON COLUMN sync_operation_logs.transfer_rate_mbps IS 'Transfer rate in MB/s';
COMMENT ON COLUMN sync_operation_logs.error_code IS 'Error code if applicable';
COMMENT ON COLUMN sync_operation_logs.error_severity IS 'Error severity: low, medium, high, critical';
COMMENT ON COLUMN sync_operation_logs.stack_trace IS 'Stack trace for errors';
COMMENT ON COLUMN sync_operation_logs.context_data IS 'Contextual information (JSONB)';
COMMENT ON COLUMN sync_operation_logs.performance_metrics IS 'Performance metrics (JSONB)';
COMMENT ON COLUMN sync_operation_logs.network_info IS 'Network information (JSONB)';
COMMENT ON COLUMN sync_operation_logs.system_info IS 'System information (JSONB)';
COMMENT ON COLUMN sync_operation_logs.retry_attempt IS 'Retry attempt number';
COMMENT ON COLUMN sync_operation_logs.retry_reason IS 'Reason for retry';
COMMENT ON COLUMN sync_operation_logs.session_id IS 'Session identifier';
COMMENT ON COLUMN sync_operation_logs.correlation_id IS 'Correlation ID for tracing related logs';
COMMENT ON COLUMN sync_operation_logs.tags IS 'Array of tags for categorization';
COMMENT ON COLUMN sync_operation_logs.metadata IS 'Additional log metadata (JSONB)';
COMMENT ON COLUMN sync_operation_logs.timestamp IS 'Log timestamp';

COMMENT ON TABLE operation_metrics IS 'Operation metrics and statistics';
COMMENT ON COLUMN operation_metrics.id IS 'Unique metric identifier';
COMMENT ON COLUMN operation_metrics.sync_operation_id IS 'Foreign key to sync_operations table';
COMMENT ON COLUMN operation_metrics.metric_type IS 'Metric type: duration, throughput, success_rate, error_rate, resource_usage, network_quality';
COMMENT ON COLUMN operation_metrics.metric_name IS 'Metric name';
COMMENT ON COLUMN operation_metrics.metric_value IS 'Metric value';
COMMENT ON COLUMN operation_metrics.metric_unit IS 'Metric unit: seconds, MB/s, percentage, count';
COMMENT ON COLUMN operation_metrics.measurement_time IS 'Time when metric was measured';
COMMENT ON COLUMN operation_metrics.comparison_value IS 'Value for comparison (baseline or previous)';
COMMENT ON COLUMN operation_metrics.comparison_percentage IS 'Percentage change from comparison value';
COMMENT ON COLUMN operation_metrics.is_anomaly IS 'Whether this metric indicates an anomaly';
COMMENT ON COLUMN operation_metrics.anomaly_score IS 'Anomaly score (0-1)';
COMMENT ON COLUMN operation_metrics.threshold_value IS 'Threshold value for alerting';
COMMENT ON COLUMN operation_metrics.threshold_breached IS 'Whether threshold was breached';
COMMENT ON COLUMN operation_metrics.alert_sent IS 'Whether alert was sent';
COMMENT ON COLUMN operation_metrics.metadata IS 'Additional metric metadata (JSONB)';
COMMENT ON COLUMN operation_metrics.created_at IS 'Metric creation timestamp';

COMMENT ON TABLE operation_events IS 'Significant operation events and milestones';
COMMENT ON COLUMN operation_events.id IS 'Unique event identifier';
COMMENT ON COLUMN operation_events.sync_operation_id IS 'Foreign key to sync_operations table';
COMMENT ON COLUMN operation_events.server_id IS 'Foreign key to servers table';
COMMENT ON COLUMN operation_events.event_type IS 'Event type: started, connected, authenticated, transfer_started, transfer_completed, validation_started, validation_completed, backup_created, cleanup_started, cleanup_completed, error_occurred, retry_started, operation_completed, operation_cancelled, operation_paused, operation_resumed';
COMMENT ON COLUMN operation_events.event_name IS 'Event name';
COMMENT ON COLUMN operation_events.event_description IS 'Event description';
COMMENT ON COLUMN operation_events.event_severity IS 'Event severity: debug, info, warning, error, critical';
COMMENT ON COLUMN operation_events.event_data IS 'Event-specific data (JSONB)';
COMMENT ON COLUMN operation_events.previous_state IS 'Previous state before event';
COMMENT ON COLUMN operation_events.current_state IS 'Current state after event';
COMMENT ON COLUMN operation_events.duration_seconds IS 'Event duration in seconds';
COMMENT ON COLUMN operation_events.progress_percentage IS 'Progress percentage (0-100)';
COMMENT ON COLUMN operation_events.affected_items IS 'List of affected items (JSONB)';
COMMENT ON COLUMN operation_events.automated_action IS 'Whether automated action was taken';
COMMENT ON COLUMN operation_events.action_taken IS 'Action that was taken';
COMMENT ON COLUMN operation_events.action_result IS 'Result of the action';
COMMENT ON COLUMN operation_events.notification_sent IS 'Whether notification was sent';
COMMENT ON COLUMN operation_events.notification_channels IS 'Channels used for notification';
COMMENT ON COLUMN operation_events.metadata IS 'Additional event metadata (JSONB)';
COMMENT ON COLUMN operation_events.timestamp IS 'Event timestamp';

-- Indexes for sync_operation_logs
CREATE INDEX IF NOT EXISTS idx_sync_operation_logs_sync_operation_id ON sync_operation_logs(sync_operation_id);
CREATE INDEX IF NOT EXISTS idx_sync_operation_logs_server_id ON sync_operation_logs(server_id);
CREATE INDEX IF NOT EXISTS idx_sync_operation_logs_batch_operation_id ON sync_operation_logs(batch_operation_id);
CREATE INDEX IF NOT EXISTS idx_sync_operation_logs_log_level ON sync_operation_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_sync_operation_logs_log_category ON sync_operation_logs(log_category);
CREATE INDEX IF NOT EXISTS idx_sync_operation_logs_timestamp ON sync_operation_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_sync_operation_logs_correlation_id ON sync_operation_logs(correlation_id) WHERE correlation_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sync_operation_logs_tags ON sync_operation_logs USING GIN(tags);

-- Indexes for operation_metrics
CREATE INDEX IF NOT EXISTS idx_operation_metrics_sync_operation_id ON operation_metrics(sync_operation_id);
CREATE INDEX IF NOT EXISTS idx_operation_metrics_metric_type ON operation_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_operation_metrics_metric_name ON operation_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_operation_metrics_measurement_time ON operation_metrics(measurement_time);
CREATE INDEX IF NOT EXISTS idx_operation_metrics_is_anomaly ON operation_metrics(is_anomaly);
CREATE INDEX IF NOT EXISTS idx_operation_metrics_threshold_breached ON operation_metrics(threshold_breached);

-- Indexes for operation_events
CREATE INDEX IF NOT EXISTS idx_operation_events_sync_operation_id ON operation_events(sync_operation_id);
CREATE INDEX IF NOT EXISTS idx_operation_events_server_id ON operation_events(server_id);
CREATE INDEX IF NOT EXISTS idx_operation_events_event_type ON operation_events(event_type);
CREATE INDEX IF NOT EXISTS idx_operation_events_event_severity ON operation_events(event_severity);
CREATE INDEX IF NOT EXISTS idx_operation_events_timestamp ON operation_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_operation_events_notification_sent ON operation_events(notification_sent) WHERE notification_sent = true;