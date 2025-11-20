#!/usr/bin/env python3
"""
Configuration Validator Module

Validates configuration files against schemas, security policies,
and best practices for various configuration formats.
"""

import os
import re
import json
import yaml
import toml
import configparser
from typing import Optional, List, Dict, Any, Union, Tuple
from pathlib import Path
from datetime import datetime
import subprocess
import tempfile
import ast
from pydantic import BaseModel, ValidationError

from .logger import get_logger
from .config_models import ConfigType, ValidationRule, ConfigFile, ServerDefinition

logger = get_logger()


class ValidationResult(BaseModel):
    """Configuration validation result"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []
    security_issues: List[str] = []
    metadata: Dict[str, Any] = {}

    def add_error(self, message: str):
        """Add error message"""
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str):
        """Add warning message"""
        self.warnings.append(message)

    def add_suggestion(self, message: str):
        """Add suggestion message"""
        self.suggestions.append(message)

    def add_security_issue(self, message: str):
        """Add security issue message"""
        self.security_issues.append(message)


class ConfigurationValidator:
    """
    Validates configuration files against various criteria including
    syntax, semantic correctness, security policies, and best practices.
    """

    def __init__(self, enable_security_validation: bool = True):
        """
        Initialize configuration validator.

        Args:
            enable_security_validation: Enable security policy validation
        """
        self.enable_security_validation = enable_security_validation
        self.security_patterns = self._initialize_security_patterns()
        self.validation_rules = self._initialize_validation_rules()

    def _initialize_security_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize security validation patterns"""
        return {
            'passwords': [
                {'pattern': r'password\s*[:=]\s*["\']?([^"\']+)', 'severity': 'high'},
                {'pattern': r'passwd\s*[:=]\s*["\']?([^"\']+)', 'severity': 'high'},
                {'pattern': r'secret\s*[:=]\s*["\']?([^"\']+)', 'severity': 'high'},
                {'pattern': r'api_key\s*[:=]\s*["\']?([^"\']+)', 'severity': 'high'},
            ],
            'private_keys': [
                {'pattern': r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', 'severity': 'critical'},
                {'pattern': r'-----BEGIN\s+EC\s+PRIVATE\s+KEY-----', 'severity': 'critical'},
                {'pattern': r'-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----', 'severity': 'critical'},
            ],
            'tokens': [
                {'pattern': r'token\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})', 'severity': 'high'},
                {'pattern': r'bearer\s+([a-zA-Z0-9_-]{20,})', 'severity': 'high'},
            ],
            'database_credentials': [
                {'pattern': r'database_url\s*[:=]\s*["\']?([^"\']+)', 'severity': 'high'},
                {'pattern': r'db_password\s*[:=]\s*["\']?([^"\']+)', 'severity': 'high'},
                {'pattern': r'mongodb_uri\s*[:=]\s*["\']?([^"\']+)', 'severity': 'high'},
            ],
            'insecure_protocols': [
                {'pattern': r'http://', 'severity': 'medium'},
                {'pattern': r'ftp://', 'severity': 'medium'},
                {'pattern': r'telnet://', 'severity': 'high'},
            ]
        }

    def _initialize_validation_rules(self) -> List[Dict[str, Any]]:
        """Initialize validation rules"""
        return [
            # Environment file rules
            {
                'config_type': ConfigType.ENV,
                'rules': [
                    {
                        'name': 'no_empty_values',
                        'description': 'Check for empty values in environment files',
                        'validator': self._validate_no_empty_values,
                        'severity': 'warning'
                    },
                    {
                        'name': 'proper_format',
                        'description': 'Check proper KEY=VALUE format',
                        'validator': self._validate_env_format,
                        'severity': 'error'
                    }
                ]
            },
            # YAML rules
            {
                'config_type': ConfigType.YAML,
                'rules': [
                    {
                        'name': 'yaml_syntax',
                        'description': 'Validate YAML syntax',
                        'validator': self._validate_yaml_syntax,
                        'severity': 'error'
                    },
                    {
                        'name': 'no_duplicate_keys',
                        'description': 'Check for duplicate keys in YAML',
                        'validator': self._validate_no_duplicate_keys,
                        'severity': 'error'
                    }
                ]
            },
            # JSON rules
            {
                'config_type': ConfigType.JSON,
                'rules': [
                    {
                        'name': 'json_syntax',
                        'description': 'Validate JSON syntax',
                        'validator': self._validate_json_syntax,
                        'severity': 'error'
                    }
                ]
            },
            # Docker Compose rules
            {
                'config_type': ConfigType.DOCKER_COMPOSE,
                'rules': [
                    {
                        'name': 'docker_compose_syntax',
                        'description': 'Validate Docker Compose syntax',
                        'validator': self._validate_docker_compose_syntax,
                        'severity': 'error'
                    },
                    {
                        'name': 'no_hardcoded_secrets',
                        'description': 'Check for hardcoded secrets in Docker Compose',
                        'validator': self._validate_no_hardcoded_secrets,
                        'severity': 'high'
                    }
                ]
            }
        ]

    async def validate_config(
        self,
        config_data: str,
        config_file: ConfigFile,
        server: Optional[ServerDefinition] = None,
        custom_rules: Optional[List[ValidationRule]] = None
    ) -> ValidationResult:
        """
        Validate configuration data.

        Args:
            config_data: Configuration file content
            config_file: Configuration file definition
            server: Server context (optional)
            custom_rules: Additional validation rules (optional)

        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(valid=True)

        try:
            logger.debug(f"Validating configuration: {config_file.path}")

            # Syntax validation based on file type
            await self._validate_syntax(config_data, config_file.type, result)

            # Apply built-in validation rules
            await self._apply_validation_rules(config_data, config_file, result)

            # Apply custom validation rules
            if custom_rules:
                await self._apply_custom_rules(config_data, custom_rules, result)

            # Security validation
            if self.enable_security_validation:
                await self._validate_security(config_data, config_file, result)

            # Context-specific validation
            if server:
                await self._validate_server_context(config_data, config_file, server, result)

            # File-specific validation commands
            if config_file.validation_commands:
                await self._validate_with_commands(config_data, config_file.validation_commands, result)

            logger.info(f"Validation completed for {config_file.path}: {'PASS' if result.valid else 'FAIL'}")

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            result.add_error(f"Validation process failed: {str(e)}")

        return result

    async def _validate_syntax(self, config_data: str, config_type: ConfigType, result: ValidationResult):
        """Validate configuration syntax based on type"""
        try:
            if config_type == ConfigType.YAML:
                yaml.safe_load(config_data)
            elif config_type == ConfigType.JSON:
                json.loads(config_data)
            elif config_type == ConfigType.TOML:
                toml.loads(config_data)
            elif config_type == ConfigType.INI:
                config = configparser.ConfigParser()
                config.read_string(config_data)
            elif config_type == ConfigType.ENV:
                self._validate_env_syntax(config_data)
            elif config_type == ConfigType.DOCKER_COMPOSE:
                # Docker Compose files are YAML
                yaml.safe_load(config_data)

        except yaml.YAMLError as e:
            result.add_error(f"YAML syntax error: {str(e)}")
        except json.JSONDecodeError as e:
            result.add_error(f"JSON syntax error: {str(e)}")
        except toml.TomlDecodeError as e:
            result.add_error(f"TOML syntax error: {str(e)}")
        except configparser.Error as e:
            result.add_error(f"INI syntax error: {str(e)}")
        except Exception as e:
            result.add_error(f"Syntax validation error: {str(e)}")

    def _validate_env_syntax(self, config_data: str):
        """Validate environment file syntax"""
        lines = config_data.split('\n')
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' not in line:
                raise ValueError(f"Invalid environment variable format at line {line_num}: {line}")

    async def _apply_validation_rules(self, config_data: str, config_file: ConfigFile, result: ValidationResult):
        """Apply built-in validation rules"""
        for rule_set in self.validation_rules:
            if rule_set['config_type'] == config_file.type:
                for rule in rule_set['rules']:
                    try:
                        await rule['validator'](config_data, result)
                    except Exception as e:
                        logger.error(f"Validation rule '{rule['name']}' failed: {e}")
                        result.add_error(f"Validation rule error: {str(e)}")

    async def _apply_custom_rules(self, config_data: str, custom_rules: List[ValidationRule], result: ValidationResult):
        """Apply custom validation rules"""
        for rule in custom_rules:
            try:
                if rule.rule_type == "regex":
                    await self._apply_regex_rule(config_data, rule, result)
                elif rule.rule_type == "command":
                    await self._apply_command_rule(config_data, rule, result)
                elif rule.rule_type == "custom":
                    await self._apply_custom_script_rule(config_data, rule, result)
            except Exception as e:
                logger.error(f"Custom validation rule '{rule.name}' failed: {e}")
                result.add_error(f"Custom rule error: {str(e)}")

    async def _apply_regex_rule(self, config_data: str, rule: ValidationRule, result: ValidationResult):
        """Apply regex-based validation rule"""
        if rule.regex_pattern:
            pattern = re.compile(rule.regex_pattern, re.MULTILINE | re.IGNORECASE)
            matches = pattern.findall(config_data)

            if matches and rule.required:
                if rule.severity == "error":
                    for match in matches:
                        result.add_error(f"Rule '{rule.name}' violation: {match}")
                elif rule.severity == "warning":
                    for match in matches:
                        result.add_warning(f"Rule '{rule.name}' warning: {match}")
                else:
                    for match in matches:
                        result.add_suggestion(f"Rule '{rule.name}' suggestion: {match}")

    async def _apply_command_rule(self, config_data: str, rule: ValidationRule, result: ValidationResult):
        """Apply command-based validation rule"""
        if rule.validation_command:
            try:
                # Create temporary file with config data
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                    temp_file.write(config_data)
                    temp_path = temp_file.name

                try:
                    # Replace placeholder with temp file path
                    command = rule.validation_command.replace('{file}', temp_path)

                    # Execute validation command
                    process = await asyncio.create_subprocess_shell(
                        command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )

                    stdout, stderr = await process.communicate()

                    if process.returncode != 0:
                        error_msg = stderr.decode('utf-8').strip()
                        if error_msg:
                            result.add_error(f"Rule '{rule.name}': {error_msg}")
                        else:
                            result.add_error(f"Rule '{rule.name}' validation failed")
                    elif stdout:
                        output = stdout.decode('utf-8').strip()
                        if output:
                            result.add_suggestion(f"Rule '{rule.name}': {output}")

                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

            except Exception as e:
                result.add_error(f"Command validation failed for rule '{rule.name}': {str(e)}")

    async def _apply_custom_script_rule(self, config_data: str, rule: ValidationRule, result: ValidationResult):
        """Apply custom script validation rule"""
        if rule.validation_script:
            try:
                # Execute custom script (could be Python code, shell script, etc.)
                # This is a simplified implementation - in practice, you'd want
                # more sophisticated script execution with proper sandboxing

                if rule.validation_script.startswith('python:'):
                    # Simple Python script execution
                    script_code = rule.validation_script[7:]  # Remove 'python:' prefix
                    # Create a safe execution environment
                    exec_globals = {'config_data': config_data, 'result': result}
                    exec(script_code, exec_globals)

            except Exception as e:
                result.add_error(f"Custom script validation failed for rule '{rule.name}': {str(e)}")

    async def _validate_security(self, config_data: str, config_file: ConfigFile, result: ValidationResult):
        """Validate configuration for security issues"""
        lines = config_data.split('\n')

        for category, patterns in self.security_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                severity = pattern_info['severity']

                for line_num, line in enumerate(lines, 1):
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        # Skip if it's commented out
                        if line.strip().startswith('#'):
                            continue

                        security_message = f"{category.replace('_', ' ').title()} detected at line {line_num}"

                        if severity == 'critical':
                            result.add_security_issue(f"CRITICAL: {security_message}")
                        elif severity == 'high':
                            result.add_security_issue(f"HIGH: {security_message}")
                        elif severity == 'medium':
                            result.add_warning(f"Security: {security_message}")
                        else:
                            result.add_suggestion(f"Security: {security_message}")

    async def _validate_server_context(
        self,
        config_data: str,
        config_file: ConfigFile,
        server: ServerDefinition,
        result: ValidationResult
    ):
        """Validate configuration in server context"""
        # Example: Validate that database URLs use correct hostnames
        if server.hostname:
            db_url_pattern = r'(?:database_url|db_host|redis_host|mongo_host)\s*[:=]\s*["\']?([^"\']+)'
            matches = re.finditer(db_url_pattern, config_data, re.IGNORECASE)

            for match in matches:
                host = match.group(1)
                if not (host == 'localhost' or host == server.hostname or host.startswith('127.') or host.startswith('10.') or host.startswith('192.168.')):
                    result.add_warning(f"Database host '{host}' may not be accessible from server '{server.name}'")

    async def _validate_with_commands(self, config_data: str, validation_commands: List[str], result: ValidationResult):
        """Validate configuration using external commands"""
        for command in validation_commands:
            try:
                # Create temporary file with config data
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                    temp_file.write(config_data)
                    temp_path = temp_file.name

                try:
                    # Execute validation command
                    process = await asyncio.create_subprocess_shell(
                        command.format(file=temp_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )

                    stdout, stderr = await process.communicate()

                    if process.returncode != 0:
                        error_msg = stderr.decode('utf-8').strip()
                        if error_msg:
                            result.add_error(f"Validation command failed: {error_msg}")
                        else:
                            result.add_error("Configuration validation failed")
                    elif stdout:
                        output = stdout.decode('utf-8').strip()
                        if output:
                            result.add_suggestion(f"Validation output: {output}")

                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

            except Exception as e:
                result.add_error(f"Validation command execution failed: {str(e)}")

    # Built-in validation rule implementations
    async def _validate_no_empty_values(self, config_data: str, result: ValidationResult):
        """Validate environment files have no empty values"""
        lines = config_data.split('\n')
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                if not value.strip():
                    result.add_warning(f"Empty value for key '{key.strip()}' at line {line_num}")

    async def _validate_env_format(self, config_data: str, result: ValidationResult):
        """Validate proper environment file format"""
        lines = config_data.split('\n')
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' not in line:
                    result.add_error(f"Invalid format at line {line_num}: {line}")
                elif line.count('=') > 1:
                    # Check for unescaped quotes
                    if not re.match(r'^[^=]*="[^"]*"$', line):
                        result.add_error(f"Multiple '=' characters at line {line_num}: {line}")

    async def _validate_yaml_syntax(self, config_data: str, result: ValidationResult):
        """Validate YAML syntax"""
        try:
            yaml.safe_load(config_data)
        except yaml.YAMLError as e:
            result.add_error(f"YAML syntax error: {str(e)}")

    async def _validate_no_duplicate_keys(self, config_data: str, result: ValidationResult):
        """Check for duplicate keys in YAML"""
        try:
            # Parse YAML while tracking duplicate keys
            class DuplicateKeyLoader(yaml.SafeLoader):
                def construct_mapping(self, node, deep=False):
                    mapping = {}
                    for key_node, value_node in node.value:
                        key = self.construct_object(key_node, deep=deep)
                        if key in mapping:
                            raise yaml.YAMLError(f"Duplicate key: {key}")
                        mapping[key] = self.construct_object(value_node, deep=deep)
                    return mapping

            yaml.load(config_data, DuplicateKeyLoader)
        except yaml.YAMLError as e:
            if "Duplicate key" in str(e):
                result.add_error(str(e))

    async def _validate_json_syntax(self, config_data: str, result: ValidationResult):
        """Validate JSON syntax"""
        try:
            json.loads(config_data)
        except json.JSONDecodeError as e:
            result.add_error(f"JSON syntax error: {str(e)}")

    async def _validate_docker_compose_syntax(self, config_data: str, result: ValidationResult):
        """Validate Docker Compose syntax"""
        try:
            compose_data = yaml.safe_load(config_data)

            # Basic Docker Compose structure validation
            if not isinstance(compose_data, dict):
                result.add_error("Docker Compose file must be a dictionary/YAML object")
                return

            # Check required keys
            if 'services' not in compose_data and not compose_data:
                result.add_warning("No services defined in Docker Compose file")

            # Validate services structure
            if 'services' in compose_data:
                services = compose_data['services']
                if not isinstance(services, dict):
                    result.add_error("'services' must be a dictionary")
                else:
                    for service_name, service_config in services.items():
                        if not isinstance(service_config, dict):
                            result.add_error(f"Service '{service_name}' configuration must be a dictionary")

        except yaml.YAMLError as e:
            result.add_error(f"Docker Compose syntax error: {str(e)}")

    async def _validate_no_hardcoded_secrets(self, config_data: str, result: ValidationResult):
        """Check for hardcoded secrets in Docker Compose"""
        # Look for hardcoded passwords and secrets
        secret_patterns = [
            r'password:\s*["\']?([^"\']+)["\']?',
            r'MYSQL_PASSWORD:\s*["\']?([^"\']+)["\']?',
            r'POSTGRES_PASSWORD:\s*["\']?([^"\']+)["\']?',
            r'REDIS_PASSWORD:\s*["\']?([^"\']+)["\']?',
        ]

        lines = config_data.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in secret_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    secret_value = match.group(1)
                    if secret_value and not secret_value.startswith('${'):
                        result.add_security_issue(f"Hardcoded secret in Docker Compose at line {line_num}")


# Global validator instance
_config_validator: Optional[ConfigurationValidator] = None


def get_config_validator() -> ConfigurationValidator:
    """Get the global configuration validator"""
    global _config_validator
    if _config_validator is None:
        _config_validator = ConfigurationValidator()
    return _config_validator


def initialize_config_validator(enable_security_validation: bool = True) -> ConfigurationValidator:
    """Initialize the global configuration validator"""
    global _config_validator
    _config_validator = ConfigurationValidator(enable_security_validation)
    return _config_validator


# Import asyncio for async operations
import asyncio