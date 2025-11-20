"""
Environment Synchronization Database Operations

Database operations for environment synchronization features including
server management, sync operations, batch operations, and configuration.
"""

import asyncpg
import uuid
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from .database import get_connection


# ═══════════════════════════════════════════════════════════
# SERVER MANAGEMENT OPERATIONS
# ═══════════════════════════════════════════════════════════


async def create_server(
    name: str,
    hostname: str,
    port: int,
    environment_name: str,
    server_type: str,
    auth_method: Dict[str, Any],
    config_paths: List[str],
    description: Optional[str] = None,
    backup_path: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> uuid.UUID:
    """
    Create a new server definition.

    Args:
        name: Server name
        hostname: Server hostname or IP address
        port: SSH port
        environment_name: Environment name (production, staging, etc.)
        server_type: Server type (web, api, database, etc.)
        auth_method: Authentication method dictionary (encrypted)
        config_paths: List of configuration file paths
        description: Optional server description
        backup_path: Optional backup directory path
        tags: Optional server tags
        metadata: Additional metadata

    Returns:
        UUID of created server
    """
    server_id = uuid.uuid4()

    async with get_connection() as conn:
        # Insert server environment
        env_id = uuid.uuid4()
        await conn.execute(
            """
            INSERT INTO server_environments (
                id, name, description, tags, variables, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            ON CONFLICT (name) DO UPDATE SET
                updated_at = NOW()
            """,
            env_id,
            environment_name,
            f"Environment for {name}",
            tags or [],
            {}
        )

        # Get environment ID
        env_row = await conn.fetchrow(
            "SELECT id FROM server_environments WHERE name = $1",
            environment_name
        )
        environment_id = env_row["id"]

        # Insert server
        await conn.execute(
            """
            INSERT INTO servers (
                id, name, hostname, port, description, environment_id, server_type,
                auth_method, connection_timeout, config_paths, backup_path,
                status, tags, metadata, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW(), NOW())
            """,
            server_id,
            name,
            hostname,
            port,
            description,
            environment_id,
            server_type,
            json.dumps(auth_method),
            30,  # Default connection timeout
            config_paths,
            backup_path,
            "offline",  # Default status
            tags or [],
            json.dumps(metadata or {})
        )

    return server_id


async def get_server(server_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """
    Get server by ID.

    Args:
        server_id: UUID of the server

    Returns:
        Server dictionary or None if not found
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT s.*, e.name as environment_name, e.description as environment_description
            FROM servers s
            JOIN server_environments e ON s.environment_id = e.id
            WHERE s.id = $1 AND s.archived = false
            """,
            server_id
        )

        if row:
            result = dict(row)
            # Parse JSON fields
            for field in ['auth_method', 'tags', 'metadata']:
                if isinstance(result.get(field), str):
                    result[field] = json.loads(result[field])
            return result

        return None


async def list_servers(
    environment: Optional[str] = None,
    server_type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    List servers with optional filtering.

    Args:
        environment: Filter by environment name
        server_type: Filter by server type
        tags: Filter by tags (must contain all specified tags)
        status: Filter by status
        limit: Maximum number of servers to return
        offset: Number of servers to skip

    Returns:
        List of server dictionaries
    """
    async with get_connection() as conn:
        query = """
            SELECT s.*, e.name as environment_name, e.description as environment_description
            FROM servers s
            JOIN server_environments e ON s.environment_id = e.id
            WHERE s.archived = false
        """
        params = []
        param_count = 0

        # Add filters
        if environment:
            param_count += 1
            query += f" AND e.name = ${param_count}"
            params.append(environment)

        if server_type:
            param_count += 1
            query += f" AND s.server_type = ${param_count}"
            params.append(server_type)

        if status:
            param_count += 1
            query += f" AND s.status = ${param_count}"
            params.append(status)

        if tags:
            for tag in tags:
                param_count += 1
                query += f" AND ${param_count} = ANY(s.tags)"
                params.append(tag)

        # Add ordering and pagination
        query += " ORDER BY s.created_at DESC"
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)

        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)

        rows = await conn.fetch(query, *params)

        results = []
        for row in rows:
            result = dict(row)
            # Parse JSON fields
            for field in ['auth_method', 'tags', 'metadata']:
                if isinstance(result.get(field), str):
                    result[field] = json.loads(result[field])
            results.append(result)

        return results


async def update_server_status(server_id: uuid.UUID, status: str) -> None:
    """
    Update server status.

    Args:
        server_id: UUID of the server
        status: New status (online, offline, maintenance, error)
    """
    async with get_connection() as conn:
        await conn.execute(
            """
            UPDATE servers
            SET status = $1, updated_at = NOW()
            WHERE id = $2
            """,
            status,
            server_id
        )


async def update_server_last_sync(server_id: uuid.UUID) -> None:
    """
    Update server's last sync timestamp.

    Args:
        server_id: UUID of the server
    """
    async with get_connection() as conn:
        await conn.execute(
            """
            UPDATE servers
            SET last_sync = NOW(), updated_at = NOW()
            WHERE id = $1
            """,
            server_id
        )


async def delete_server(server_id: uuid.UUID) -> None:
    """
    Soft delete server (sets archived=true).

    Args:
        server_id: UUID of the server to archive
    """
    async with get_connection() as conn:
        await conn.execute(
            "UPDATE servers SET archived = true, updated_at = NOW() WHERE id = $1",
            server_id
        )


# ═══════════════════════════════════════════════════════════
# SYNC OPERATIONS
# ═══════════════════════════════════════════════════════════


async def create_sync_operation(
    server_id: uuid.UUID,
    operation_type: str,
    config_files: List[Dict[str, Any]],
    source_data: Dict[str, str],
    initiated_by: str,
    dry_run: bool = False,
    force_overwrite: bool = False,
    create_backups: bool = True,
    validate_after_sync: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> uuid.UUID:
    """
    Create a new synchronization operation.

    Args:
        server_id: Target server ID
        operation_type: Type of operation
        config_files: List of configuration file definitions
        source_data: Source configuration data
        initiated_by: Who initiated the operation
        dry_run: Perform dry run without making changes
        force_overwrite: Force overwrite existing files
        create_backups: Create backups before sync
        validate_after_sync: Validate configuration after sync
        metadata: Additional metadata

    Returns:
        UUID of created sync operation
    """
    operation_id = uuid.uuid4()

    async with get_connection() as conn:
        # Insert sync operation
        await conn.execute(
            """
            INSERT INTO sync_operations (
                id, server_id, operation_type, config_files, source_data,
                dry_run, force_overwrite, create_backups, validate_after_sync,
                status, initiated_by, metadata, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())
            """,
            operation_id,
            server_id,
            operation_type,
            json.dumps(config_files),
            json.dumps(source_data),
            dry_run,
            force_overwrite,
            create_backups,
            validate_after_sync,
            "pending",
            initiated_by,
            json.dumps(metadata or {})
        )

    return operation_id


async def get_sync_operation(operation_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """
    Get sync operation by ID.

    Args:
        operation_id: UUID of the operation

    Returns:
        Operation dictionary or None if not found
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT so.*, s.name as server_name, s.hostname as server_hostname
            FROM sync_operations so
            JOIN servers s ON so.server_id = s.id
            WHERE so.id = $1
            """,
            operation_id
        )

        if row:
            result = dict(row)
            # Parse JSON fields
            for field in ['config_files', 'source_data', 'results', 'errors', 'warnings', 'metadata']:
                if isinstance(result.get(field), str):
                    result[field] = json.loads(result[field])
            return result

        return None


async def update_sync_operation_status(
    operation_id: uuid.UUID,
    status: str,
    results: Optional[Dict[str, Any]] = None,
    errors: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None
) -> None:
    """
    Update sync operation status and results.

    Args:
        operation_id: UUID of the operation
        status: New status
        results: Operation results
        errors: Error messages
        warnings: Warning messages
    """
    async with get_connection() as conn:
        await conn.execute(
            """
            UPDATE sync_operations
            SET status = $1,
                results = COALESCE($2::jsonb, results),
                errors = COALESCE($3::jsonb, errors),
                warnings = COALESCE($4::jsonb, warnings),
                updated_at = NOW()
            WHERE id = $5
            """,
            status,
            json.dumps(results or {}),
            json.dumps(errors or []),
            json.dumps(warnings or []),
            operation_id
        )


async def list_sync_operations(
    server_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    initiated_by: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    List sync operations with optional filtering.

    Args:
        server_id: Filter by server ID
        status: Filter by status
        initiated_by: Filter by initiator
        limit: Maximum number of operations to return
        offset: Number of operations to skip

    Returns:
        List of operation dictionaries
    """
    async with get_connection() as conn:
        query = """
            SELECT so.*, s.name as server_name, s.hostname as server_hostname
            FROM sync_operations so
            JOIN servers s ON so.server_id = s.id
            WHERE 1=1
        """
        params = []
        param_count = 0

        # Add filters
        if server_id:
            param_count += 1
            query += f" AND so.server_id = ${param_count}"
            params.append(server_id)

        if status:
            param_count += 1
            query += f" AND so.status = ${param_count}"
            params.append(status)

        if initiated_by:
            param_count += 1
            query += f" AND so.initiated_by = ${param_count}"
            params.append(initiated_by)

        # Add ordering and pagination
        query += " ORDER BY so.created_at DESC"
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)

        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)

        rows = await conn.fetch(query, *params)

        results = []
        for row in rows:
            result = dict(row)
            # Parse JSON fields
            for field in ['config_files', 'source_data', 'results', 'errors', 'warnings', 'metadata']:
                if isinstance(result.get(field), str):
                    result[field] = json.loads(result[field])
            results.append(result)

        return results


# ═══════════════════════════════════════════════════════════
# BATCH SYNC OPERATIONS
# ═══════════════════════════════════════════════════════════


async def create_sync_batch(
    name: str,
    server_ids: List[uuid.UUID],
    config_files: List[Dict[str, Any]],
    source_data: Dict[str, str],
    initiated_by: str,
    parallel_execution: bool = True,
    max_parallel_servers: int = 5,
    continue_on_error: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> uuid.UUID:
    """
    Create a new batch synchronization operation.

    Args:
        name: Batch operation name
        server_ids: List of target server IDs
        config_files: List of configuration file definitions
        source_data: Source configuration data
        initiated_by: Who initiated the batch
        parallel_execution: Execute operations in parallel
        max_parallel_servers: Maximum parallel operations
        continue_on_error: Continue on individual server errors
        metadata: Additional metadata

    Returns:
        UUID of created batch operation
    """
    batch_id = uuid.uuid4()

    async with get_connection() as conn:
        # Insert batch operation
        await conn.execute(
            """
            INSERT INTO sync_batches (
                id, name, server_ids, config_files, source_data,
                parallel_execution, max_parallel_servers, continue_on_error,
                status, initiated_by, metadata, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
            """,
            batch_id,
            name,
            [str(sid) for sid in server_ids],  # Convert UUIDs to strings
            json.dumps(config_files),
            json.dumps(source_data),
            parallel_execution,
            max_parallel_servers,
            continue_on_error,
            "pending",
            initiated_by,
            json.dumps(metadata or {})
        )

    return batch_id


async def get_sync_batch(batch_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """
    Get sync batch by ID.

    Args:
        batch_id: UUID of the batch

    Returns:
        Batch dictionary or None if not found
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM sync_batches WHERE id = $1",
            batch_id
        )

        if row:
            result = dict(row)
            # Parse JSON fields
            for field in ['server_ids', 'config_files', 'source_data', 'operations', 'results_summary', 'metadata']:
                if isinstance(result.get(field), str):
                    result[field] = json.loads(result[field])
            return result

        return None


async def update_sync_batch_status(
    batch_id: uuid.UUID,
    status: str,
    results_summary: Optional[Dict[str, Any]] = None
) -> None:
    """
    Update sync batch status and results.

    Args:
        batch_id: UUID of the batch
        status: New status
        results_summary: Results summary dictionary
    """
    async with get_connection() as conn:
        await conn.execute(
            """
            UPDATE sync_batches
            SET status = $1,
                results_summary = COALESCE($2::jsonb, results_summary),
                updated_at = NOW()
            WHERE id = $3
            """,
            status,
            json.dumps(results_summary or {}),
            batch_id
        )


async def list_sync_batches(
    status: Optional[str] = None,
    initiated_by: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    List sync batches with optional filtering.

    Args:
        status: Filter by status
        initiated_by: Filter by initiator
        limit: Maximum number of batches to return
        offset: Number of batches to skip

    Returns:
        List of batch dictionaries
    """
    async with get_connection() as conn:
        query = "SELECT * FROM sync_batches WHERE 1=1"
        params = []
        param_count = 0

        # Add filters
        if status:
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append(status)

        if initiated_by:
            param_count += 1
            query += f" AND initiated_by = ${param_count}"
            params.append(initiated_by)

        # Add ordering and pagination
        query += " ORDER BY created_at DESC"
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)

        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)

        rows = await conn.fetch(query, *params)

        results = []
        for row in rows:
            result = dict(row)
            # Parse JSON fields
            for field in ['server_ids', 'config_files', 'source_data', 'operations', 'results_summary', 'metadata']:
                if isinstance(result.get(field), str):
                    result[field] = json.loads(result[field])
            results.append(result)

        return results


# ═══════════════════════════════════════════════════════════
# CONFIGURATION MANAGEMENT
# ═══════════════════════════════════════════════════════════


async def create_environment_sync_config(
    name: str,
    description: Optional[str],
    default_timeout: int,
    default_parallel_limit: int,
    default_backup_path: str,
    encryption_method: str,
    metadata: Optional[Dict[str, Any]] = None
) -> uuid.UUID:
    """
    Create environment synchronization configuration.

    Args:
        name: Configuration name
        description: Optional description
        default_timeout: Default operation timeout
        default_parallel_limit: Default parallel operations limit
        default_backup_path: Default backup path
        encryption_method: Default encryption method
        metadata: Additional metadata

    Returns:
        UUID of created configuration
    """
    config_id = uuid.uuid4()

    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO environment_sync_configs (
                id, name, description, default_timeout, default_parallel_limit,
                default_backup_path, encryption_method, metadata, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
            """,
            config_id,
            name,
            description,
            default_timeout,
            default_parallel_limit,
            default_backup_path,
            encryption_method,
            json.dumps(metadata or {})
        )

    return config_id


async def get_environment_sync_config() -> Optional[Dict[str, Any]]:
    """
    Get the active environment synchronization configuration.

    Returns:
        Configuration dictionary or None if not found
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM environment_sync_configs ORDER BY created_at DESC LIMIT 1"
        )

        if row:
            result = dict(row)
            if isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            return result

        return None


async def get_server_environments() -> List[Dict[str, Any]]:
    """
    Get all server environments.

    Returns:
        List of environment dictionaries
    """
    async with get_connection() as conn:
        rows = await conn.fetch(
            "SELECT * FROM server_environments ORDER BY name"
        )

        results = []
        for row in rows:
            result = dict(row)
            # Parse JSON fields
            for field in ['tags', 'variables']:
                if isinstance(result.get(field), str):
                    result[field] = json.loads(result[field])
            results.append(result)

        return results


async def get_server_statistics() -> Dict[str, Any]:
    """
    Get server statistics for monitoring.

    Returns:
        Dictionary with server statistics
    """
    async with get_connection() as conn:
        stats = {}

        # Total servers by status
        status_counts = await conn.fetch(
            """
            SELECT status, COUNT(*) as count
            FROM servers
            WHERE archived = false
            GROUP BY status
            """
        )
        stats['servers_by_status'] = {row['status']: row['count'] for row in status_counts}

        # Total servers by type
        type_counts = await conn.fetch(
            """
            SELECT server_type, COUNT(*) as count
            FROM servers
            WHERE archived = false
            GROUP BY server_type
            """
        )
        stats['servers_by_type'] = {row['server_type']: row['count'] for row in type_counts}

        # Servers by environment
        env_counts = await conn.fetch(
            """
            SELECT e.name, COUNT(*) as count
            FROM servers s
            JOIN server_environments e ON s.environment_id = e.id
            WHERE s.archived = false
            GROUP BY e.name
            """
        )
        stats['servers_by_environment'] = {row['name']: row['count'] for row in env_counts}

        # Recent sync operations
        recent_syncs = await conn.fetchrow(
            """
            SELECT
                COUNT(*) as total_operations,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'failed') as failed,
                COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress
            FROM sync_operations
            WHERE created_at > NOW() - INTERVAL '24 hours'
            """
        )
        stats['recent_sync_operations_24h'] = dict(recent_syncs)

        return stats