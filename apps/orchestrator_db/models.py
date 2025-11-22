"""
Pydantic Database Models for Multi-Agent Orchestration

These models map directly to the PostgreSQL tables defined in schema_orchestrator.sql.
They provide:
- Automatic UUID handling (converts asyncpg UUID objects to Python UUID)
- Type safety and validation
- Automatic JSON serialization/deserialization
- Field validation and defaults

Usage:
    from models import Agent, OrchestratorAgent, Prompt, AgentLog, SystemLog

    # Automatically handles UUID conversion from database
    agent = Agent(**row_dict)
    print(agent.id)  # Works with both UUID objects and strings
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, Literal, Union
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════
# ORCHESTRATOR_AGENT MODEL
# ═══════════════════════════════════════════════════════════


class OrchestratorAgent(BaseModel):
    """
    Singleton orchestrator agent that manages other agents.

    Maps to: orchestrator_agents table
    """
    id: UUID
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None
    status: Optional[Literal['idle', 'executing', 'waiting', 'blocked', 'complete']] = None
    working_dir: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost: float = 0.0
    archived: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('total_cost', mode='before')
    @classmethod
    def convert_decimal(cls, v):
        """Convert Decimal to float"""
        if isinstance(v, Decimal):
            return float(v)
        return v

    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        """Parse JSON string metadata to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════
# AGENT MODEL
# ═══════════════════════════════════════════════════════════


class Agent(BaseModel):
    """
    Agent registry and configuration for managed agents.

    Maps to: agents table
    """
    id: UUID
    orchestrator_agent_id: UUID
    name: str
    model: str
    system_prompt: Optional[str] = None
    working_dir: Optional[str] = None
    git_worktree: Optional[str] = None
    status: Optional[Literal['idle', 'executing', 'waiting', 'blocked', 'complete']] = None
    session_id: Optional[str] = None
    adw_id: Optional[str] = None
    adw_step: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost: float = 0.0
    archived: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'orchestrator_agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('total_cost', mode='before')
    @classmethod
    def convert_decimal(cls, v):
        """Convert Decimal to float"""
        if isinstance(v, Decimal):
            return float(v)
        return v

    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        """Parse JSON string metadata to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════
# PROMPT MODEL
# ═══════════════════════════════════════════════════════════


class Prompt(BaseModel):
    """
    Prompts sent to agents from engineers or orchestrator.

    Maps to: prompts table
    """
    id: UUID
    agent_id: Optional[UUID] = None
    task_slug: Optional[str] = None
    author: Literal['engineer', 'orchestrator_agent']
    prompt_text: str
    summary: Optional[str] = None
    timestamp: datetime
    session_id: Optional[str] = None

    @field_validator('id', 'agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════
# AGENT_LOG MODEL
# ═══════════════════════════════════════════════════════════


class AgentLog(BaseModel):
    """
    Unified event log for hooks and agent responses during task execution.

    Maps to: agent_logs table
    """
    id: UUID
    agent_id: UUID
    session_id: Optional[str] = None
    task_slug: Optional[str] = None
    adw_id: Optional[str] = None
    adw_step: Optional[str] = None
    entry_index: Optional[int] = None
    event_category: Literal['hook', 'response']
    event_type: str
    content: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    timestamp: datetime

    @field_validator('id', 'agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('payload', mode='before')
    @classmethod
    def parse_payload(cls, v):
        """Parse JSON string payload to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════
# SYSTEM_LOG MODEL
# ═══════════════════════════════════════════════════════════


class SystemLog(BaseModel):
    """
    Application-level system logs (global application events only).

    For agent-related logs, use agent_logs table instead.

    Maps to: system_logs table
    """
    id: UUID
    file_path: Optional[str] = None
    adw_id: Optional[str] = None
    adw_step: Optional[str] = None
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR']
    message: str
    summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        """Parse JSON string metadata to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════
# ORCHESTRATOR_CHAT MODEL
# ═══════════════════════════════════════════════════════════


class OrchestratorChat(BaseModel):
    """
    Append-only conversation log capturing 3-way communication: user ↔ orchestrator ↔ agents.

    Maps to: orchestrator_chat table
    """
    id: UUID
    created_at: datetime
    updated_at: datetime
    orchestrator_agent_id: UUID
    sender_type: Literal['user', 'orchestrator', 'agent']
    receiver_type: Literal['user', 'orchestrator', 'agent']
    message: str
    summary: Optional[str] = None
    agent_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('id', 'orchestrator_agent_id', 'agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        """Parse JSON string metadata to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════
# ENVIRONMENT SYNCHRONIZATION MODELS
# ═══════════════════════════════════════════════════════════


class Server(BaseModel):
    """
    Server definitions and configurations for environment synchronization.

    Maps to: servers table
    """
    id: UUID
    orchestrator_agent_id: UUID
    name: str
    hostname: str
    ip_address: str
    port: int = 22
    connection_type: Literal['ssh', 'sftp', 'ftp', 'sftp_with_key', 'sftp_with_password']
    username: str
    password: Optional[str] = None
    private_key_path: Optional[str] = None
    private_key_passphrase: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    environment_type: Literal['development', 'staging', 'production', 'testing', 'local']
    status: Literal['active', 'inactive', 'maintenance', 'error'] = 'inactive'
    health_check_url: Optional[str] = None
    health_check_interval: int = 300
    last_health_check: Optional[datetime] = None
    health_status: Literal['healthy', 'unhealthy', 'unknown'] = 'unknown'
    connection_timeout: int = 30
    max_parallel_operations: int = 5
    backup_enabled: bool = True
    backup_retention_days: int = 30
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'orchestrator_agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        """Parse JSON string metadata to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class SyncOperation(BaseModel):
    """
    Individual sync operation tracking.

    Maps to: sync_operations table
    """
    id: UUID
    server_id: UUID
    operation_name: str
    sync_type: Literal['full_sync', 'incremental_sync', 'file_sync', 'env_sync', 'config_sync', 'backup_sync']
    source_path: Optional[str] = None
    destination_path: Optional[str] = None
    operation_direction: Literal['upload', 'download', 'bidirectional']
    status: Literal['pending', 'in_progress', 'completed', 'failed', 'cancelled', 'paused'] = 'pending'
    priority: int = 5
    schedule_expression: Optional[str] = None
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_files_transferred: int = 0
    total_bytes_transferred: int = 0
    sync_options: Dict[str, Any] = Field(default_factory=lambda: {
        "preserve_permissions": True,
        "preserve_timestamps": True,
        "follow_symlinks": False,
        "compression": True,
        "encryption": False,
        "exclude_patterns": [],
        "include_patterns": [],
        "checksum_verification": True,
        "max_file_size": None,
        "max_file_age": None,
        "dry_run": False
    })
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    progress_percentage: float = 0.00
    estimated_completion: Optional[datetime] = None
    auto_retry_enabled: bool = True
    max_retry_attempts: int = 3
    retry_count: int = 0
    retry_delay_seconds: int = 300
    notification_enabled: bool = True
    notification_emails: list[str] = Field(default_factory=list)
    notification_webhooks: list[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    @field_validator('id', 'server_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('sync_options', 'error_details', 'metadata', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Parse JSON string fields to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class SyncBatch(BaseModel):
    """
    Batch operation management for grouping and scheduling multiple sync operations.

    Maps to: sync_batches table
    """
    id: UUID
    orchestrator_agent_id: UUID
    batch_name: str
    description: Optional[str] = None
    batch_type: Literal['manual', 'scheduled', 'triggered', 'emergency']
    status: Literal['pending', 'in_progress', 'completed', 'failed', 'cancelled', 'paused'] = 'pending'
    execution_order: Optional[Literal['sequential', 'parallel', 'priority_based']] = None
    max_parallel_operations: int = 3
    continue_on_failure: bool = False
    stop_on_first_failure: bool = False
    schedule_expression: Optional[str] = None
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_operations: int = 0
    completed_operations: int = 0
    failed_operations: int = 0
    total_duration_seconds: int = 0
    average_duration_seconds: float = 0.00
    batch_options: Dict[str, Any] = Field(default_factory=lambda: {
        "rollback_on_failure": False,
        "create_backup_before_batch": True,
        "send_summary_report": True,
        "timeout_minutes": 60,
        "retry_failed_operations": True,
        "max_batch_retries": 1
    })
    error_summary: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    progress_percentage: float = 0.00
    estimated_completion: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'orchestrator_agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('batch_options', 'error_details', 'metadata', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Parse JSON string fields to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class ServerEnvironment(BaseModel):
    """
    Environment variable storage for servers.

    Maps to: server_environments table
    """
    id: UUID
    server_id: UUID
    variable_name: str
    variable_value: str
    environment_type: Literal['default', 'development', 'staging', 'production', 'testing', 'custom'] = 'default'
    is_encrypted: bool = False
    is_sensitive: bool = False
    description: Optional[str] = None
    variable_type: Literal['string', 'number', 'boolean', 'json', 'url', 'email', 'path', 'port'] = 'string'
    is_required: bool = False
    default_value: Optional[str] = None
    validation_pattern: Optional[str] = None
    source: Literal['manual', 'imported', 'synced', 'generated', 'discovered'] = 'manual'
    last_synced_at: Optional[datetime] = None
    sync_status: Literal['synced', 'pending_sync', 'sync_failed', 'local_only'] = 'synced'
    checksum: Optional[str] = None
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'server_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        """Parse JSON string metadata to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class ConfigFile(BaseModel):
    """
    Configuration file management.

    Maps to: config_files table
    """
    id: UUID
    server_id: UUID
    file_path: str
    file_name: str
    file_extension: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_hash: Optional[str] = None
    file_content: Optional[str] = None
    file_content_type: Literal['text', 'binary', 'json', 'yaml', 'xml', 'ini', 'env'] = 'text'
    encoding: str = 'utf-8'
    mime_type: Optional[str] = None
    config_type: Literal['application', 'database', 'web_server', 'security', 'logging', 'environment', 'deployment', 'custom'] = 'custom'
    backup_enabled: bool = True
    backup_retention_count: int = 10
    version_control_enabled: bool = False
    sync_enabled: bool = True
    sync_direction: Literal['upload', 'download', 'bidirectional'] = 'bidirectional'
    validation_enabled: bool = True
    validation_schema: Optional[Dict[str, Any]] = None
    encryption_enabled: bool = False
    compression_enabled: bool = False
    is_template: bool = False
    template_variables: list = Field(default_factory=list)
    auto_reload_services: list[str] = Field(default_factory=list)
    file_permissions: Optional[str] = None
    file_owner: Optional[str] = None
    last_modified_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    sync_status: Literal['synced', 'pending_sync', 'sync_failed', 'local_only', 'remote_only', 'conflict'] = 'synced'
    sync_error_message: Optional[str] = None
    sync_error_details: Optional[Dict[str, Any]] = None
    checksum: Optional[str] = None
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'server_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('validation_schema', 'sync_error_details', 'metadata', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Parse JSON string fields to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class SyncOperationLog(BaseModel):
    """
    Detailed operation logging for sync activities.

    Maps to: sync_operation_logs table
    """
    id: UUID
    sync_operation_id: Optional[UUID] = None
    server_id: Optional[UUID] = None
    batch_operation_id: Optional[UUID] = None
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    log_category: Literal['connection', 'authentication', 'file_transfer', 'validation', 'backup', 'cleanup', 'system', 'performance', 'security']
    log_type: str
    message: str
    message_details: Dict[str, Any] = Field(default_factory=dict)
    source_component: Optional[str] = None
    source_function: Optional[str] = None
    file_path: Optional[str] = None
    operation_step: Optional[str] = None
    step_status: Optional[Literal['started', 'in_progress', 'completed', 'failed', 'skipped']] = None
    execution_time_ms: Optional[int] = None
    bytes_transferred: Optional[int] = None
    files_transferred: Optional[int] = None
    transfer_rate_mbps: Optional[float] = None
    error_code: Optional[str] = None
    error_severity: Optional[Literal['low', 'medium', 'high', 'critical']] = None
    stack_trace: Optional[str] = None
    context_data: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    network_info: Dict[str, Any] = Field(default_factory=dict)
    system_info: Dict[str, Any] = Field(default_factory=dict)
    retry_attempt: Optional[int] = None
    retry_reason: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime

    @field_validator('id', 'sync_operation_id', 'server_id', 'batch_operation_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('message_details', 'context_data', 'performance_metrics', 'network_info', 'system_info', 'metadata', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Parse JSON string fields to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class ServerBackup(BaseModel):
    """
    Backup tracking for servers and configurations.

    Maps to: server_backups table
    """
    id: UUID
    server_id: UUID
    sync_operation_id: Optional[UUID] = None
    backup_name: str
    backup_type: Literal['full', 'incremental', 'differential', 'config_only', 'environment_only', 'database', 'custom']
    backup_method: Literal['rsync', 'tar', 'zip', 'snapshot', 'database_dump', 'custom_script', 'cloud_backup']
    status: Literal['pending', 'in_progress', 'completed', 'failed', 'cancelled', 'expired', 'restoring'] = 'pending'
    source_paths: list[str] = Field(default_factory=list)
    destination_path: Optional[str] = None
    backup_format: Literal['tar', 'tar.gz', 'tar.bz2', 'zip', '7z', 'rsync', 'native'] = 'tar.gz'
    compression_enabled: bool = True
    compression_level: int = 6
    encryption_enabled: bool = False
    encryption_algorithm: str = 'aes256'
    checksum_algorithm: str = 'sha256'
    file_count: Optional[int] = None
    total_size_bytes: Optional[int] = None
    compressed_size_bytes: Optional[int] = None
    compression_ratio: Optional[float] = None
    backup_size_limit_gb: Optional[float] = None
    retention_days: int = 30
    retention_policy: Dict[str, Any] = Field(default_factory=lambda: {
        "keep_daily": 7,
        "keep_weekly": 4,
        "keep_monthly": 12,
        "keep_yearly": 5,
        "auto_cleanup": True
    })
    backup_schedule: Optional[str] = None
    last_backup_at: Optional[datetime] = None
    next_backup_at: Optional[datetime] = None
    backup_duration_seconds: Optional[int] = None
    backup_throughput_mbps: Optional[float] = None
    verification_enabled: bool = True
    verification_status: Literal['pending', 'in_progress', 'passed', 'failed', 'skipped'] = 'pending'
    verification_result: Optional[Dict[str, Any]] = None
    auto_restore_enabled: bool = False
    restore_test_enabled: bool = False
    last_restore_test_at: Optional[datetime] = None
    restore_test_result: Optional[Dict[str, Any]] = None
    backup_metadata: Dict[str, Any] = Field(default_factory=dict)
    includes_database: bool = False
    includes_config_files: bool = True
    includes_environment_variables: bool = True
    includes_user_data: bool = False
    exclude_patterns: list[str] = Field(default_factory=list)
    include_patterns: list[str] = Field(default_factory=list)
    backup_tags: list[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3
    notification_enabled: bool = True
    notification_channels: list[str] = Field(default_factory=list)
    storage_location_type: Optional[Literal['local', 'network', 'cloud', 'tape']] = None
    storage_location_path: Optional[str] = None
    cloud_provider: Optional[str] = None
    cloud_bucket: Optional[str] = None
    cloud_region: Optional[str] = None
    access_url: Optional[str] = None
    is_encrypted_at_rest: bool = False
    data_classification: Literal['public', 'internal', 'confidential', 'restricted'] = 'confidential'
    compliance_tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @field_validator('id', 'server_id', 'sync_operation_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if v is None:
            return None
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('retention_policy', 'verification_result', 'restore_test_result', 'backup_metadata', 'error_details', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Parse JSON string fields to dict"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════
# LLM PROVIDER CONFIGURATION MODELS
# ═══════════════════════════════════════════════════════════


class LlmProviderConfig(BaseModel):
    """
    Configuration for LLM providers including OpenRouter, Anthropic, OpenAI, etc.

    Maps to: llm_provider_configs table
    """
    id: UUID
    orchestrator_agent_id: UUID
    provider_name: str
    provider_type: Literal['openrouter', 'anthropic', 'openai', 'google', 'custom']
    display_name: str
    api_base_url: str
    api_version: Optional[str] = None
    api_key_encrypted: Optional[str] = None
    api_key_header: str = 'Authorization'
    auth_type: Literal['bearer_token', 'api_key', 'oauth', 'basic_auth', 'custom']
    auth_scheme: str = 'Bearer'
    provider_description: Optional[str] = None
    provider_website: Optional[str] = None
    documentation_url: Optional[str] = None
    status: Literal['active', 'inactive', 'error', 'maintenance', 'testing'] = 'inactive'
    rate_limit_rpm: int = 60
    rate_limit_tpm: int = 10000
    rate_limit_tpd: int = 100000
    rate_limit_strategy: Literal['sliding_window', 'fixed_window', 'token_bucket'] = 'sliding_window'
    connection_timeout_seconds: int = 30
    read_timeout_seconds: int = 60
    max_retries: int = 3
    retry_delay_seconds: int = 1
    backoff_multiplier: float = 2.0
    supports_streaming: bool = False
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_audio: bool = False
    supports_embeddings: bool = False
    supports_fine_tuning: bool = False
    default_model_id: Optional[str] = None
    preferred_models: list[str] = Field(default_factory=list)
    excluded_models: list[str] = Field(default_factory=list)
    custom_headers: Dict[str, Any] = Field(default_factory=dict)
    default_parameters: Dict[str, Any] = Field(default_factory=dict)
    total_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    last_request_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    consecutive_errors: int = 0
    health_check_enabled: bool = True
    health_check_interval_seconds: int = 300
    last_health_check_at: Optional[datetime] = None
    health_status: Literal['healthy', 'unhealthy', 'unknown', 'disabled'] = 'unknown'
    health_check_endpoint: Optional[str] = None
    uptime_percentage: float = 100.0
    is_default_provider: bool = False
    is_fallback_provider: bool = False
    priority_rank: int = 100
    tags: list[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    archived: bool = False
    created_at: datetime
    updated_at: datetime
    last_synced_at: Optional[datetime] = None

    @field_validator('id', 'orchestrator_agent_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('total_cost_usd', 'backoff_multiplier', 'uptime_percentage', mode='before')
    @classmethod
    def convert_decimal(cls, v):
        """Convert Decimal to float"""
        if isinstance(v, Decimal):
            return float(v)
        return v

    @field_validator('preferred_models', 'excluded_models', 'custom_headers', 'default_parameters', 'tags', 'metadata', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Parse JSON string fields to dict/list"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class OpenRouterModel(BaseModel):
    """
    OpenRouter model specifications and pricing information.

    Maps to: openrouter_models table
    """
    id: UUID
    llm_provider_config_id: UUID
    model_id: str
    model_name: str
    provider_name: str
    model_family: Optional[str] = None
    context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None
    input_token_limit: Optional[int] = None
    architecture: Optional[str] = None
    model_size: Optional[Literal['tiny', 'small', 'medium', 'large', 'xlarge', 'unknown']] = None
    parameter_count: Optional[int] = None
    training_data_cutoff: Optional[datetime] = None
    is_open_source: bool = False
    capabilities: list[str] = Field(default_factory=list)
    supports_streaming: bool = False
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_audio: bool = False
    supports_json_mode: bool = False
    supports_image_generation: bool = False
    supports_embeddings: bool = False
    input_cost_per_million: float = 0.0
    output_cost_per_million: float = 0.0
    cache_read_cost_per_million: Optional[float] = None
    cache_write_cost_per_million: Optional[float] = None
    pricing_currency: str = 'USD'
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    benchmark_scores: Dict[str, Any] = Field(default_factory=dict)
    latency_ms_average: Optional[float] = None
    throughput_tokens_per_second: Optional[float] = None
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    average_request_duration_ms: Optional[float] = None
    is_available: bool = True
    availability_status: Optional[Literal['available', 'unavailable', 'deprecated', 'beta', 'limited']] = None
    deprecated_at: Optional[datetime] = None
    sunset_at: Optional[datetime] = None
    average_rating: Optional[float] = None
    review_count: int = 0
    quality_score: Optional[float] = None
    available_regions: list[str] = Field(default_factory=list)
    restricted_regions: list[str] = Field(default_factory=list)
    requires_special_header: bool = False
    special_headers: Dict[str, Any] = Field(default_factory=dict)
    minimum_context_length: Optional[int] = None
    recommended_context_length: Optional[int] = None
    provider_model_url: Optional[str] = None
    documentation_url: Optional[str] = None
    model_card_url: Optional[str] = None
    is_recommended_model: bool = False
    is_popular_model: bool = False
    is_new_model: bool = False
    release_date: Optional[datetime] = None
    last_updated_by_provider: Optional[datetime] = None
    notes: Optional[str] = None
    internal_tags: list[str] = Field(default_factory=list)
    archived: bool = False
    discovered_at: datetime
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    last_pricing_update: Optional[datetime] = None

    @field_validator('id', 'llm_provider_config_id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        """Convert asyncpg UUID to Python UUID"""
        if isinstance(v, UUID):
            return v
        return UUID(str(v))

    @field_validator('total_cost_usd', 'input_cost_per_million', 'output_cost_per_million', 'cache_read_cost_per_million', 'cache_write_cost_per_million', 'average_rating', 'quality_score', 'latency_ms_average', 'throughput_tokens_per_second', 'average_request_duration_ms', mode='before')
    @classmethod
    def convert_decimal(cls, v):
        """Convert Decimal to float"""
        if isinstance(v, Decimal):
            return float(v)
        return v

    @field_validator('capabilities', 'tags', 'benchmark_scores', 'available_regions', 'restricted_regions', 'special_headers', 'internal_tags', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Parse JSON string fields to dict/list"""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @field_validator('training_data_cutoff', 'deprecated_at', 'sunset_at', 'release_date', 'last_updated_by_provider', 'discovered_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime from string or keep datetime object"""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                return None
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ═══════════════════════════════════════════════════════════
# EXPORT PUBLIC API
# ═══════════════════════════════════════════════════════════

__all__ = [
    "OrchestratorAgent",
    "Agent",
    "Prompt",
    "AgentLog",
    "SystemLog",
    "OrchestratorChat",
    "Server",
    "SyncOperation",
    "SyncBatch",
    "ServerEnvironment",
    "ConfigFile",
    "SyncOperationLog",
    "ServerBackup",
    "LlmProviderConfig",
    "OpenRouterModel",
]
