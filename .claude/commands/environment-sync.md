# Environment Synchronization Command

You are creating a comprehensive environment synchronization slash command for managing and synchronizing Claude Code environments across a distributed server network. This command handles environment file management, configuration validation, dependency synchronization, and cross-server deployment.

## Workflow Overview

The environment sync process consists of these major phases:

### Phase 1: Discovery and Analysis
- Scan current directory for environment files (.env, .env.*, package.json, requirements.txt, pyproject.toml, etc.)
- Identify target servers and their current environment state
- Analyze dependencies and configuration conflicts
- Generate synchronization plan with conflict resolution strategies

### Phase 2: Environment Validation
- Validate environment file syntax and structure
- Check for missing required variables and secrets
- Verify dependency compatibility across servers
- Identify security vulnerabilities in environment configurations

### Phase 3: Synchronization Execution
- Create standardized environment templates
- Deploy environment files to target servers
- Synchronize package dependencies (npm, uv, pip, etc.)
- Update server configurations with proper permissions

### Phase 4: Verification and Monitoring
- Test environment connectivity and functionality
- Validate service startup and health checks
- Monitor synchronization status across all servers
- Generate comprehensive sync report

## Command Implementation

### 1. Environment Discovery Module
Create functions to:
- Recursively scan for environment-related files
- Parse and categorize different environment file types
- Extract dependency lists and configuration variables
- Identify server-specific vs. shared configurations

### 2. Server Connectivity Module
Implement:
- SSH connection testing to all target servers
- Environment state assessment on remote servers
- Network topology mapping for distributed sync
- Fallback strategies for connectivity issues

### 3. Conflict Resolution Engine
Build logic to:
- Detect conflicting environment variables
- Merge configuration files intelligently
- Handle version incompatibilities
- Preserve server-specific customizations

### 4. Deployment Automation
Create:
- Secure file transfer mechanisms
- Atomic deployment strategies
- Rollback capabilities for failed syncs
- Service restart orchestration

### 5. Validation Framework
Implement:
- Environment variable validation rules
- Dependency compatibility checks
- Service health verification
- Performance baseline testing

### 6. Monitoring and Reporting
Add:
- Real-time sync progress tracking
- Success/failure reporting by server
- Performance impact analysis
- Automated alerts for sync failures

## Required Tools and Permissions

The command needs access to:
- **Read**: Environment files, configuration files, dependency manifests
- **Write**: Create/modify environment files and sync reports
- **Bash**: SSH operations, file transfers, service management
- **Grep**: Search environment files and configurations
- **Glob**: Find environment-related files by pattern
- **WebFetch**: Download dependency packages if needed
- **Edit**: Modify configuration files during sync

## Output Format

The command should generate:

### Sync Plan Report
```
Environment Synchronization Plan
================================

Discovery Summary:
- Environment files found: 15
- Target servers: 4 (primary, backup, dev, staging)
- Dependencies to sync: 237
- Potential conflicts: 3

Conflicts Detected:
1. DATABASE_URL differs between servers
   - Recommendation: Use server-specific override files
2. Node version mismatch (v18 vs v20)
   - Recommendation: Standardize to v20 across all servers

Execution Plan:
1. Create base .env.template file
2. Deploy server-specific .env.{server} files
3. Sync npm packages via npm ci
4. Restart services in dependency order
5. Validate health endpoints

Estimated time: 12 minutes
```

### Execution Report
```
Sync Execution Report
====================

Server: primary.example.com
Status: ✅ SUCCESS
Files synced: 8/8
Services restarted: 3/3
Health checks: PASS
Duration: 3m 24s

Server: dev.example.com
Status: ✅ SUCCESS
Files synced: 7/7
Services restarted: 2/2
Health checks: PASS
Duration: 2m 18s

Server: staging.example.com
Status: ⚠️ PARTIAL
Files synced: 6/8 (2 conflicts)
Services restarted: 2/3 (1 failed)
Health checks: 2 PASS, 1 FAIL
Duration: 4m 12s

Overall Status: ⚠️ SUCCESSFUL WITH ISSUES
Recommendations: Review staging server conflicts
```

## Error Handling

Implement robust error handling for:
- Network connectivity failures
- Permission denied errors
- Invalid environment file syntax
- Dependency installation failures
- Service startup failures
- Configuration conflicts

## Security Considerations

- Encrypt sensitive environment variables during transfer
- Validate all environment values against security policies
- Never log or display secret values
- Use SSH key authentication for server access
- Implement proper file permissions (600 for .env files)

## Integration Points

The command should integrate with:
- LAVINMQ message queues for async sync operations
- Existing server monitoring systems
- Configuration management tools (Ansible, etc.)
- CI/CD pipelines for automated environment syncs
- Alerting systems for sync notifications

Now implement this comprehensive environment synchronization slash command following the established workflow patterns in your Multi-Agent Orchestration System.