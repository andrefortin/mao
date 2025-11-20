#!/usr/bin/env python3
"""
Remote Operations Module

Handles SSH connections, file transfers, and remote command execution
for environment synchronization across distributed server networks.
"""

import os
import asyncio
import tempfile
import shutil
from typing import Optional, List, Dict, Any, Union, Tuple
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
import paramiko
from paramiko import SSHClient, AutoAddPolicy, RSAKey, ECDSAKey, Ed25519Key
from paramiko.ssh_exception import SSHException, AuthenticationException, BadHostKeyException
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from .logger import get_logger
from .config_models import ServerDefinition, AuthMethod, ConfigFile
from .config_encryption import get_encryption_manager, EncryptionError

logger = get_logger()


class RemoteOperationError(Exception):
    """Base exception for remote operations"""
    pass


class ConnectionError(RemoteOperationError):
    """Exception for connection failures"""
    pass


class AuthenticationError(RemoteOperationError):
    """Exception for authentication failures"""
    pass


class FileOperationError(RemoteOperationError):
    """Exception for file operation failures"""
    pass


class CommandExecutionError(RemoteOperationError):
    """Exception for command execution failures"""
    pass


class SSHConnection:
    """
    Manages SSH connections to remote servers with support for various authentication methods.
    """

    def __init__(
        self,
        server: ServerDefinition,
        connection_timeout: int = 30,
        keepalive_interval: int = 60
    ):
        """
        Initialize SSH connection.

        Args:
            server: Server definition with connection details
            connection_timeout: Connection timeout in seconds
            keepalive_interval: Keep-alive interval in seconds
        """
        self.server = server
        self.connection_timeout = connection_timeout
        self.keepalive_interval = keepalive_interval
        self.client: Optional[SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
        self.is_connected = False

        # Decrypt authentication method if needed
        self.encryption_manager = get_encryption_manager()
        self._auth_method = self._prepare_auth_method()

    def _prepare_auth_method(self) -> AuthMethod:
        """Prepare and decrypt authentication method"""
        try:
            # Ensure auth_method is a proper AuthMethod instance
            if isinstance(self.server.auth_method, dict):
                auth_dict = self.encryption_manager.decrypt_auth_method(self.server.auth_method)
                return AuthMethod(**auth_dict)
            return self.server.auth_method
        except Exception as e:
            logger.error(f"Failed to prepare authentication method: {e}")
            raise AuthenticationError(f"Authentication method preparation failed: {e}")

    async def connect(self) -> bool:
        """
        Establish SSH connection to the remote server.

        Returns:
            True if connection successful
        """
        try:
            if self.is_connected:
                return True

            logger.info(f"Connecting to {self.server.hostname}:{self.server.port}")

            # Create SSH client
            self.client = SSHClient()
            self.client.set_missing_host_key_policy(AutoAddPolicy())

            # Prepare authentication credentials
            auth_credentials = await self._prepare_auth_credentials()

            # Connect to server
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.connect(
                    hostname=self.server.hostname,
                    port=self.server.port,
                    timeout=self.connection_timeout,
                    auth_timeout=self.connection_timeout,
                    **auth_credentials
                )
            )

            # Enable keep-alive
            self.client.get_transport().set_keepalive(self.keepalive_interval)

            # Initialize SFTP client
            self.sftp = self.client.open_sftp()
            self.is_connected = True

            logger.success(f"Connected to {self.server.hostname}")
            return True

        except AuthenticationException as e:
            logger.error(f"Authentication failed for {self.server.hostname}: {e}")
            raise AuthenticationError(f"SSH authentication failed: {e}")
        except BadHostKeyException as e:
            logger.error(f"Host key verification failed for {self.server.hostname}: {e}")
            raise ConnectionError(f"Host key verification failed: {e}")
        except SSHException as e:
            logger.error(f"SSH connection failed to {self.server.hostname}: {e}")
            raise ConnectionError(f"SSH connection failed: {e}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.server.hostname}: {e}")
            raise ConnectionError(f"Connection failed: {e}")

    async def _prepare_auth_credentials(self) -> Dict[str, Any]:
        """Prepare authentication credentials based on auth method"""
        auth_method = self._auth_method

        if auth_method.type == "ssh_key":
            return await self._prepare_ssh_key_auth(auth_method)
        elif auth_method.type == "password":
            return await self._prepare_password_auth(auth_method)
        elif auth_method.type == "certificate":
            return await self._prepare_certificate_auth(auth_method)
        elif auth_method.type == "aws_instance_profile":
            return await self._prepare_aws_auth(auth_method)
        else:
            raise AuthenticationError(f"Unsupported authentication method: {auth_method.type}")

    async def _prepare_ssh_key_auth(self, auth_method: AuthMethod) -> Dict[str, Any]:
        """Prepare SSH key authentication"""
        try:
            if auth_method.private_key_data:
                # Use provided private key data
                key_data = auth_method.private_key_data
                if isinstance(key_data, str):
                    key_data = key_data.encode('utf-8')
                private_key = self._parse_private_key(key_data, auth_method.passphrase)
            elif auth_method.private_key_path:
                # Load private key from file
                if not os.path.exists(auth_method.private_key_path):
                    raise AuthenticationError(f"Private key file not found: {auth_method.private_key_path}")

                with open(auth_method.private_key_path, 'r') as f:
                    key_data = f.read()
                private_key = self._parse_private_key(key_data, auth_method.passphrase)
            else:
                raise AuthenticationError("No private key data or path provided")

            return {
                'username': auth_method.username,
                'pkey': private_key
            }

        except Exception as e:
            raise AuthenticationError(f"SSH key authentication preparation failed: {e}")

    async def _prepare_password_auth(self, auth_method: AuthMethod) -> Dict[str, Any]:
        """Prepare password authentication"""
        if not auth_method.username or not auth_method.password:
            raise AuthenticationError("Username and password required for password authentication")

        return {
            'username': auth_method.username,
            'password': auth_method.password
        }

    async def _prepare_certificate_auth(self, auth_method: AuthMethod) -> Dict[str, Any]:
        """Prepare certificate authentication"""
        try:
            if auth_method.certificate_data:
                cert_data = auth_method.certificate_data
                if isinstance(cert_data, str):
                    cert_data = cert_data.encode('utf-8')
            elif auth_method.certificate_path:
                if not os.path.exists(auth_method.certificate_path):
                    raise AuthenticationError(f"Certificate file not found: {auth_method.certificate_path}")

                with open(auth_method.certificate_path, 'r') as f:
                    cert_data = f.read()
            else:
                raise AuthenticationError("No certificate data or path provided")

            # Parse certificate
            from io import StringIO
            cert = paramiko.RSAKey.from_private_key(StringIO(cert_data))

            return {
                'username': auth_method.username,
                'pkey': cert
            }

        except Exception as e:
            raise AuthenticationError(f"Certificate authentication preparation failed: {e}")

    async def _prepare_aws_auth(self, auth_method: AuthMethod) -> Dict[str, Any]:
        """Prepare AWS instance profile authentication"""
        try:
            # Get temporary credentials from EC2 instance metadata
            session = boto3.Session(
                region_name=auth_method.aws_region,
                profile_name=auth_method.aws_profile
            )

            sts = session.client('sts')
            response = sts.get_caller_identity()

            # For AWS auth, we typically need to get the public key
            # This would require additional AWS services integration
            logger.warning("AWS instance profile authentication not fully implemented")
            return {'username': auth_method.username or 'ec2-user'}

        except NoCredentialsError:
            raise AuthenticationError("AWS credentials not found for instance profile authentication")
        except Exception as e:
            raise AuthenticationError(f"AWS authentication preparation failed: {e}")

    def _parse_private_key(self, key_data: Union[str, bytes], passphrase: Optional[str] = None) -> paramiko.PKey:
        """Parse private key in various formats"""
        try:
            if isinstance(key_data, str):
                key_data = key_data.encode('utf-8')

            key_password = passphrase.encode('utf-8') if passphrase else None

            # Try different key formats
            key_classes = [RSAKey, ECDSAKey, Ed25519Key]

            for key_class in key_classes:
                try:
                    return key_class.from_private_key_file(StringIO(key_data.decode()), password=key_password)
                except:
                    try:
                        return key_class.from_private_key(StringIO(key_data.decode()), password=key_password)
                    except:
                        continue

            raise AuthenticationError("Unable to parse private key in any supported format")

        except Exception as e:
            raise AuthenticationError(f"Private key parsing failed: {e}")

    async def execute_command(
        self,
        command: str,
        timeout: Optional[int] = None,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute command on remote server.

        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            working_directory: Working directory for command
            environment: Environment variables for command

        Returns:
            Dictionary with command execution results
        """
        if not self.is_connected:
            await self.connect()

        try:
            # Prepare command with working directory
            if working_directory:
                command = f"cd {working_directory} && {command}"

            # Prepare environment variables
            if environment:
                env_exports = " ".join([f'export {k}="{v}"' for k, v in environment.items()])
                command = f"{env_exports} && {command}"

            logger.debug(f"Executing command on {self.server.hostname}: {command}")

            # Execute command
            stdin, stdout, stderr = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.exec_command(command, timeout=timeout or self.connection_timeout)
            )

            # Read output
            stdout_data = await asyncio.get_event_loop().run_in_executor(
                None, stdout.read
            )
            stderr_data = await asyncio.get_event_loop().run_in_executor(
                None, stderr.read
            )
            exit_code = await asyncio.get_event_loop().run_in_executor(
                None, stdout.channel.recv_exit_status
            )

            result = {
                'command': command,
                'exit_code': exit_code,
                'stdout': stdout_data.decode('utf-8') if stdout_data else '',
                'stderr': stderr_data.decode('utf-8') if stderr_data else '',
                'success': exit_code == 0,
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.debug(f"Command completed on {self.server.hostname} with exit code {exit_code}")
            return result

        except Exception as e:
            logger.error(f"Command execution failed on {self.server.hostname}: {e}")
            raise CommandExecutionError(f"Command execution failed: {e}")

    async def upload_file(
        self,
        local_path: Union[str, Path],
        remote_path: str,
        permissions: Optional[int] = None,
        create_directories: bool = True
    ) -> Dict[str, Any]:
        """
        Upload file to remote server.

        Args:
            local_path: Local file path
            remote_path: Remote file path
            permissions: File permissions (octal)
            create_directories: Create remote directories if needed

        Returns:
            Dictionary with upload results
        """
        if not self.is_connected:
            await self.connect()

        try:
            local_path = Path(local_path)

            if not local_path.exists():
                raise FileOperationError(f"Local file not found: {local_path}")

            # Create remote directories if needed
            if create_directories:
                remote_dir = str(Path(remote_path).parent)
                await self.execute_command(f"mkdir -p {remote_dir}")

            logger.debug(f"Uploading {local_path} to {self.server.hostname}:{remote_path}")

            # Upload file
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.sftp.put(str(local_path), remote_path)
            )

            # Set permissions if specified
            if permissions:
                await self.execute_command(f"chmod {permissions:o} {remote_path}")

            # Verify upload
            local_size = local_path.stat().st_size
            remote_stat = await asyncio.get_event_loop().run_in_executor(
                None, self.sftp.stat, remote_path
            )
            remote_size = remote_stat.st_size

            result = {
                'local_path': str(local_path),
                'remote_path': remote_path,
                'local_size': local_size,
                'remote_size': remote_size,
                'success': local_size == remote_size,
                'permissions': permissions,
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.success(f"File uploaded to {self.server.hostname}: {remote_path}")
            return result

        except Exception as e:
            logger.error(f"File upload failed to {self.server.hostname}: {e}")
            raise FileOperationError(f"File upload failed: {e}")

    async def download_file(
        self,
        remote_path: str,
        local_path: Union[str, Path],
        create_directories: bool = True
    ) -> Dict[str, Any]:
        """
        Download file from remote server.

        Args:
            remote_path: Remote file path
            local_path: Local file path
            create_directories: Create local directories if needed

        Returns:
            Dictionary with download results
        """
        if not self.is_connected:
            await self.connect()

        try:
            local_path = Path(local_path)

            # Create local directories if needed
            if create_directories:
                local_path.parent.mkdir(parents=True, exist_ok=True)

            logger.debug(f"Downloading {self.server.hostname}:{remote_path} to {local_path}")

            # Download file
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.sftp.get(remote_path, str(local_path))
            )

            # Verify download
            remote_stat = await asyncio.get_event_loop().run_in_executor(
                None, self.sftp.stat, remote_path
            )
            remote_size = remote_stat.st_size
            local_size = local_path.stat().st_size

            result = {
                'remote_path': remote_path,
                'local_path': str(local_path),
                'remote_size': remote_size,
                'local_size': local_size,
                'success': remote_size == local_size,
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.success(f"File downloaded from {self.server.hostname}: {remote_path}")
            return result

        except Exception as e:
            logger.error(f"File download failed from {self.server.hostname}: {e}")
            raise FileOperationError(f"File download failed: {e}")

    async def file_exists(self, remote_path: str) -> bool:
        """Check if remote file exists"""
        if not self.is_connected:
            await self.connect()

        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self.sftp.stat, remote_path
            )
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"File existence check failed on {self.server.hostname}: {e}")
            return False

    async def create_backup(self, file_path: str, backup_dir: Optional[str] = None) -> Optional[str]:
        """
        Create backup of remote file.

        Args:
            file_path: File to backup
            backup_dir: Backup directory (optional)

        Returns:
            Backup file path if successful, None otherwise
        """
        try:
            if not await self.file_exists(file_path):
                logger.warning(f"File to backup does not exist: {file_path}")
                return None

            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = Path(file_path).name
            backup_filename = f"{filename}.backup_{timestamp}"

            if backup_dir:
                backup_path = f"{backup_dir.rstrip('/')}/{backup_filename}"
                # Create backup directory
                await self.execute_command(f"mkdir -p {backup_dir}")
            else:
                backup_path = f"{file_path}.backup_{timestamp}"

            # Copy file to backup location
            result = await self.execute_command(f"cp {file_path} {backup_path}")

            if result['success']:
                logger.success(f"Backup created: {backup_path}")
                return backup_path
            else:
                logger.error(f"Backup creation failed: {result.get('stderr', 'Unknown error')}")
                return None

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return None

    async def disconnect(self):
        """Close SSH connection"""
        try:
            if self.sftp:
                self.sftp.close()
                self.sftp = None

            if self.client:
                self.client.close()
                self.client = None

            self.is_connected = False
            logger.debug(f"Disconnected from {self.server.hostname}")

        except Exception as e:
            logger.error(f"Error during disconnect from {self.server.hostname}: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


class RemoteOperationsManager:
    """
    Manages remote operations across multiple servers with connection pooling and retry logic.
    """

    def __init__(self, max_connections: int = 10):
        """
        Initialize remote operations manager.

        Args:
            max_connections: Maximum concurrent connections
        """
        self.max_connections = max_connections
        self.active_connections: Dict[str, SSHConnection] = {}
        self.connection_semaphore = asyncio.Semaphore(max_connections)

    async def get_connection(self, server: ServerDefinition) -> SSHConnection:
        """Get or create SSH connection for server"""
        server_key = f"{server.hostname}:{server.port}"

        if server_key in self.active_connections:
            connection = self.active_connections[server_key]
            if connection.is_connected:
                return connection
            else:
                # Remove stale connection
                del self.active_connections[server_key]

        # Create new connection
        connection = SSHConnection(server)
        self.active_connections[server_key] = connection
        return connection

    async def close_connection(self, server: ServerDefinition):
        """Close connection for server"""
        server_key = f"{server.hostname}:{server.port}"

        if server_key in self.active_connections:
            await self.active_connections[server_key].disconnect()
            del self.active_connections[server_key]

    async def close_all_connections(self):
        """Close all active connections"""
        for connection in self.active_connections.values():
            await connection.disconnect()
        self.active_connections.clear()

    @asynccontextmanager
    async def server_connection(self, server: ServerDefinition):
        """Context manager for server connection"""
        async with self.connection_semaphore:
            connection = await self.get_connection(server)
            try:
                yield connection
            finally:
                # Don't close connection here - let connection pooling handle it
                pass

    async def sync_config_file(
        self,
        server: ServerDefinition,
        config_file: ConfigFile,
        source_data: str,
        create_backup: bool = True,
        validate_after_sync: bool = True
    ) -> Dict[str, Any]:
        """
        Synchronize a single configuration file to remote server.

        Args:
            server: Target server
            config_file: Configuration file definition
            source_data: Source configuration data
            create_backup: Create backup before sync
            validate_after_sync: Validate configuration after sync

        Returns:
            Dictionary with sync results
        """
        result = {
            'server': server.name,
            'config_file': config_file.path,
            'success': False,
            'backup_path': None,
            'validation_results': None,
            'error': None,
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            async with self.server_connection(server) as conn:
                # Create backup if requested
                backup_path = None
                if create_backup and await conn.file_exists(config_file.path):
                    backup_path = await conn.create_backup(
                        config_file.path,
                        server.backup_path
                    )
                    result['backup_path'] = backup_path

                # Write source data to temporary file
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                    temp_file.write(source_data)
                    temp_path = temp_file.name

                try:
                    # Upload configuration file
                    upload_result = await conn.upload_file(
                        temp_path,
                        config_file.path,
                        create_directories=True
                    )

                    if not upload_result['success']:
                        result['error'] = "File upload failed"
                        return result

                    # Run validation commands if specified
                    if config_file.validation_commands:
                        for validation_cmd in config_file.validation_commands:
                            cmd_result = await conn.execute_command(validation_cmd)
                            if not cmd_result['success']:
                                result['error'] = f"Validation failed: {cmd_result['stderr']}"
                                # Restore backup if available
                                if backup_path:
                                    await conn.execute_command(f"mv {backup_path} {config_file.path}")
                                return result

                    # Run post-sync commands if specified
                    if config_file.post_sync_commands:
                        for post_cmd in config_file.post_sync_commands:
                            cmd_result = await conn.execute_command(post_cmd)
                            if not cmd_result['success']:
                                logger.warning(f"Post-sync command failed: {post_cmd}")

                    result['success'] = True
                    logger.success(f"Configuration file synced to {server.name}: {config_file.path}")

                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Configuration sync failed for {server.name}: {e}")

        return result

    async def validate_remote_config(
        self,
        server: ServerDefinition,
        config_file: ConfigFile
    ) -> Dict[str, Any]:
        """
        Validate configuration file on remote server.

        Args:
            server: Target server
            config_file: Configuration file to validate

        Returns:
            Dictionary with validation results
        """
        result = {
            'server': server.name,
            'config_file': config_file.path,
            'valid': False,
            'errors': [],
            'warnings': [],
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            async with self.server_connection(server) as conn:
                # Check if file exists
                if not await conn.file_exists(config_file.path):
                    result['errors'].append(f"Configuration file not found: {config_file.path}")
                    return result

                # Run validation commands if specified
                if config_file.validation_commands:
                    for validation_cmd in config_file.validation_commands:
                        cmd_result = await conn.execute_command(validation_cmd)
                        if cmd_result['success']:
                            if cmd_result['stderr']:
                                result['warnings'].append(cmd_result['stderr'])
                        else:
                            result['errors'].append(f"Validation command failed: {cmd_result['stderr']}")
                else:
                    # Basic syntax validation based on file type
                    if config_file.type.value == 'yaml':
                        cmd_result = await conn.execute_command(f"python3 -c 'import yaml; yaml.safe_load(open(\"{config_file.path}\"))'")
                        if cmd_result['success']:
                            result['valid'] = True
                        else:
                            result['errors'].append(f"YAML syntax error: {cmd_result['stderr']}")
                    elif config_file.type.value == 'json':
                        cmd_result = await conn.execute_command(f"python3 -m json.tool {config_file.path}")
                        if cmd_result['success']:
                            result['valid'] = True
                        else:
                            result['errors'].append(f"JSON syntax error: {cmd_result['stderr']}")
                    else:
                        # For other types, just check if file is readable
                        result['valid'] = True

        except Exception as e:
            result['errors'].append(f"Validation error: {str(e)}")
            logger.error(f"Configuration validation failed for {server.name}: {e}")

        return result


# Global remote operations manager
_remote_ops_manager: Optional[RemoteOperationsManager] = None


def get_remote_operations_manager() -> RemoteOperationsManager:
    """Get the global remote operations manager"""
    global _remote_ops_manager
    if _remote_ops_manager is None:
        _remote_ops_manager = RemoteOperationsManager()
    return _remote_ops_manager


def initialize_remote_operations_manager(max_connections: int = 10) -> RemoteOperationsManager:
    """Initialize the global remote operations manager"""
    global _remote_ops_manager
    _remote_ops_manager = RemoteOperationsManager(max_connections)
    return _remote_ops_manager


# Import StringIO for key parsing
from io import StringIO