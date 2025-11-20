#!/usr/bin/env python3
"""
Environment Synchronization Module

Main orchestrator for environment configuration synchronization
across distributed server networks with comprehensive validation,
security, and monitoring capabilities.
"""

import asyncio
import uuid
from typing import Optional, List, Dict, Any, Set, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json

from .logger import get_logger
from .config_models import (
    ServerDefinition, SyncOperation, SyncBatch, SyncStatus, ConfigFile,
    ServerStatus, EnvironmentSyncConfig, ValidationResponse
)
from .config_encryption import get_encryption_manager, EncryptionError
from .config_validator import get_config_validator, ValidationResult
from .remote_operations import get_remote_operations_manager, RemoteOperationsManager
from .websocket_manager import get_websocket_manager

logger = get_logger()


class EnvironmentSyncError(Exception):
    """Base exception for environment synchronization"""
    pass


class SyncOperationError(EnvironmentSyncError):
    """Exception for sync operation failures"""
    pass


class ValidationFailureError(EnvironmentSyncError):
    """Exception for validation failures"""
    pass


class RollbackError(EnvironmentSyncError):
    """Exception for rollback failures"""
    pass


class SyncOperationManager:
    """
    Manages individual synchronization operations with comprehensive
    validation, execution, monitoring, and rollback capabilities.
    """

    def __init__(
        self,
        remote_ops_manager: RemoteOperationsManager,
        ws_manager,
        config_validator,
        encryption_manager
    ):
        """
        Initialize sync operation manager.

        Args:
            remote_ops_manager: Remote operations manager
            ws_manager: WebSocket manager for real-time updates
            config_validator: Configuration validator
            encryption_manager: Encryption manager
        """
        self.remote_ops_manager = remote_ops_manager
        self.ws_manager = ws_manager
        self.config_validator = config_validator
        self.encryption_manager = encryption_manager

    async def execute_sync_operation(self, operation: SyncOperation) -> SyncOperation:
        """
        Execute a single synchronization operation.

        Args:
            operation: Sync operation to execute

        Returns:
            Updated sync operation with results
        """
        try:
            logger.info(f"Starting sync operation: {operation.id}")
            operation.status = SyncStatus.IN_PROGRESS
            operation.started_at = datetime.utcnow()

            # Broadcast operation start
            await self._broadcast_operation_update(operation)

            # Get server definition
            server = await self._get_server_definition(operation.server_id)
            if not server:
                raise SyncOperationError(f"Server not found: {operation.server_id}")

            # Validate configuration before sync
            validation_results = []
            for config_file in operation.config_files:
                source_data = operation.source_data.get(config_file.path, "")
                validation_result = await self.config_validator.validate_config(
                    source_data, config_file, server
                )
                validation_results.append({
                    'file_path': config_file.path,
                    'validation': validation_result
                })

                # Check validation failures
                if not validation_result.valid and operation.validate_after_sync:
                    operation.status = SyncStatus.FAILED
                    operation.errors.append(f"Validation failed for {config_file.path}: {validation_result.errors}")
                    await self._broadcast_operation_update(operation)
                    return operation

            # Execute sync if not a dry run
            if not operation.dry_run:
                sync_results = await self._execute_config_sync(
                    server, operation.config_files, operation.source_data,
                    operation.create_backups, operation.validate_after_sync
                )

                # Process sync results
                for result in sync_results:
                    if not result['success']:
                        operation.errors.append(f"Sync failed for {result['config_file']}: {result.get('error', 'Unknown error')}")

                    operation.results[result['config_file']] = result

                # Determine overall success
                if all(result['success'] for result in sync_results):
                    operation.status = SyncStatus.COMPLETED
                    server.last_sync = datetime.utcnow()
                    await self._update_server_status(server)
                else:
                    operation.status = SyncStatus.FAILED
                    # Attempt rollback if configured
                    if operation.create_backups:
                        await self._attempt_rollback(operation, sync_results)
            else:
                # Dry run - only validation
                operation.status = SyncStatus.COMPLETED
                operation.results['dry_run'] = {
                    'validation_results': validation_results,
                    'files_to_sync': [f.path for f in operation.config_files]
                }

            operation.completed_at = datetime.utcnow()
            await self._broadcast_operation_update(operation)

            logger.info(f"Sync operation completed: {operation.id} - {operation.status.value}")
            return operation

        except Exception as e:
            logger.error(f"Sync operation failed: {operation.id} - {e}")
            operation.status = SyncStatus.FAILED
            operation.errors.append(str(e))
            operation.completed_at = datetime.utcnow()
            await self._broadcast_operation_update(operation)
            return operation

    async def _get_server_definition(self, server_id: uuid.UUID) -> Optional[ServerDefinition]:
        """Get server definition from database"""
        # This would integrate with the database module
        # For now, return None - will be implemented in database extension
        return None

    async def _execute_config_sync(
        self,
        server: ServerDefinition,
        config_files: List[ConfigFile],
        source_data: Dict[str, str],
        create_backups: bool,
        validate_after_sync: bool
    ) -> List[Dict[str, Any]]:
        """Execute configuration synchronization"""
        results = []

        for config_file in config_files:
            file_data = source_data.get(config_file.path, "")
            result = await self.remote_ops_manager.sync_config_file(
                server, config_file, file_data, create_backups, validate_after_sync
            )
            results.append(result)

        return results

    async def _attempt_rollback(self, operation: SyncOperation, sync_results: List[Dict[str, Any]]):
        """Attempt rollback of failed sync operation"""
        logger.warning(f"Attempting rollback for operation: {operation.id}")

        try:
            server = await self._get_server_definition(operation.server_id)
            if not server:
                logger.error("Cannot rollback: server not found")
                return

            rollback_successful = True
            for result in sync_results:
                if result.get('backup_path'):
                    # Restore from backup
                    async with self.remote_ops_manager.server_connection(server) as conn:
                        restore_result = await conn.execute_command(
                            f"mv {result['backup_path']} {result['config_file']}"
                        )
                        if not restore_result['success']:
                            rollback_successful = False
                            operation.warnings.append(f"Rollback failed for {result['config_file']}")

            if rollback_successful:
                operation.status = SyncStatus.ROLLED_BACK
                logger.info(f"Rollback successful for operation: {operation.id}")
            else:
                operation.warnings.append("Partial rollback completed - some files could not be restored")

        except Exception as e:
            logger.error(f"Rollback failed for operation {operation.id}: {e}")
            operation.warnings.append(f"Rollback failed: {str(e)}")

    async def _update_server_status(self, server: ServerDefinition):
        """Update server status in database"""
        # This would integrate with the database module
        pass

    async def _broadcast_operation_update(self, operation: SyncOperation):
        """Broadcast operation update via WebSocket"""
        try:
            await self.ws_manager.broadcast({
                'type': 'environment_sync_operation_update',
                'operation_id': str(operation.id),
                'server_id': str(operation.server_id),
                'status': operation.status.value,
                'progress': {
                    'started_at': operation.started_at.isoformat() if operation.started_at else None,
                    'completed_at': operation.completed_at.isoformat() if operation.completed_at else None,
                    'errors_count': len(operation.errors),
                    'warnings_count': len(operation.warnings),
                    'files_processed': len(operation.results)
                }
            })
        except Exception as e:
            logger.error(f"Failed to broadcast operation update: {e}")


class BatchSyncManager:
    """
    Manages batch synchronization operations across multiple servers
    with parallel execution and comprehensive monitoring.
    """

    def __init__(
        self,
        sync_operation_manager: SyncOperationManager,
        ws_manager,
        max_parallel_operations: int = 5
    ):
        """
        Initialize batch sync manager.

        Args:
            sync_operation_manager: Individual sync operation manager
            ws_manager: WebSocket manager for real-time updates
            max_parallel_operations: Maximum parallel operations
        """
        self.sync_operation_manager = sync_operation_manager
        self.ws_manager = ws_manager
        self.max_parallel_operations = max_parallel_operations

    async def execute_batch_sync(self, batch: SyncBatch) -> SyncBatch:
        """
        Execute a batch synchronization operation.

        Args:
            batch: Batch sync operation to execute

        Returns:
            Updated batch with results
        """
        try:
            logger.info(f"Starting batch sync: {batch.id}")
            batch.status = SyncStatus.IN_PROGRESS
            batch.started_at = datetime.utcnow()
            batch.total_operations = len(batch.operations)

            await self._broadcast_batch_update(batch)

            # Prepare operations
            if not batch.operations:
                # Create operations from server list and config files
                batch.operations = await self._prepare_operations(batch)

            # Execute operations (parallel or sequential)
            if batch.parallel_execution:
                await self._execute_parallel(batch)
            else:
                await self._execute_sequential(batch)

            # Calculate results summary
            batch.successful_operations = sum(1 for op in batch.operations if op.status == SyncStatus.COMPLETED)
            batch.failed_operations = sum(1 for op in batch.operations if op.status == SyncStatus.FAILED)

            batch.results_summary = {
                'total_operations': batch.total_operations,
                'successful_operations': batch.successful_operations,
                'failed_operations': batch.failed_operations,
                'success_rate': batch.successful_operations / batch.total_operations if batch.total_operations > 0 else 0,
                'files_synced': sum(len(op.results) for op in batch.operations),
                'total_errors': sum(len(op.errors) for op in batch.operations),
                'total_warnings': sum(len(op.warnings) for op in batch.operations)
            }

            # Determine overall status
            if batch.failed_operations == 0:
                batch.status = SyncStatus.COMPLETED
            elif batch.continue_on_error:
                batch.status = SyncStatus.COMPLETED  # Partial success
            else:
                batch.status = SyncStatus.FAILED

            batch.completed_at = datetime.utcnow()
            await self._broadcast_batch_update(batch)

            logger.info(f"Batch sync completed: {batch.id} - {batch.status.value}")
            return batch

        except Exception as e:
            logger.error(f"Batch sync failed: {batch.id} - {e}")
            batch.status = SyncStatus.FAILED
            batch.errors.append(str(e))
            batch.completed_at = datetime.utcnow()
            await self._broadcast_batch_update(batch)
            return batch

    async def _prepare_operations(self, batch: SyncBatch) -> List[SyncOperation]:
        """Prepare individual operations from batch configuration"""
        operations = []

        for server_id in batch.server_ids:
            operation = SyncOperation(
                id=uuid.uuid4(),
                server_id=server_id,
                operation_type="full_sync",
                config_files=batch.config_files,
                source_data=batch.source_data,
                dry_run=batch.dry_run,
                force_overwrite=False,
                create_backups=True,
                validate_after_sync=True,
                initiated_by=batch.initiated_by,
                metadata=batch.metadata
            )
            operations.append(operation)

        return operations

    async def _execute_parallel(self, batch: SyncBatch):
        """Execute operations in parallel"""
        semaphore = asyncio.Semaphore(batch.max_parallel_servers)

        async def execute_with_semaphore(operation):
            async with semaphore:
                return await self.sync_operation_manager.execute_sync_operation(operation)

        tasks = [execute_with_semaphore(op) for op in batch.operations]
        batch.operations = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        for i, result in enumerate(batch.operations):
            if isinstance(result, Exception):
                batch.operations[i] = batch.operations[i]  # Keep original operation
                batch.operations[i].status = SyncStatus.FAILED
                batch.operations[i].errors.append(str(result))

    async def _execute_sequential(self, batch: SyncBatch):
        """Execute operations sequentially"""
        for i, operation in enumerate(batch.operations):
            try:
                updated_operation = await self.sync_operation_manager.execute_sync_operation(operation)
                batch.operations[i] = updated_operation

                # Stop on first error if not continuing on error
                if updated_operation.status == SyncStatus.FAILED and not batch.continue_on_error:
                    logger.warning(f"Stopping batch execution due to failure: {updated_operation.errors}")
                    break

            except Exception as e:
                batch.operations[i].status = SyncStatus.FAILED
                batch.operations[i].errors.append(str(e))

                if not batch.continue_on_error:
                    logger.warning(f"Stopping batch execution due to error: {e}")
                    break

    async def _broadcast_batch_update(self, batch: SyncBatch):
        """Broadcast batch update via WebSocket"""
        try:
            await self.ws_manager.broadcast({
                'type': 'environment_sync_batch_update',
                'batch_id': str(batch.id),
                'status': batch.status.value,
                'progress': {
                    'started_at': batch.started_at.isoformat() if batch.started_at else None,
                    'completed_at': batch.completed_at.isoformat() if batch.completed_at else None,
                    'total_operations': batch.total_operations,
                    'successful_operations': batch.successful_operations,
                    'failed_operations': batch.failed_operations,
                    'progress_percentage': (batch.successful_operations + batch.failed_operations) / batch.total_operations * 100 if batch.total_operations > 0 else 0
                },
                'results_summary': batch.results_summary
            })
        except Exception as e:
            logger.error(f"Failed to broadcast batch update: {e}")


class EnvironmentSynchronizationManager:
    """
    Main environment synchronization orchestrator that coordinates
    all sync operations, validation, security, and monitoring.
    """

    def __init__(self, config: Optional[EnvironmentSyncConfig] = None):
        """
        Initialize environment synchronization manager.

        Args:
            config: Global synchronization configuration
        """
        self.config = config or EnvironmentSyncConfig(name="default")
        self.encryption_manager = get_encryption_manager()
        self.config_validator = get_config_validator()
        self.remote_ops_manager = get_remote_operations_manager()
        self.ws_manager = get_websocket_manager()

        # Initialize sub-managers
        self.sync_operation_manager = SyncOperationManager(
            self.remote_ops_manager,
            self.ws_manager,
            self.config_validator,
            self.encryption_manager
        )
        self.batch_sync_manager = BatchSyncManager(
            self.sync_operation_manager,
            self.ws_manager,
            self.config.default_parallel_limit
        )

        # Active operations tracking
        self.active_operations: Dict[uuid.UUID, SyncOperation] = {}
        self.active_batches: Dict[uuid.UUID, SyncBatch] = {}

        logger.info("Environment Synchronization Manager initialized")

    async def validate_configuration(
        self,
        config_data: Dict[str, str],
        config_files: List[ConfigFile],
        server_id: Optional[uuid.UUID] = None
    ) -> Dict[str, ValidationResult]:
        """
        Validate configuration data for multiple files.

        Args:
            config_data: Configuration data by file path
            config_files: List of configuration file definitions
            server_id: Server ID for context validation (optional)

        Returns:
            Dictionary of validation results by file path
        """
        results = {}

        server = None
        if server_id:
            server = await self._get_server_definition(server_id)

        for config_file in config_files:
            file_data = config_data.get(config_file.path, "")
            validation_result = await self.config_validator.validate_config(
                file_data, config_file, server
            )
            results[config_file.path] = validation_result

        return results

    async def create_sync_operation(
        self,
        server_id: uuid.UUID,
        config_files: List[ConfigFile],
        source_data: Dict[str, str],
        operation_type: str = "full_sync",
        dry_run: bool = False,
        initiated_by: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> SyncOperation:
        """
        Create a new synchronization operation.

        Args:
            server_id: Target server ID
            config_files: Configuration files to sync
            source_data: Source configuration data
            operation_type: Type of operation
            dry_run: Perform dry run without making changes
            initiated_by: Who initiated the operation
            metadata: Additional metadata

        Returns:
            Created sync operation
        """
        operation = SyncOperation(
            id=uuid.uuid4(),
            server_id=server_id,
            operation_type=operation_type,
            config_files=config_files,
            source_data=source_data,
            dry_run=dry_run,
            force_overwrite=False,
            create_backups=True,
            validate_after_sync=True,
            initiated_by=initiated_by,
            metadata=metadata or {}
        )

        self.active_operations[operation.id] = operation
        await self._broadcast_operation_created(operation)

        logger.info(f"Created sync operation: {operation.id} for server: {server_id}")
        return operation

    async def create_batch_sync(
        self,
        name: str,
        server_ids: List[uuid.UUID],
        config_files: List[ConfigFile],
        source_data: Dict[str, str],
        initiated_by: str = "system",
        parallel_execution: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SyncBatch:
        """
        Create a new batch synchronization operation.

        Args:
            name: Batch operation name
            server_ids: Target server IDs
            config_files: Configuration files to sync
            source_data: Source configuration data
            initiated_by: Who initiated the batch
            parallel_execution: Execute operations in parallel
            metadata: Additional metadata

        Returns:
            Created batch sync operation
        """
        batch = SyncBatch(
            id=uuid.uuid4(),
            name=name,
            server_ids=server_ids,
            config_files=config_files,
            source_data=source_data,
            parallel_execution=parallel_execution,
            max_parallel_servers=self.config.default_parallel_limit,
            continue_on_error=False,
            initiated_by=initiated_by,
            metadata=metadata or {}
        )

        self.active_batches[batch.id] = batch
        await self._broadcast_batch_created(batch)

        logger.info(f"Created batch sync: {batch.id} for {len(server_ids)} servers")
        return batch

    async def execute_sync_operation(self, operation_id: uuid.UUID) -> SyncOperation:
        """
        Execute a synchronization operation.

        Args:
            operation_id: Operation ID to execute

        Returns:
            Updated operation with results
        """
        if operation_id not in self.active_operations:
            raise SyncOperationError(f"Operation not found: {operation_id}")

        operation = self.active_operations[operation_id]
        updated_operation = await self.sync_operation_manager.execute_sync_operation(operation)

        # Remove from active operations if completed
        if updated_operation.status in [SyncStatus.COMPLETED, SyncStatus.FAILED, SyncStatus.ROLLED_BACK]:
            del self.active_operations[operation_id]

        return updated_operation

    async def execute_batch_sync(self, batch_id: uuid.UUID) -> SyncBatch:
        """
        Execute a batch synchronization operation.

        Args:
            batch_id: Batch ID to execute

        Returns:
            Updated batch with results
        """
        if batch_id not in self.active_batches:
            raise SyncOperationError(f"Batch not found: {batch_id}")

        batch = self.active_batches[batch_id]
        updated_batch = await self.batch_sync_manager.execute_batch_sync(batch)

        # Remove from active batches if completed
        if updated_batch.status in [SyncStatus.COMPLETED, SyncStatus.FAILED]:
            del self.active_batches[batch_id]

        return updated_batch

    async def get_operation_status(self, operation_id: uuid.UUID) -> Optional[SyncOperation]:
        """Get current status of a sync operation"""
        return self.active_operations.get(operation_id)

    async def get_batch_status(self, batch_id: uuid.UUID) -> Optional[SyncBatch]:
        """Get current status of a batch sync operation"""
        return self.active_batches.get(batch_id)

    async def cancel_operation(self, operation_id: uuid.UUID) -> bool:
        """
        Cancel an active synchronization operation.

        Args:
            operation_id: Operation ID to cancel

        Returns:
            True if operation was cancelled
        """
        if operation_id in self.active_operations:
            operation = self.active_operations[operation_id]
            operation.status = SyncStatus.FAILED
            operation.errors.append("Operation cancelled by user")
            operation.completed_at = datetime.utcnow()

            await self._broadcast_operation_update(operation)
            del self.active_operations[operation_id]

            logger.info(f"Cancelled sync operation: {operation_id}")
            return True

        return False

    async def cancel_batch(self, batch_id: uuid.UUID) -> bool:
        """
        Cancel an active batch synchronization.

        Args:
            batch_id: Batch ID to cancel

        Returns:
            True if batch was cancelled
        """
        if batch_id in self.active_batches:
            batch = self.active_batches[batch_id]
            batch.status = SyncStatus.FAILED
            batch.errors.append("Batch cancelled by user")
            batch.completed_at = datetime.utcnow()

            await self._broadcast_batch_update(batch)
            del self.active_batches[batch_id]

            logger.info(f"Cancelled batch sync: {batch_id}")
            return True

        return False

    async def get_active_operations(self) -> List[SyncOperation]:
        """Get list of all active operations"""
        return list(self.active_operations.values())

    async def get_active_batches(self) -> List[SyncBatch]:
        """Get list of all active batch operations"""
        return list(self.active_batches.values())

    async def _get_server_definition(self, server_id: uuid.UUID) -> Optional[ServerDefinition]:
        """Get server definition from database"""
        # This will integrate with the database module
        return None

    async def _broadcast_operation_created(self, operation: SyncOperation):
        """Broadcast operation creation event"""
        await self.ws_manager.broadcast({
            'type': 'environment_sync_operation_created',
            'operation': operation.dict(),
            'timestamp': datetime.utcnow().isoformat()
        })

    async def _broadcast_operation_update(self, operation: SyncOperation):
        """Broadcast operation update event"""
        await self.ws_manager.broadcast({
            'type': 'environment_sync_operation_update',
            'operation': operation.dict(),
            'timestamp': datetime.utcnow().isoformat()
        })

    async def _broadcast_batch_created(self, batch: SyncBatch):
        """Broadcast batch creation event"""
        await self.ws_manager.broadcast({
            'type': 'environment_sync_batch_created',
            'batch': batch.dict(),
            'timestamp': datetime.utcnow().isoformat()
        })

    async def _broadcast_batch_update(self, batch: SyncBatch):
        """Broadcast batch update event"""
        await self.ws_manager.broadcast({
            'type': 'environment_sync_batch_update',
            'batch': batch.dict(),
            'timestamp': datetime.utcnow().isoformat()
        })

    async def shutdown(self):
        """Shutdown the environment sync manager"""
        logger.info("Shutting down Environment Synchronization Manager")

        # Cancel all active operations
        for operation_id in list(self.active_operations.keys()):
            await self.cancel_operation(operation_id)

        # Cancel all active batches
        for batch_id in list(self.active_batches.keys()):
            await self.cancel_batch(batch_id)

        # Close remote connections
        await self.remote_ops_manager.close_all_connections()

        logger.info("Environment Synchronization Manager shutdown complete")


# Global environment sync manager
_env_sync_manager: Optional[EnvironmentSynchronizationManager] = None


def get_environment_sync_manager() -> EnvironmentSynchronizationManager:
    """Get the global environment sync manager"""
    global _env_sync_manager
    if _env_sync_manager is None:
        _env_sync_manager = EnvironmentSynchronizationManager()
    return _env_sync_manager


def initialize_environment_sync_manager(config: Optional[EnvironmentSyncConfig] = None) -> EnvironmentSynchronizationManager:
    """Initialize the global environment sync manager"""
    global _env_sync_manager
    _env_sync_manager = EnvironmentSynchronizationManager(config)
    return _env_sync_manager