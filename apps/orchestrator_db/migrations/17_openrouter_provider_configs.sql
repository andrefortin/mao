-- ============================================================================
-- OPENROUTER PROVIDER CONFIGURATION TABLES
-- ============================================================================
-- OpenRouter provider configuration and model management tables
--
-- Dependencies: None
-- Note: Stores OpenRouter API configuration and available model information

-- ============================================================================
-- LLM Provider Configurations Table
-- ============================================================================
-- General LLM provider configurations (OpenRouter and other providers)

CREATE TABLE IF NOT EXISTS llm_provider_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    orchestrator_agent_id UUID NOT NULL REFERENCES orchestrator_agents(id) ON DELETE CASCADE,

    -- Provider identification
    provider_name TEXT NOT NULL,
    provider_type TEXT NOT NULL CHECK (provider_type IN ('openrouter', 'anthropic', 'openai', 'google', 'custom')),
    display_name TEXT NOT NULL,

    -- API configuration
    api_base_url TEXT NOT NULL,
    api_version TEXT,
    api_key_encrypted TEXT, -- Encrypted API key
    api_key_header TEXT DEFAULT 'Authorization',

    -- Authentication details
    auth_type TEXT NOT NULL CHECK (auth_type IN ('bearer_token', 'api_key', 'oauth', 'basic_auth', 'custom')),
    auth_scheme TEXT DEFAULT 'Bearer',

    -- Provider metadata
    provider_description TEXT,
    provider_website TEXT,
    documentation_url TEXT,
    status TEXT CHECK (status IN ('active', 'inactive', 'error', 'maintenance', 'testing')) DEFAULT 'inactive',

    -- Rate limiting
    rate_limit_rpm INTEGER DEFAULT 60, -- Requests per minute
    rate_limit_tpm INTEGER DEFAULT 10000, -- Tokens per minute
    rate_limit_tpd INTEGER DEFAULT 100000, -- Tokens per day
    rate_limit_strategy TEXT CHECK (rate_limit_strategy IN ('sliding_window', 'fixed_window', 'token_bucket')) DEFAULT 'sliding_window',

    -- Connection settings
    connection_timeout_seconds INTEGER DEFAULT 30,
    read_timeout_seconds INTEGER DEFAULT 60,
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 1,
    backoff_multiplier DECIMAL(3,2) DEFAULT 2.0,

    -- Feature support
    supports_streaming BOOLEAN DEFAULT false,
    supports_function_calling BOOLEAN DEFAULT false,
    supports_vision BOOLEAN DEFAULT false,
    supports_audio BOOLEAN DEFAULT false,
    supports_embeddings BOOLEAN DEFAULT false,
    supports_fine_tuning BOOLEAN DEFAULT false,

    -- Configuration metadata
    default_model_id TEXT,
    preferred_models JSONB DEFAULT '[]'::jsonb,
    excluded_models JSONB DEFAULT '[]'::jsonb,
    custom_headers JSONB DEFAULT '{}'::jsonb,
    default_parameters JSONB DEFAULT '{}'::jsonb,

    -- Usage tracking
    total_requests BIGINT DEFAULT 0,
    total_tokens BIGINT DEFAULT 0,
    total_cost_usd DECIMAL(12,4) DEFAULT 0.0000,
    last_request_at TIMESTAMPTZ,
    last_error_at TIMESTAMPTZ,
    last_error_message TEXT,
    consecutive_errors INTEGER DEFAULT 0,

    -- Health monitoring
    health_check_enabled BOOLEAN DEFAULT true,
    health_check_interval_seconds INTEGER DEFAULT 300,
    last_health_check_at TIMESTAMPTZ,
    health_status TEXT CHECK (health_status IN ('healthy', 'unhealthy', 'unknown', 'disabled')) DEFAULT 'unknown',
    health_check_endpoint TEXT,
    uptime_percentage DECIMAL(5,2) DEFAULT 100.00,

    -- Configuration flags
    is_default_provider BOOLEAN DEFAULT false,
    is_fallback_provider BOOLEAN DEFAULT false,
    priority_rank INTEGER DEFAULT 100, -- Lower number = higher priority

    -- Metadata
    tags JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    archived BOOLEAN DEFAULT false,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_synced_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT unique_provider_per_orchestrator UNIQUE (orchestrator_agent_id, provider_name),
    CONSTRAINT positive_rate_limits CHECK (rate_limit_rpm > 0 AND rate_limit_tpm > 0 AND rate_limit_tpd > 0),
    CONSTRAINT positive_timeouts CHECK (connection_timeout_seconds > 0 AND read_timeout_seconds > 0),
    CONSTRAINT positive_retries CHECK (max_retries >= 0 AND retry_delay_seconds >= 0),
    CONSTRAINT valid_priority_rank CHECK (priority_rank > 0),
    CONSTRAINT valid_uptime CHECK (uptime_percentage >= 0.0 AND uptime_percentage <= 100.0)
);

-- ============================================================================
-- OpenRouter Models Table
-- ============================================================================
-- Specific model information for OpenRouter provider

CREATE TABLE IF NOT EXISTS openrouter_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    llm_provider_config_id UUID NOT NULL REFERENCES llm_provider_configs(id) ON DELETE CASCADE,

    -- Model identification
    model_id TEXT NOT NULL, -- OpenRouter model ID (e.g., "anthropic/claude-3-sonnet")
    model_name TEXT NOT NULL, -- Human-readable name
    provider_name TEXT NOT NULL, -- Original provider (e.g., "Anthropic")
    model_family TEXT, -- Model family (e.g., "claude-3", "gpt-4")

    -- Model specifications
    context_length INTEGER,
    max_output_tokens INTEGER,
    input_token_limit INTEGER,

    -- Architecture and characteristics
    architecture TEXT,
    model_size TEXT CHECK (model_size IN ('tiny', 'small', 'medium', 'large', 'xlarge', 'unknown')),
    parameter_count BIGINT,
    training_data_cutoff DATE,
    is_open_source BOOLEAN DEFAULT false,

    -- Capabilities
    capabilities JSONB DEFAULT '[]'::jsonb, -- Array of capability strings
    supports_streaming BOOLEAN DEFAULT false,
    supports_function_calling BOOLEAN DEFAULT false,
    supports_vision BOOLEAN DEFAULT false,
    supports_audio BOOLEAN DEFAULT false,
    supports_json_mode BOOLEAN DEFAULT false,
    supports_image_generation BOOLEAN DEFAULT false,
    supports_embeddings BOOLEAN DEFAULT false,

    -- Pricing information
    input_cost_per_million DECIMAL(10,6) DEFAULT 0.000000,
    output_cost_per_million DECIMAL(10,6) DEFAULT 0.000000,
    cache_read_cost_per_million DECIMAL(10,6),
    cache_write_cost_per_million DECIMAL(10,6),
    pricing_currency TEXT DEFAULT 'USD',

    -- Categorization
    category TEXT,
    subcategory TEXT,
    tags JSONB DEFAULT '[]'::jsonb,

    -- Performance characteristics
    benchmark_scores JSONB DEFAULT '{}'::jsonb, -- Various benchmark scores
    latency_ms_average DECIMAL(8,2),
    throughput_tokens_per_second DECIMAL(8,2),

    -- Usage statistics
    total_requests BIGINT DEFAULT 0,
    total_input_tokens BIGINT DEFAULT 0,
    total_output_tokens BIGINT DEFAULT 0,
    total_cost_usd DECIMAL(12,4) DEFAULT 0.0000,
    average_request_duration_ms DECIMAL(10,2),

    -- Availability and status
    is_available BOOLEAN DEFAULT true,
    availability_status TEXT CHECK (availability_status IN ('available', 'unavailable', 'deprecated', 'beta', 'limited')),
    deprecated_at TIMESTAMPTZ,
    sunset_at TIMESTAMPTZ,

    -- Quality metrics
    average_rating DECIMAL(3,2), -- 1.0-5.0 rating
    review_count INTEGER DEFAULT 0,
    quality_score DECIMAL(5,2), -- Internal quality scoring

    -- Regional availability
    available_regions JSONB DEFAULT '[]'::jsonb,
    restricted_regions JSONB DEFAULT '[]'::jsonb,

    -- Special requirements
    requires_special_header BOOLEAN DEFAULT false,
    special_headers JSONB DEFAULT '{}'::jsonb,
    minimum_context_length INTEGER,
    recommended_context_length INTEGER,

    -- Provider metadata
    provider_model_url TEXT,
    documentation_url TEXT,
    model_card_url TEXT,

    -- Configuration metadata
    is_recommended_model BOOLEAN DEFAULT false,
    is_popular_model BOOLEAN DEFAULT false,
    is_new_model BOOLEAN DEFAULT false,
    release_date DATE,
    last_updated_by_provider TIMESTAMPTZ,

    -- Internal metadata
    notes TEXT,
    internal_tags JSONB DEFAULT '[]'::jsonb,
    archived BOOLEAN DEFAULT false,

    -- Timestamps
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    last_pricing_update TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT unique_model_per_provider UNIQUE (llm_provider_config_id, model_id),
    CONSTRAINT positive_costs CHECK (
        input_cost_per_million >= 0 AND
        output_cost_per_million >= 0 AND
        (cache_read_cost_per_million IS NULL OR cache_read_cost_per_million >= 0) AND
        (cache_write_cost_per_million IS NULL OR cache_write_cost_per_million >= 0)
    ),
    CONSTRAINT positive_tokens CHECK (
        total_input_tokens >= 0 AND
        total_output_tokens >= 0 AND
        total_requests >= 0
    ),
    CONSTRAINT valid_rating CHECK (average_rating IS NULL OR (average_rating >= 1.0 AND average_rating <= 5.0)),
    CONSTRAINT valid_quality_score CHECK (quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 100.0)),
    CONSTRAINT positive_performance CHECK (
        latency_ms_average IS NULL OR latency_ms_average >= 0,
        throughput_tokens_per_second IS NULL OR throughput_tokens_per_second >= 0
    ),
    CONSTRAINT valid_dates CHECK (
        deprecated_at IS NULL OR deprecated_at >= discovered_at,
        sunset_at IS NULL OR sunset_at >= deprecated_at
    )
);

-- ============================================================================
-- Table and Column Comments
-- ============================================================================

-- llm_provider_configs table comments
COMMENT ON TABLE llm_provider_configs IS 'Configuration for LLM providers including OpenRouter, Anthropic, OpenAI, etc. (scoped to orchestrator)';
COMMENT ON COLUMN llm_provider_configs.id IS 'Unique provider configuration identifier';
COMMENT ON COLUMN llm_provider_configs.orchestrator_agent_id IS 'Foreign key to orchestrator_agents table (required - configs belong to one orchestrator)';
COMMENT ON COLUMN llm_provider_configs.provider_name IS 'Provider identifier (e.g., "openrouter", "anthropic")';
COMMENT ON COLUMN llm_provider_configs.provider_type IS 'Provider type category';
COMMENT ON COLUMN llm_provider_configs.display_name IS 'Human-readable provider name';
COMMENT ON COLUMN llm_provider_configs.api_base_url IS 'Base URL for provider API';
COMMENT ON COLUMN llm_provider_configs.api_key_encrypted IS 'Encrypted API key for authentication';
COMMENT ON COLUMN llm_provider_configs.auth_type IS 'Authentication method type';
COMMENT ON COLUMN llm_provider_configs.auth_scheme IS 'Authentication scheme (e.g., "Bearer")';
COMMENT ON COLUMN llm_provider_configs.rate_limit_rpm IS 'Rate limit: requests per minute';
COMMENT ON COLUMN llm_provider_configs.rate_limit_tpm IS 'Rate limit: tokens per minute';
COMMENT ON COLUMN llm_provider_configs.rate_limit_tpd IS 'Rate limit: tokens per day';
COMMENT ON COLUMN llm_provider_configs.supports_streaming IS 'Provider supports response streaming';
COMMENT ON COLUMN llm_provider_configs.supports_function_calling IS 'Provider supports function/tool calling';
COMMENT ON COLUMN llm_provider_configs.default_model_id IS 'Default model to use for this provider';
COMMENT ON COLUMN llm_provider_configs.total_requests IS 'Total number of API requests made';
COMMENT ON COLUMN llm_provider_configs.total_tokens IS 'Total tokens processed';
COMMENT ON COLUMN llm_provider_configs.total_cost_usd IS 'Total cost in USD';
COMMENT ON COLUMN llm_provider_configs.health_status IS 'Current health check status';
COMMENT ON COLUMN llm_provider_configs.is_default_provider IS 'Whether this is the default provider';
COMMENT ON COLUMN llm_provider_configs.is_fallback_provider IS 'Whether this provider is used as fallback';
COMMENT ON COLUMN llm_provider_configs.priority_rank IS 'Priority ranking (lower = higher priority)';
COMMENT ON COLUMN llm_provider_configs.tags IS 'Provider tags for categorization';
COMMENT ON COLUMN llm_provider_configs.metadata IS 'Additional provider configuration (JSONB)';
COMMENT ON COLUMN llm_provider_configs.archived IS 'Soft delete flag';

-- openrouter_models table comments
COMMENT ON TABLE openrouter_models IS 'OpenRouter model specifications and pricing information (linked to provider config)';
COMMENT ON COLUMN openrouter_models.id IS 'Unique model record identifier';
COMMENT ON COLUMN openrouter_models.llm_provider_config_id IS 'Foreign key to llm_provider_configs table';
COMMENT ON COLUMN openrouter_models.model_id IS 'OpenRouter model identifier (e.g., "anthropic/claude-3-sonnet")';
COMMENT ON COLUMN openrouter_models.model_name IS 'Human-readable model name';
COMMENT ON COLUMN openrouter_models.provider_name IS 'Original model provider (e.g., "Anthropic")';
COMMENT ON COLUMN openrouter_models.model_family IS 'Model family grouping';
COMMENT ON COLUMN openrouter_models.context_length IS 'Maximum context window size';
COMMENT ON COLUMN openrouter_models.max_output_tokens IS 'Maximum tokens in model response';
COMMENT ON COLUMN openrouter_models.architecture IS 'Model architecture type';
COMMENT ON COLUMN openrouter_models.model_size IS 'Model size category';
COMMENT ON COLUMN openrouter_models.parameter_count IS 'Number of model parameters';
COMMENT ON COLUMN openrouter_models.capabilities IS 'Array of model capabilities';
COMMENT ON COLUMN openrouter_models.input_cost_per_million IS 'Cost per million input tokens';
COMMENT ON COLUMN openrouter_models.output_cost_per_million IS 'Cost per million output tokens';
COMMENT ON COLUMN openrouter_models.category IS 'Model category (e.g., "chat", "code", "embedding")';
COMMENT ON COLUMN openrouter_models.tags IS 'Model tags for filtering';
COMMENT ON COLUMN openrouter_models.total_requests IS 'Total requests using this model';
COMMENT ON COLUMN openrouter_models.total_input_tokens IS 'Cumulative input tokens consumed';
COMMENT ON COLUMN openrouter_models.total_output_tokens IS 'Cumulative output tokens generated';
COMMENT ON COLUMN openrouter_models.is_available IS 'Whether model is currently available';
COMMENT ON COLUMN openrouter_models.average_rating IS 'Average user rating (1-5)';
COMMENT ON COLUMN openrouter_models.available_regions IS 'Regions where model is available';
COMMENT ON COLUMN openrouter_models.is_recommended_model IS 'Provider recommends this model';
COMMENT ON COLUMN openrouter_models.is_popular_model IS 'Model is popular among users';
COMMENT ON COLUMN openrouter_models.notes IS 'Internal notes about the model';
COMMENT ON COLUMN openrouter_models.archived IS 'Soft delete flag';

-- ============================================================================
-- Indexes for Performance Optimization
-- ============================================================================

-- llm_provider_configs indexes
CREATE INDEX IF NOT EXISTS idx_llm_provider_configs_orchestrator_id ON llm_provider_configs(orchestrator_agent_id);
CREATE INDEX IF NOT EXISTS idx_llm_provider_configs_provider_name ON llm_provider_configs(provider_name);
CREATE INDEX IF NOT EXISTS idx_llm_provider_configs_provider_type ON llm_provider_configs(provider_type);
CREATE INDEX IF NOT EXISTS idx_llm_provider_configs_status ON llm_provider_configs(status);
CREATE INDEX IF NOT EXISTS idx_llm_provider_configs_is_default ON llm_provider_configs(is_default_provider);
CREATE INDEX IF NOT EXISTS idx_llm_provider_configs_priority_rank ON llm_provider_configs(priority_rank);
CREATE INDEX IF NOT EXISTS idx_llm_provider_configs_health_status ON llm_provider_configs(health_status);
CREATE INDEX IF NOT EXISTS idx_llm_provider_configs_archived ON llm_provider_configs(archived);
CREATE INDEX IF NOT EXISTS idx_llm_provider_configs_created_at ON llm_provider_configs(created_at);

-- openrouter_models indexes
CREATE INDEX IF NOT EXISTS idx_openrouter_models_provider_config_id ON openrouter_models(llm_provider_config_id);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_model_id ON openrouter_models(model_id);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_provider_name ON openrouter_models(provider_name);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_model_family ON openrouter_models(model_family);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_category ON openrouter_models(category);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_is_available ON openrouter_models(is_available);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_is_recommended ON openrouter_models(is_recommended_model);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_is_popular ON openrouter_models(is_popular_model);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_context_length ON openrouter_models(context_length);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_input_cost ON openrouter_models(input_cost_per_million);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_output_cost ON openrouter_models(output_cost_per_million);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_archived ON openrouter_models(archived);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_created_at ON openrouter_models(created_at);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_last_used_at ON openrouter_models(last_used_at);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_openrouter_models_provider_available ON openrouter_models(llm_provider_config_id, is_available);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_family_cost ON openrouter_models(model_family, input_cost_per_million);
CREATE INDEX IF NOT EXISTS idx_openrouter_models_category_available ON openrouter_models(category, is_available);

-- ============================================================================
-- Default OpenRouter Provider Configuration (if desired)
-- ============================================================================

-- Note: This INSERT is commented out by default. Uncomment and modify as needed.
-- INSERT INTO llm_provider_configs (
--     orchestrator_agent_id,
--     provider_name,
--     provider_type,
--     display_name,
--     api_base_url,
--     auth_type,
--     auth_scheme,
--     supports_streaming,
--     supports_function_calling,
--     supports_vision,
--     is_default_provider,
--     rate_limit_rpm,
--     rate_limit_tpm,
--     metadata
-- ) SELECT
--     id,
--     'openrouter',
--     'openrouter',
--     'OpenRouter',
--     'https://openrouter.ai/api/v1',
--     'bearer_token',
--     'Bearer',
--     true,
--     true,
--     true,
--     false,
--     60,
--     10000,
--     '{"website": "https://openrouter.ai", "documentation": "https://openrouter.ai/docs"}'::jsonb
-- FROM orchestrator_agents
-- WHERE archived = false
-- LIMIT 1;