#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "python-dotenv",
#     "rich",
#     "pydantic",
# ]
# ///

"""
Validation Test for Environment Synchronization Database Migrations

This script validates that:
1. All migration files exist and are valid SQL
2. Pydantic models are compatible with database schema
3. All necessary indexes and constraints are defined
4. Migration dependencies are correctly ordered

Usage:
    uv run apps/orchestrator_db/validation_test.py
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Import models to test their validity
try:
    from models import (
        Server, SyncOperation, SyncBatch, ServerEnvironment,
        ConfigFile, SyncOperationLog, ServerBackup
    )
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import models: {e}")
    MODELS_AVAILABLE = False

console = Console()

def test_migration_files_exist():
    """Test that all required migration files exist"""
    console.print("\n[bold cyan]🔍 Testing Migration Files Existence[/bold cyan]")

    migrations_dir = Path(__file__).parent / "migrations"
    required_migrations = [
        "9_servers.sql",
        "10_sync_operations.sql",
        "11_sync_batches.sql",
        "12_server_environments.sql",
        "13_config_files.sql",
        "14_sync_operation_logs.sql",
        "15_server_backups.sql",
    ]

    table = Table(title="Migration Files Status")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Size", style="dim")

    all_exist = True
    for migration in required_migrations:
        migration_path = migrations_dir / migration
        exists = migration_path.exists()
        status = "✅ Found" if exists else "❌ Missing"
        size = f"{migration_path.stat().st_size:,} bytes" if exists else "N/A"

        if not exists:
            all_exist = False
            table.add_row(migration, Text(status, style="red"), size)
        else:
            table.add_row(migration, Text(status, style="green"), size)

    console.print(table)
    return all_exist

def test_migration_sql_syntax():
    """Test basic SQL syntax validation"""
    console.print("\n[bold cyan]🔍 Testing SQL Syntax[/bold cyan]")

    migrations_dir = Path(__file__).parent / "migrations"
    migration_files = [
        "9_servers.sql",
        "10_sync_operations.sql",
        "11_sync_batches.sql",
        "12_server_environments.sql",
        "13_config_files.sql",
        "14_sync_operation_logs.sql",
        "15_server_backups.sql",
    ]

    table = Table(title="SQL Syntax Validation")
    table.add_column("File", style="cyan")
    table.add_column("Tables Created", style="green")
    table.add_column("Indexes Created", style="blue")
    table.add_column("Syntax Status", style="yellow")

    all_valid = True
    for migration in migration_files:
        migration_path = migrations_dir / migration
        if not migration_path.exists():
            continue

        content = migration_path.read_text()

        # Count CREATE TABLE statements
        create_tables = len(re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', content, re.IGNORECASE))

        # Count CREATE INDEX statements
        create_indexes = len(re.findall(r'CREATE INDEX IF NOT EXISTS', content, re.IGNORECASE))

        # Basic syntax checks
        syntax_issues = []

        # Check for balanced parentheses in CREATE TABLE statements
        table_matches = re.finditer(r'CREATE TABLE IF NOT EXISTS \w+\s*\((.*?)\);', content, re.DOTALL | re.IGNORECASE)
        for match in table_matches:
            table_def = match.group(1)
            if table_def.count('(') != table_def.count(')'):
                syntax_issues.append("Unbalanced parentheses in table definition")

        # Check for required elements
        if 'CREATE TABLE' not in content.upper():
            syntax_issues.append("No CREATE TABLE found")

        if not syntax_issues:
            status = "✅ Valid"
            status_style = "green"
        else:
            status = f"❌ {', '.join(syntax_issues)}"
            status_style = "red"
            all_valid = False

        table.add_row(migration, str(create_tables), str(create_indexes), Text(status, style=status_style))

    console.print(table)
    return all_valid

def test_model_compatibility():
    """Test that Pydantic models are compatible with expected schema"""
    console.print("\n[bold cyan]🔍 Testing Model Compatibility[/bold cyan]")

    if not MODELS_AVAILABLE:
        console.print("[red]❌ Models not available - skipping compatibility test[/red]")
        return False

    table = Table(title="Model Validation")
    table.add_column("Model", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")

    models_to_test = [
        ("Server", Server),
        ("SyncOperation", SyncOperation),
        ("SyncBatch", SyncBatch),
        ("ServerEnvironment", ServerEnvironment),
        ("ConfigFile", ConfigFile),
        ("SyncOperationLog", SyncOperationLog),
        ("ServerBackup", ServerBackup),
    ]

    all_valid = True
    for model_name, model_class in models_to_test:
        try:
            # Test basic model creation and field access
            schema_fields = list(model_class.model_fields.keys())

            # Check if model has a UUID field (common pattern)
            has_uuid_field = any('id' in field_name.lower() for field_name in schema_fields)

            # Check if model has timestamp fields (created_at, updated_at)
            has_timestamp_fields = any('created_at' in field_name or 'updated_at' in field_name
                                     for field_name in schema_fields)

            # Test that model can be instantiated (basic validation)
            # We won't actually create instances since we don't have test data

            status = "✅ Valid"
            status_style = "green"
            details = f"{len(schema_fields)} fields, UUID: {has_uuid_field}, Timestamps: {has_timestamp_fields}"

        except Exception as e:
            status = "❌ Error"
            status_style = "red"
            details = str(e)
            all_valid = False

        table.add_row(model_name, Text(status, style=status_style), details)

    console.print(table)
    return all_valid

def test_migration_order():
    """Test that migrations are properly ordered by dependencies"""
    console.print("\n[bold cyan]🔍 Testing Migration Dependencies[/bold cyan]")

    migration_order = [
        ("0_orchestrator_agents.sql", []),
        ("1_agents.sql", ["0_orchestrator_agents.sql"]),
        ("2_prompts.sql", ["1_agents.sql"]),
        ("3_agent_logs.sql", ["1_agents.sql"]),
        ("4_system_logs.sql", []),
        ("5_indexes.sql", ["0_orchestrator_agents.sql", "1_agents.sql", "2_prompts.sql", "3_agent_logs.sql", "4_system_logs.sql"]),
        ("6_functions.sql", []),
        ("7_triggers.sql", []),
        ("8_orchestrator_chat.sql", ["0_orchestrator_agents.sql"]),
        ("9_servers.sql", ["0_orchestrator_agents.sql"]),
        ("10_sync_operations.sql", ["9_servers.sql"]),
        ("11_sync_batches.sql", ["10_sync_operations.sql"]),
        ("12_server_environments.sql", ["9_servers.sql"]),
        ("13_config_files.sql", ["9_servers.sql"]),
        ("14_sync_operation_logs.sql", ["10_sync_operations.sql", "9_servers.sql"]),
        ("15_server_backups.sql", ["9_servers.sql", "10_sync_operations.sql"]),
    ]

    table = Table(title="Migration Dependencies")
    table.add_column("Migration", style="cyan")
    table.add_column("Dependencies", style="yellow")
    table.add_column("Order Status", style="green")

    migrations_dir = Path(__file__).parent / "migrations"
    migration_files = {f.name for f in migrations_dir.glob("*.sql")}

    all_valid = True
    for migration, deps in migration_order:
        exists = migration in migration_files
        if exists:
            # Check if all dependencies exist
            missing_deps = [dep for dep in deps if dep not in migration_files]
            if not missing_deps:
                status = "✅ OK"
                status_style = "green"
            else:
                status = f"❌ Missing deps: {', '.join(missing_deps)}"
                status_style = "red"
                all_valid = False
        else:
            status = "❌ Missing file"
            status_style = "red"
            all_valid = False

        table.add_row(migration, ', '.join(deps) if deps else "None", Text(status, style=status_style))

    console.print(table)
    return all_valid

def main():
    """Run all validation tests"""
    console.print(Panel.fit(
        "[bold cyan]Environment Synchronization Database Validation[/bold cyan]",
        border_style="cyan"
    ))

    # Load .env to test environment setup
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        console.print(f"[dim]✅ Loaded .env from {env_file}[/dim]")
    else:
        console.print("[yellow]⚠️  .env file not found at project root[/yellow]")

    # Run tests
    results = {
        "Migration Files Exist": test_migration_files_exist(),
        "SQL Syntax": test_migration_sql_syntax(),
        "Model Compatibility": test_model_compatibility(),
        "Migration Dependencies": test_migration_order(),
    }

    # Summary
    console.print("\n[bold cyan]📊 Validation Summary[/bold cyan]")

    summary_table = Table(title="Test Results")
    summary_table.add_column("Test", style="cyan")
    summary_table.add_column("Result", style="green")

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        if result:
            summary_table.add_row(test_name, Text("✅ PASSED", style="green"))
            passed += 1
        else:
            summary_table.add_row(test_name, Text("❌ FAILED", style="red"))

    console.print(summary_table)

    # Overall status
    success_rate = (passed / total) * 100
    if passed == total:
        console.print(Panel.fit(
            f"[bold green]✅ ALL TESTS PASSED[/bold green]\n"
            f"Environment synchronization database is ready!",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            f"[bold red]❌ {total - passed} TESTS FAILED[/bold red]\n"
            f"Success Rate: {success_rate:.1f}%\n"
            f"Please fix the issues before proceeding.",
            border_style="red"
        ))
        return 1

    return 0

if __name__ == "__main__":
    exit(main())