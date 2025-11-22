-- ============================================================================
-- SYNC_BATCHES TABLE
-- ============================================================================
-- Batch operation management for grouping and scheduling multiple sync operations
--
-- Dependencies: sync_operations (10_sync_operations.sql)
-- Constraints:
--   - batch_name must be unique per orchestrator

CREATE TABLE IF NOT EXISTS sync_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    orchestrator_agent_id UUID NOT NULL REFERENCES orchestrator_agents(id) ON DELETE CASCADE,
    batch_name TEXT NOT NULL,
    description TEXT,
    batch_type TEXT NOT NULL CHECK (batch_type IN ('manual', 'scheduled', 'triggered', 'emergency')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled', 'paused')),
    execution_order TEXT CHECK (execution_order IN ('sequential', 'parallel', 'priority_based')),
    max_parallel_operations INTEGER DEFAULT 3,
    continue_on_failure BOOLEAN DEFAULT false,
    stop_on_first_failure BOOLEAN DEFAULT false,
    schedule_expression TEXT,  -- Cron expression
    next_run TIMESTAMPTZ,
    last_run TIMESTAMPTZ,
    run_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    total_operations INTEGER DEFAULT 0,
    completed_operations INTEGER DEFAULT 0,
    failed_operations INTEGER DEFAULT 0,
    total_duration_seconds BIGINT DEFAULT 0,
    average_duration_seconds NUMERIC(10,2) DEFAULT 0.00,
    batch_options JSONB DEFAULT '{
        "rollback_on_failure": false,
        "create_backup_before_batch": true,
        "send_summary_report": true,
        "timeout_minutes": 60,
        "retry_failed_operations": true,
        "max_batch_retries": 1
    }'::jsonb,
    error_summary TEXT,
    error_details JSONB,
    progress_percentage NUMERIC(5,2) DEFAULT 0.00 CHECK (progress_percentage BETWEEN 0 AND 100),
    estimated_completion TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint
    CONSTRAINT unique_batch_name_per_orchestrator UNIQUE (orchestrator_agent_id, batch_name)
);

-- Junction table for batch-to-operation relationships
CREATE TABLE IF NOT EXISTS batch_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES sync_batches(id) ON DELETE CASCADE,
    sync_operation_id UUID NOT NULL REFERENCES sync_operations(id) ON DELETE CASCADE,
    execution_order INTEGER DEFAULT 0,
    execution_status TEXT DEFAULT 'pending' CHECK (execution_status IN ('pending', 'in_progress', 'completed', 'failed', 'skipped')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds BIGINT,
    result_message TEXT,
    result_details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint
    CONSTRAINT unique_batch_operation UNIQUE (batch_id, sync_operation_id)
);

-- Table and column comments
COMMENT ON TABLE sync_batches IS 'Batch operation management for grouping and scheduling multiple sync operations';
COMMENT ON COLUMN sync_batches.id IS 'Unique batch identifier';
COMMENT ON COLUMN sync_batches.orchestrator_agent_id IS 'Foreign key to orchestrator_agents table';
COMMENT ON COLUMN sync_batches.batch_name IS 'Human-readable batch name (unique per orchestrator)';
COMMENT ON COLUMN sync_batches.description IS 'Batch description and purpose';
COMMENT ON COLUMN sync_batches.batch_type IS 'Batch type: manual, scheduled, triggered, emergency';
COMMENT ON COLUMN sync_batches.status IS 'Batch status: pending, in_progress, completed, failed, cancelled, paused';
COMMENT ON COLUMN sync_batches.execution_order IS 'Execution order: sequential, parallel, priority_based';
COMMENT ON COLUMN sync_batches.max_parallel_operations IS 'Maximum parallel operations in batch';
COMMENT ON COLUMN sync_batches.continue_on_failure IS 'Continue batch if individual operations fail';
COMMENT ON COLUMN sync_batches.stop_on_first_failure IS 'Stop batch on first operation failure';
COMMENT ON COLUMN sync_batches.schedule_expression IS 'Cron expression for scheduled batches';
COMMENT ON COLUMN sync_batches.next_run IS 'Next scheduled run time';
COMMENT ON COLUMN sync_batches.last_run IS 'Last batch execution timestamp';
COMMENT ON COLUMN sync_batches.run_count IS 'Total number of times batch has run';
COMMENT ON COLUMN sync_batches.success_count IS 'Number of successful batch runs';
COMMENT ON COLUMN sync_batches.failure_count IS 'Number of failed batch runs';
COMMENT ON COLUMN sync_batches.total_operations IS 'Total operations in batch';
COMMENT ON COLUMN sync_batches.completed_operations IS 'Number of completed operations';
COMMENT ON COLUMN sync_batches.failed_operations IS 'Number of failed operations';
COMMENT ON COLUMN sync_batches.total_duration_seconds IS 'Total execution time across all runs';
COMMENT ON COLUMN sync_batches.average_duration_seconds IS 'Average execution time per run';
COMMENT ON COLUMN sync_batches.batch_options IS 'Batch configuration options (JSONB)';
COMMENT ON COLUMN sync_batches.error_summary IS 'Summary of batch errors (if failed)';
COMMENT ON COLUMN sync_batches.error_details IS 'Detailed error information (JSONB)';
COMMENT ON COLUMN sync_batches.progress_percentage IS 'Current batch progress percentage (0-100)';
COMMENT ON COLUMN sync_batches.estimated_completion IS 'Estimated batch completion time';
COMMENT ON COLUMN sync_batches.started_at IS 'Batch start timestamp';
COMMENT ON COLUMN sync_batches.completed_at IS 'Batch completion timestamp';
COMMENT ON COLUMN sync_batches.metadata IS 'Additional batch metadata (JSONB)';
COMMENT ON COLUMN sync_batches.created_at IS 'Batch creation timestamp';
COMMENT ON COLUMN sync_batches.updated_at IS 'Last update timestamp';

COMMENT ON TABLE batch_operations IS 'Junction table linking batches to sync operations';
COMMENT ON COLUMN batch_operations.id IS 'Unique batch operation identifier';
COMMENT ON COLUMN batch_operations.batch_id IS 'Foreign key to sync_batches table';
COMMENT ON COLUMN batch_operations.sync_operation_id IS 'Foreign key to sync_operations table';
COMMENT ON COLUMN batch_operations.execution_order IS 'Order of execution within the batch';
COMMENT ON COLUMN batch_operations.execution_status IS 'Operation execution status';
COMMENT ON COLUMN batch_operations.started_at IS 'Operation start timestamp';
COMMENT ON COLUMN batch_operations.completed_at IS 'Operation completion timestamp';
COMMENT ON COLUMN batch_operations.duration_seconds IS 'Operation duration in seconds';
COMMENT ON COLUMN batch_operations.result_message IS 'Operation result message';
COMMENT ON COLUMN batch_operations.result_details IS 'Detailed operation result (JSONB)';
COMMENT ON COLUMN batch_operations.created_at IS 'Batch operation creation timestamp';
COMMENT ON COLUMN batch_operations.updated_at IS 'Last update timestamp';

-- Indexes for sync_batches
CREATE INDEX IF NOT EXISTS idx_sync_batches_orchestrator_agent_id ON sync_batches(orchestrator_agent_id);
CREATE INDEX IF NOT EXISTS idx_sync_batches_status ON sync_batches(status);
CREATE INDEX IF NOT EXISTS idx_sync_batches_batch_type ON sync_batches(batch_type);
CREATE INDEX IF NOT EXISTS idx_sync_batches_next_run ON sync_batches(next_run) WHERE next_run IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sync_batches_created_at ON sync_batches(created_at);
CREATE INDEX IF NOT EXISTS idx_sync_batches_started_at ON sync_batches(started_at) WHERE started_at IS NOT NULL;

-- Indexes for batch_operations
CREATE INDEX IF NOT EXISTS idx_batch_operations_batch_id ON batch_operations(batch_id);
CREATE INDEX IF NOT EXISTS idx_batch_operations_sync_operation_id ON batch_operations(sync_operation_id);
CREATE INDEX IF NOT EXISTS idx_batch_operations_execution_status ON batch_operations(execution_status);
CREATE INDEX IF NOT EXISTS idx_batch_operations_execution_order ON batch_operations(execution_order);