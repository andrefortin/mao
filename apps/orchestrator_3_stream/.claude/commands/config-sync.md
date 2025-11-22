# Configuration Management for Distributed Server Networks

Comprehensive configuration synchronization and management for config.json and settings.json across distributed server networks with LAVINMQ orchestration and real-time validation.

## Usage

```bash
/config-sync [action] [target] [options]
```

## Actions

### **sync** - Synchronize configurations
Synchronize config files across servers with validation and rollback capabilities.

```bash
/config-sync sync [source] [target] [options]
```

**Parameters:**
- **source**: Source server or configuration directory (required)
  - `local` - Use current directory as source
  - `mesh01` - Specific server as source
  - `config-backups` - Use backup directory as source
- **target**: Target servers or server category (default: mesh)
  - `mesh` - All mesh servers (mesh01-mesh13)
  - `agenticoverlord` - Cloudflare tunnel servers
  - `digitalocean` - Production cloud servers
  - `all` - Complete server network
  - Comma-separated list: `mesh01,mesh02,mesh05`

**Options:**
- `--config-types=json,settings,yaml` - Configuration file types to sync
- `--validate-only` - Validate configurations without applying changes
- `--backup` - Create backup before synchronization
- `--force` - Force synchronization even if validation fails
- `--exclude=pattern` - Exclude files matching pattern
- `--dry-run` - Show what would be synchronized without making changes

### **validate** - Validate configuration files
Validate configuration files against schemas and best practices.

```bash
/config-sync validate [target] [options]
```

**Parameters:**
- **target**: Target to validate (default: current directory)
  - `local` - Validate local configurations
  - Server name or category for remote validation

**Options:**
- `--schema=schema.json` - Custom validation schema
- `--strict` - Enable strict validation mode
- `--report=json|table` - Output format for validation results
- `--fix` - Automatically fix common configuration issues

### **backup** - Create and manage configuration backups
Create backups of current configurations with versioning and compression.

```bash
/config-sync backup [target] [options]
```

**Parameters:**
- **target**: Target to backup (default: local)
- **options**:
  - `--name=backup-name` - Custom backup name
  - `--compress` - Compress backup files
  - `--remote` - Store backup on remote server
  - `--retention=days` - Backup retention period

### **restore** - Restore from configuration backups
Restore configurations from previous backups with validation.

```bash
/config-sync restore [backup-name] [target] [options]
```

**Parameters:**
- **backup-name**: Name or ID of backup to restore
- **target**: Target server(s) for restoration
- **options**:
  - `--validate` - Validate restored configurations
  - `--restart-services` - Restart affected services after restore
  - `--dry-run` - Show what would be restored

### **diff** - Compare configurations
Compare configuration files between servers or versions.

```bash
/config-sync diff [source1] [source2] [options]
```

**Parameters:**
- **source1**: First configuration source
- **source2**: Second configuration source
- **options**:
  - `--format=table|json|diff` - Output format
  - `--ignore-whitespace` - Ignore whitespace differences
  - `--context=lines` - Number of context lines in diff output

### **encrypt** - Encrypt configuration files
Encrypt sensitive configuration data with AES-256 encryption.

```bash
/config-sync encrypt [file] [options]
```

**Options:**
- `--key-file=key.pem` - Encryption key file
- `--output=encrypted.enc` - Output encrypted file
- `--backup` - Create backup before encryption

### **decrypt** - Decrypt configuration files
Decrypt previously encrypted configuration files.

```bash
/config-sync decrypt [file] [options]
```

**Options:**
- `--key-file=key.pem` - Decryption key file
- `--output=config.json` - Output decrypted file
- `--validate` - Validate decrypted configuration

## Configuration File Types

### **config.json** - Main application configuration
```json
{
  "application": {
    "name": "myapp",
    "version": "1.0.0",
    "environment": "production",
    "debug": false
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 4
  },
  "database": {
    "type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "name": "myapp_prod"
  },
  "lavinmq": {
    "host": "localhost",
    "port": 5672,
    "vhost": "myapp",
    "queues": ["main", "workers", "priority"]
  }
}
```

### **settings.json** - Environment-specific settings
```json
{
  "environment": "production",
  "logging": {
    "level": "info",
    "format": "json",
    "rotation": "daily"
  },
  "security": {
    "jwt_secret": "${JWT_SECRET}",
    "encryption_key": "${ENCRYPTION_KEY}",
    "ssl_required": true
  },
  "performance": {
    "cache_ttl": 3600,
    "max_connections": 1000,
    "timeout": 30
  },
  "monitoring": {
    "metrics_enabled": true,
    "health_check_interval": 60,
    "alert_webhook": "${ALERT_WEBHOOK}"
  }
}
```

## Distributed Server Network Integration

### **LAVINMQ Configuration Broadcasting**

The system uses LAVINMQ message queues for real-time configuration updates:

```
Configuration Management Queue (config.management)
├── config.sync.broadcast      - Broadcast configuration changes
├── config.validate.request    - Request configuration validation
├── config.backup.create       - Trigger backup creation
├── config.restore.execute     - Execute configuration restore
├── config.encrypt.request     - Request configuration encryption
└── config.monitor.alerts      - Configuration monitoring alerts
```

### **Server Network Topology**

#### **Mesh Servers (Local High-Performance)**
- **Range**: mesh01-mesh13 (192.168.2.201-213)
- **Config Storage**: `/opt/app/config/`
- **Backup Location**: `/opt/app/config/backups/`
- **Sync Method**: Real-time via LAVINMQ + rsync fallback

#### **AgenticOverlord Servers (Cloudflare Tunnel)**
- **Range**: aidev + mesh11-13.agenticoverlord.com
- **Config Storage**: `/home/user/app/config/`
- **Backup Location**: `/home/user/app/config/backups/`
- **Sync Method**: HTTPS API + periodic polling

#### **DigitalOcean Servers (Production Cloud)**
- **Range**: do-small + do-medium
- **Config Storage**: `/etc/myapp/config/`
- **Backup Location**: `/etc/myapp/config/backups/`
- **Sync Method**: SSH + encrypted transport

## Configuration Validation

### **JSON Schema Validation**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "application": {
      "type": "object",
      "properties": {
        "name": {"type": "string", "minLength": 1},
        "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
        "environment": {"enum": ["development", "staging", "production"]}
      },
      "required": ["name", "version", "environment"]
    },
    "server": {
      "type": "object",
      "properties": {
        "host": {"type": "string"},
        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
        "workers": {"type": "integer", "minimum": 1, "maximum": 32}
      },
      "required": ["host", "port"]
    }
  },
  "required": ["application", "server"]
}
```

### **Validation Rules**

1. **Structure Validation**: JSON schema validation
2. **Security Validation**: Check for exposed secrets, weak passwords
3. **Performance Validation**: Validate performance-related settings
4. **Compatibility Validation**: Check version compatibility
5. **Network Validation**: Validate network endpoints and ports

## Advanced Features

### **Configuration Templating**

Support for environment variable substitution and template rendering:

```json
{
  "database": {
    "host": "${DB_HOST:localhost}",
    "port": "${DB_PORT:5432}",
    "url": "postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
  },
  "feature_flags": {
    "new_ui": "${FEATURE_NEW_UI:false}",
    "beta_features": "${FEATURE_BETA:true}"
  }
}
```

### **Configuration Versioning**

```bash
# List configuration versions
/config-sync versions [target]

# Show version diff
/config-sync versions [target] --diff=v1.2.0..v1.3.0

# Rollback to specific version
/config-sync restore v1.2.0 [target] --validate
```

### **Configuration Monitoring**

Real-time monitoring of configuration changes:

```bash
# Start monitoring
/config-sync monitor [target] --alert-webhook=${WEBHOOK_URL}

# Show change history
/config-sync history [target] --since="2024-01-01"

# Generate configuration report
/config-sync report [target] --format=html --output=report.html
```

## Security and Encryption

### **Encryption Configuration**

```bash
# Generate encryption key
/config-sync generate-key --output=config-key.pem

# Encrypt sensitive configurations
/config-sync encrypt settings.json --key-file=config-key.pem

# Decrypt for use
/config-sync decrypt settings.enc --key-file=config-key.pem --output=settings.json
```

### **Access Control**

- **Role-based Access**: Different permissions for read/write/encrypt
- **Audit Logging**: Log all configuration changes with user attribution
- **Signature Validation**: Verify configuration authenticity
- **Secure Transport**: Encrypt all configuration transfers

## Integration Examples

### **Basic Synchronization**
```bash
# Sync local config to all mesh servers
/config-sync sync local mesh --backup --validate

# Sync between specific servers
/config-sync sync mesh01 mesh02,mesh03 --config-types=json,settings
```

### **Production Deployment with Config**
```bash
# Backup current production config
/config-sync backup digitalocean --name=pre-deploy-backup

# Validate new configuration
/config-sync validate local --strict

# Deploy to production
/config-sync sync local digitalocean --backup --restart-services
```

### **Configuration Recovery**
```bash
# List available backups
/config-sync backups --target=digitalocean

# Restore from backup
/config-sync restore pre-deploy-backup digitalocean --validate --restart-services
```

### **Environment Promotion**
```bash
# Promote staging config to production
/config-sync sync agenticoverlord digitalocean --validate --backup

# Compare environments before promotion
/config-sync diff agenticoverlord digitalocean --format=table
```

## Monitoring and Alerting

### **Configuration Health Checks**

```bash
# Check configuration consistency
/config-sync health-check --all-servers

# Monitor for drift
/config-sync monitor-drift --alert-threshold=5

# Validate configuration dependencies
/config-sync check-dependencies --target=production
```

### **Alert Integration**

```bash
# Set up Slack alerts for config changes
/config-sync monitor all --webhook=${SLACK_WEBHOOK} --alert-level=high

# Email notifications for validation failures
/config-sync validate all --email-alerts=admin@company.com
```

## Best Practices

### **Configuration Management**

1. **Version Control**: Store configurations in Git with proper tagging
2. **Environment Separation**: Separate configs for each environment
3. **Secret Management**: Never store secrets in configuration files
4. **Regular Backups**: Create automated backups before changes
5. **Validation**: Always validate configurations before deployment

### **Security Practices**

1. **Encryption**: Encrypt sensitive configuration data
2. **Access Control**: Implement proper authentication and authorization
3. **Audit Trail**: Log all configuration changes and access
4. **Secure Transport**: Use encrypted channels for configuration transfer
5. **Key Rotation**: Regularly rotate encryption keys

### **Performance Optimization**

1. **Incremental Sync**: Only synchronize changed configurations
2. **Compression**: Compress large configuration files during transfer
3. **Caching**: Cache frequently accessed configurations
4. **Parallel Operations**: Synchronize to multiple servers in parallel
5. **Validation Optimization**: Use incremental validation for large configs

## Troubleshooting

### **Common Issues**

1. **Sync Failures**: Check network connectivity and permissions
2. **Validation Errors**: Review schema requirements and data types
3. **Encryption Issues**: Verify key files and permissions
4. **Performance Issues**: Check file sizes and network bandwidth
5. **Service Failures**: Validate configuration syntax and dependencies

### **Debug Commands**

```bash
# Debug synchronization issues
/config-sync sync local mesh --dry-run --verbose

# Validate configuration syntax
/config-sync validate local --debug

# Test LAVINMQ connectivity
/config-sync test-queue --queue=config.management

# Check encryption setup
/config-sync test-encryption --key-file=config-key.pem
```

### **Recovery Procedures**

```bash
# Emergency configuration restore
/config-sync restore latest-backup all --force --restart-services

# Reset to known good state
/config-sync reset-to-defaults [target] --backup-current

# Repair corrupted configuration
/config-sync repair [target] --validate --backup
```