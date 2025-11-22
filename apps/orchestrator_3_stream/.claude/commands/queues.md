# LAVINMQ Queue Management

Manage LAVINMQ message queues, worker agent coordination, and distributed task processing across your server network.

## Usage

```bash
/queues [action] [queue-name] [options]
```

## Actions

### Queue Management
- `status` - Show queue status and worker distribution
- `create` - Create new message queue
- `delete` - Delete message queue
- `purge` - Clear all messages from queue
- `info` - Detailed queue information

### Worker Agent Management
- `workers` - List worker agents and their queues
- `deploy` - Deploy worker agents to queues
- `scale` - Scale workers for specific queues
- `health` - Check worker agent health

### Monitoring and Diagnostics
- `monitor` - Real-time queue monitoring
- `metrics` - Queue performance metrics
- `diagnose` - Diagnose queue and worker issues
- `logs` - Queue operation logs

## Queue Management

### View Queue Status

```bash
# Show all queues
/queues status

# Show specific queue
/queues status myapp.workers.api

# Show queues with workers
/queues status --workers

# Show queue distribution across servers
/queues status --distribution
```

### Create and Configure Queues

```bash
# Create standard queue
/queues create myapp.workers.database

# Create priority queue
/queues create myapp.priority.high --priority=high --durable=true

# Create queue with TTL
/queues create myapp.temporary --ttl=3600 --auto-delete=true

# Create dead letter queue
/queues create myapp.dlq --dead-letter=myapp.workers
```

### Queue Configuration Options

- `--priority` - Set queue priority (high/medium/low)
- `--durable` - Make queue persistent across restarts
- `--ttl` - Message time-to-live in seconds
- `--auto-delete` - Delete queue when empty
- `--dead-letter` - Dead letter queue for failed messages
- `--max-length` - Maximum messages in queue
- `--max-priority` - Maximum priority value

### Delete and Purge Queues

```bash
# Delete queue (must be empty)
/queues delete myapp.temporary

# Purge all messages from queue
/queues purge myapp.workers.api

# Force delete with message cleanup
/queues delete myapp.old --force --purge=true
```

## Worker Agent Management

### Deploy Worker Agents

```bash
# Deploy workers to specific queue
/queues deploy myapp.workers.api --workers=8 --servers=mesh

# Deploy with auto-scaling
/queues deploy myapp.workers.database --workers=6 --auto-scale --min=3 --max=15

# Deploy across server categories
/queues deploy myapp.workers.security --workers=4 --servers=digitalocean --priority=high
```

### Worker Configuration

```bash
# Deploy with custom configuration
/queues deploy myapp.workers.api \
  --workers=10 \
  --servers=mesh01,mesh02,mesh03 \
  --concurrency=4 \
  --timeout=300 \
  --retry-delay=60 \
  --max-retries=3

# Deploy specialized workers
/queues deploy myapp.workers.integration \
  --workers=6 \
  --type=integration-specialist \
  --external-services=github,slack,jira \
  --rate-limit=100
```

### Scale Worker Agents

```bash
# Scale workers for specific queue
/queues scale myapp.workers.api 12

# Auto-scale based on queue depth
/queues scale myapp.workers.database 8 --auto-scale --queue-depth=50

# Scale across server categories
/queues scale myapp.workers.security 10 --servers=all --strategy=weighted
```

### Worker Health and Status

```bash
# Check worker health
/queues health

# Detailed worker status
/queues workers --status --verbose

# Worker performance metrics
/queues workers --metrics --performance

# Worker distribution by server
/queues workers --distribution --by-server
```

## Monitoring and Diagnostics

### Real-Time Monitoring

```bash
# Start real-time monitoring
/queues monitor --refresh=5

# Monitor specific queue
/queues monitor myapp.workers.api --refresh=2

# Monitor with alerts
/queues monitor --alerts --threshold=1000 --email=admin@example.com
```

### Queue Metrics

```bash
# Current queue metrics
/queues metrics

# Historical metrics
/queues metrics --period=1h --queue=myapp.workers.database

# Performance analytics
/queues metrics --performance --trends --period=24h

# Worker performance
/queues metrics --workers --throughput --latency
```

### Diagnostics

```bash
# Diagnose queue issues
/queues diagnose myapp.workers.api

# Full system diagnostics
/queues diagnose --all --connectivity --performance

# Worker connectivity test
/queues diagnose --workers --test-connections

# Queue depth analysis
/queues diagnose --queue-depth --trends --predictions
```

### Operation Logs

```bash
# Recent queue operations
/queues logs --tail=50

# Queue-specific logs
/queues logs myapp.workers.api --level=INFO

# Worker operation logs
/queues logs --workers --level=DEBUG

# Error logs only
/queues logs --level=ERROR --tail=100
```

## Queue Architecture

### Standard Queue Layout

```
Application Queues
├── app.main                    # Main application queue
├── app.workers.api            # API processing workers
├── app.workers.database       # Database operation workers
├── app.workers.security       # Security monitoring workers
├── app.workers.integration    # External integration workers
└── app.workers.general        # General purpose workers

Priority Queues
├── app.priority.high          # High priority tasks
├── app.priority.medium        # Medium priority tasks
└── app.priority.low           # Low priority tasks

Support Queues
├── app.dlq                    # Dead letter queue
├── app.retry                  # Retry queue for failed tasks
└── app.monitoring             # Monitoring and metrics queue
```

### Worker Agent Types

#### LAVINMQ Workers
```bash
# Standard message processing workers
/queues deploy app.workers.general --type=lavinmq-worker --workers=8
```

#### API Specialists
```bash
# API endpoint and service workers
/queues deploy app.workers.api --type=api-specialist --workers=6
```

#### Database Architects
```bash
# Database operation and migration workers
/queues deploy app.workers.database --type=database-architect --workers=4
```

#### Security Auditors
```bash
# Security monitoring and compliance workers
/queues deploy app.workers.security --type=security-auditor --workers=2
```

#### Integration Specialists
```bash
# External service integration workers
/queues deploy app.workers.integration --type=integration-specialist --workers=3
```

## Advanced Configuration

### Queue Federation

```bash
# Setup queue federation across servers
/queues create myapp.federated --federate --upstream=mesh01:5672

# Cross-datacenter queue replication
/queues create myapp.replicated --replicate --target=digitalocean:5672
```

### Cluster Configuration

```bash
# Setup queue clustering
/queues cluster --setup --nodes=mesh01,mesh02,mesh03

# Add node to cluster
/queues cluster --add-node=mesh04

# Cluster health check
/queues cluster --health --status
```

### High Availability

```bash
# Setup HA queue mirrors
/queues create myapp.ha --mirrored --mirrors=2

# Queue failover configuration
/queues create myapp.failover --failover --backup-server=mesh05
```

## Performance Optimization

### Queue Tuning

```bash
# Optimize for high throughput
/queues create app.high-throughput \
  --max-length=10000 \
  --max-priority=10 \
  --lazy-loading=true

# Optimize for low latency
/queues create app.low-latency \
  --immediate=true \
  --no-ack=false \
  --prefetch-count=1
```

### Worker Optimization

```bash
# Optimize worker performance
/queues deploy app.workers.optimized \
  --workers=12 \
  --concurrency=8 \
  --prefetch=10 \
  --batch-size=50 \
  --batch-timeout=1000
```

### Resource Management

```bash
# Set queue resource limits
/queues create app.limited \
  --max-memory=1GB \
  --max-disk=10GB \
  --message-ttl=3600

# Worker resource constraints
/queues deploy app.workers.constrained \
  --workers=6 \
  --memory-limit=512MB \
  --cpu-limit=2 \
  --io-limit=100MB/s
```

## Security and Access Control

### Authentication Setup

```bash
# Create queue user
/queues create-user app_worker --password=secure_password --permissions=read,write

# Set queue permissions
/queues set-permissions myapp.workers.api --user=app_worker --configure=read,write
```

### SSL/TLS Configuration

```bash
# Enable SSL for queue connections
/queues configure --ssl=true --cert-path=/etc/ssl/certs --require-client-cert=true

# Verify SSL configuration
/queues diagnose --ssl-test --verify-certificates
```

### Access Control Lists

```bash
# Set up queue ACLs
/queues acl myapp.workers.api --allow=192.168.2.0/24 --deny=0.0.0.0/0

# User-based access control
/queues acl --user=app_worker --queues=myapp.workers.* --permissions=consume,publish
```

## Integration Examples

### Multi-Application Setup

```bash
# Setup queues for multiple applications
/queues create app1.workers.api
/queues create app1.workers.database
/queues deploy app1.workers.api --workers=6 --servers=mesh01,mesh02
/queues deploy app1.workers.database --workers=4 --servers=mesh03

/queues create app2.workers.api
/queues create app2.workers.security
/queues deploy app2.workers.api --workers=8 --servers=digitalocean
/queues deploy app2.workers.security --workers=2 --servers=mesh04
```

### Microservices Architecture

```bash
# Service-specific queues
/queues create user.service.tasks
/queues create order.service.tasks
/queues create payment.service.tasks

# Deploy specialized workers
/queues deploy user.service.tasks --workers=4 --type=database-architect
/queues deploy order.service.tasks --workers=6 --type=api-specialist
/queues deploy payment.service.tasks --workers=3 --type=security-auditor
```

### Event-Driven Architecture

```bash
# Event queues
/queues create events.user.created
/queues create events.order.placed
/queues create events.payment.processed

# Event processing workers
/queues deploy events.user.created --workers=2 --type=integration-specialist
/queues deploy events.order.placed --workers=4 --type=api-specialist
/queues deploy events.payment.processed --workers=3 --type=security-auditor
```

## Troubleshooting

### Common Issues

1. **Queue Connection Failures**: Workers cannot connect to LAVINMQ broker
2. **Message Processing Delays**: Workers processing messages slowly
3. **Memory Leaks**: Queue or worker memory usage growing continuously
4. **Dead Letter Queue Overflow**: Too many failed messages
5. **Worker Starvation**: Workers not receiving messages

### Diagnostic Commands

```bash
# Connection test
/queues diagnose --connection-test --broker=lavinmq.example.com

# Performance analysis
/queues diagnose --performance --queue-depth --worker-latency

# Resource usage
/queues diagnose --resources --memory --cpu --disk

# Message flow analysis
/queues diagnose --message-flow --bottlenecks
```

### Recovery Procedures

```bash
# Clear stuck messages
/queues purge myapp.stuck --force

# Restart worker agents
/queues restart-workers myapp.workers.api

# Rebalance worker distribution
/queues rebalance --queue=myapp.workers.database --servers=all

# Emergency queue reset
/queues reset myapp.broken --recreate --redeploy-workers
```