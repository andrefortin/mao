#!/usr/bin/env python3
"""
Configuration Models for Environment Synchronization

Pydantic models for type-safe environment configuration management,
server definitions, and sync operations validation.
"""

import uuid
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, EmailStr
from pathlib import Path

# Import for partial updates
from pydantic import create_model


class ServerStatus(str, Enum):
    """Server operational status"""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class SyncStatus(str, Enum):
    """Synchronization operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ConfigType(str, Enum):
    """Configuration file types"""
    ENV = "env"
    YAML = "yaml"
    JSON = "json"
    TOML = "toml"
    INI = "ini"
    DOCKER_COMPOSE = "docker_compose"
    DOCKERFILE = "dockerfile"


class EncryptionMethod(str, Enum):
    """Encryption methods for sensitive data"""
    AES256_GCM = "aes256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"


class AuthMethod(BaseModel):
    """Authentication method for server connections"""
    type: Literal["ssh_key", "password", "certificate", "aws_instance_profile"]
    username: Optional[str] = None
    password: Optional[str] = None  # Should be encrypted
    private_key_path: Optional[str] = None
    private_key_data: Optional[str] = None  # Should be encrypted
    certificate_path: Optional[str] = None
    certificate_data: Optional[str] = None  # Should be encrypted
    passphrase: Optional[str] = None  # Should be encrypted
    aws_region: Optional[str] = None
    aws_profile: Optional[str] = None


class ServerEnvironment(BaseModel):
    """Server environment configuration"""
    name: str = Field(..., description="Environment name (e.g., 'production', 'staging')")
    description: Optional[str] = Field(None, description="Environment description")
    tags: List[str] = Field(default_factory=list, description="Environment tags")
    variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")


class ServerDefinition(BaseModel):
    """Complete server definition for environment synchronization"""
    id: Optional[uuid.UUID] = Field(None, description="Server UUID")
    name: str = Field(..., min_length=1, max_length=255, description="Server name")
    hostname: str = Field(..., description="Server hostname or IP address")
    port: int = Field(22, ge=1, le=65535, description="SSH port")
    description: Optional[str] = Field(None, description="Server description")

    # Server categorization
    environment: ServerEnvironment = Field(..., description="Server environment")
    server_type: Literal["web", "api", "database", "cache", "queue", "worker", "load_balancer"] = Field(
        ..., description="Server type"
    )

    # Connection details
    auth_method: AuthMethod = Field(..., description="Authentication method")
    connection_timeout: int = Field(30, ge=5, le=300, description="Connection timeout in seconds")

    # Configuration paths
    config_paths: List[str] = Field(default_factory=list, description="Configuration file paths")
    backup_path: Optional[str] = Field(None, description="Backup directory path")

    # Server capabilities
    supported_config_types: List[ConfigType] = Field(
        default_factory=lambda: [ConfigType.ENV, ConfigType.YAML, ConfigType.JSON],
        description="Supported configuration types"
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Server tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Status and timestamps
    status: ServerStatus = Field(ServerStatus.OFFLINE, description="Server status")
    last_sync: Optional[datetime] = Field(None, description="Last successful sync")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    @validator('hostname')
    def validate_hostname(cls, v):
        """Validate hostname format"""
        import re
        # Basic IP or hostname validation
        pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$|^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if not re.match(pattern, v):
            raise ValueError('Invalid hostname or IP address format')
        return v

    @validator('config_paths')
    def validate_config_paths(cls, v):
        """Validate configuration file paths"""
        if not v:
            raise ValueError('At least one config path is required')

        # Ensure paths are absolute
        for path in v:
            if not path.startswith('/'):
                raise ValueError(f'Config path must be absolute: {path}')
        return v


# Create PartialServerDefinition for updates
def create_partial_server_model():
    """Create a partial server definition model for updates"""
    fields = {}
    for field_name, field_info in ServerDefinition.__annotations__.items():
        if field_name not in ['id', 'created_at', 'updated_at']:
            fields[field_name] = (Optional[field_info], None)
    return create_model('PartialServerDefinition', **fields)

PartialServerDefinition = create_partial_server_model()


class ConfigFile(BaseModel):
    """Configuration file definition"""
    path: str = Field(..., description="Absolute file path on server")
    type: ConfigType = Field(..., description="Configuration file type")
    description: Optional[str] = Field(None, description="File description")
    required: bool = Field(True, description="Whether file is required")
    backup_before_sync: bool = Field(True, description="Create backup before sync")
    validation_commands: List[str] = Field(default_factory=list, description="Validation commands")
    post_sync_commands: List[str] = Field(default_factory=list, description="Post-sync commands")

    @validator('path')
    def validate_path(cls, v):
        """Validate file path"""
        if not v.startswith('/'):
            raise ValueError('File path must be absolute')
        return v


class SyncOperation(BaseModel):
    """Synchronization operation definition"""
    id: Optional[uuid.UUID] = Field(None, description="Operation UUID")
    server_id: uuid.UUID = Field(..., description="Target server UUID")
    operation_type: Literal["full_sync", "incremental_sync", "validate", "rollback"] = Field(
        ..., description="Operation type"
    )

    # Files to sync
    config_files: List[ConfigFile] = Field(..., description="Configuration files to sync")
    source_data: Dict[str, str] = Field(..., description="Source configuration data by path")

    # Operation options
    dry_run: bool = Field(False, description="Perform dry run without making changes")
    force_overwrite: bool = Field(False, description="Force overwrite existing files")
    create_backups: bool = Field(True, description="Create backups before sync")
    validate_after_sync: bool = Field(True, description="Validate configuration after sync")

    # Status tracking
    status: SyncStatus = Field(SyncStatus.PENDING, description="Operation status")
    started_at: Optional[datetime] = Field(None, description="Operation start time")
    completed_at: Optional[datetime] = Field(None, description="Operation completion time")

    # Results
    results: Dict[str, Any] = Field(default_factory=dict, description="Operation results")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")

    # Metadata
    initiated_by: str = Field(..., description="Who initiated the operation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SyncBatch(BaseModel):
    """Batch synchronization operation for multiple servers"""
    id: Optional[uuid.UUID] = Field(None, description="Batch UUID")
    name: str = Field(..., description="Batch operation name")
    description: Optional[str] = Field(None, description="Batch description")

    # Server selection
    server_ids: List[uuid.UUID] = Field(..., description="Target server IDs")
    environment_filter: Optional[str] = Field(None, description="Filter by environment")
    server_type_filter: Optional[str] = Field(None, description="Filter by server type")
    tag_filter: Optional[List[str]] = Field(None, description="Filter by tags")

    # Configuration data
    config_files: List[ConfigFile] = Field(..., description="Configuration files to sync")
    source_data: Dict[str, str] = Field(..., description="Source configuration data")

    # Batch options
    parallel_execution: bool = Field(True, description="Execute operations in parallel")
    max_parallel_servers: int = Field(5, ge=1, le=20, description="Max parallel operations")
    continue_on_error: bool = Field(False, description="Continue on individual server errors")

    # Individual operations
    operations: List[SyncOperation] = Field(default_factory=list, description="Individual sync operations")

    # Status tracking
    status: SyncStatus = Field(SyncStatus.PENDING, description="Batch status")
    started_at: Optional[datetime] = Field(None, description="Batch start time")
    completed_at: Optional[datetime] = Field(None, description="Batch completion time")

    # Results summary
    total_operations: int = Field(0, description="Total operations in batch")
    successful_operations: int = Field(0, description="Successful operations")
    failed_operations: int = Field(0, description="Failed operations")
    results_summary: Dict[str, Any] = Field(default_factory=dict, description="Batch results summary")

    # Metadata
    initiated_by: str = Field(..., description="Who initiated the batch")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ValidationRule(BaseModel):
    """Configuration validation rule"""
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    config_type: ConfigType = Field(..., description="Applicable configuration type")

    # Rule definition
    rule_type: Literal["syntax", "semantic", "security", "custom"] = Field(..., description="Rule type")
    validation_command: Optional[str] = Field(None, description="Command to run for validation")
    validation_script: Optional[str] = Field(None, description="Script content for validation")
    regex_pattern: Optional[str] = Field(None, description="Regex pattern for validation")

    # Rule parameters
    severity: Literal["error", "warning", "info"] = Field("error", description="Rule severity")
    required: bool = Field(True, description="Whether rule is required")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Rule tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ConfigTemplate(BaseModel):
    """Configuration file template"""
    id: Optional[uuid.UUID] = Field(None, description="Template UUID")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")

    # Template definition
    config_type: ConfigType = Field(..., description="Configuration type")
    template_content: str = Field(..., description="Template content")
    variable_schema: Dict[str, Any] = Field(default_factory=dict, description="Variable schema")

    # Template usage
    target_paths: List[str] = Field(default_factory=list, description="Typical target paths")
    applicable_server_types: List[str] = Field(default_factory=list, description="Applicable server types")
    validation_rules: List[ValidationRule] = Field(default_factory=list, description="Validation rules")

    # Metadata
    version: str = Field("1.0.0", description="Template version")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class ServerGroup(BaseModel):
    """Server group for batch operations"""
    id: Optional[uuid.UUID] = Field(None, description="Group UUID")
    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")

    # Group definition
    server_ids: List[uuid.UUID] = Field(default_factory=list, description="Server IDs in group")
    dynamic_filters: Dict[str, Any] = Field(default_factory=dict, description="Dynamic filters for server selection")

    # Group properties
    auto_refresh: bool = Field(False, description="Auto-refresh group membership")
    refresh_interval: int = Field(3600, ge=60, description="Refresh interval in seconds")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Group tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class EnvironmentSyncConfig(BaseModel):
    """Complete environment synchronization configuration"""
    id: Optional[uuid.UUID] = Field(None, description="Configuration UUID")
    name: str = Field(..., description="Configuration name")
    description: Optional[str] = Field(None, description="Configuration description")

    # Global settings
    default_timeout: int = Field(30, ge=5, le=300, description="Default operation timeout")
    default_parallel_limit: int = Field(5, ge=1, le=20, description="Default parallel operations limit")
    default_backup_path: str = Field("/var/backups/env_sync", description="Default backup path")

    # Security settings
    encryption_method: EncryptionMethod = Field(EncryptionMethod.AES256_GCM, description="Default encryption method")
    require_approval_for_production: bool = Field(True, description="Require approval for production changes")
    audit_log_retention_days: int = Field(90, ge=7, description="Audit log retention period")

    # Validation settings
    enforce_validation: bool = Field(True, description="Enforce configuration validation")
    fail_on_validation_error: bool = Field(True, description="Fail operations on validation errors")

    # Notification settings
    notify_on_success: bool = Field(True, description="Send notifications on successful sync")
    notify_on_failure: bool = Field(True, description="Send notifications on sync failure")
    notification_channels: List[str] = Field(default_factory=list, description="Notification channels")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


# Request/Response Models for API Endpoints

class CreateServerRequest(BaseModel):
    """Request model for creating a server"""
    server: ServerDefinition


class UpdateServerRequest(BaseModel):
    """Request model for updating a server"""
    server: PartialServerDefinition


class SyncOperationRequest(BaseModel):
    """Request model for sync operations"""
    operation: SyncOperation


class SyncBatchRequest(BaseModel):
    """Request model for batch sync operations"""
    batch: SyncBatch


class ServerListResponse(BaseModel):
    """Response model for server listing"""
    servers: List[ServerDefinition]
    total_count: int
    page: int
    page_size: int


class SyncOperationResponse(BaseModel):
    """Response model for sync operation status"""
    operation: SyncOperation
    server: Optional[ServerDefinition] = None


class SyncBatchResponse(BaseModel):
    """Response model for batch sync status"""
    batch: SyncBatch
    operations: List[SyncOperationResponse]


class ValidationResponse(BaseModel):
    """Response model for configuration validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


