# Deploy Application to Server Network

Deploy applications and Claude Code environments across your distributed server network with LAVINMQ worker agent orchestration and comprehensive deployment management. Supports both traditional application deployment and Claude Code environment deployment with full agent ecosystem management.

## Usage

```bash
# Traditional Application Deployment
/deploy [app-name] [servers] [branch] [options]

# Claude Code Environment Deployment
/deploy [app-name] [servers] [branch] --claude-code [claude-options]
```

## Parameters

- **app-name**: Name of the application or Claude Code environment to deploy (required)
- **servers**: Target server category or specific servers (default: mesh)
  - `mesh` - Local mesh servers (mesh01-mesh13)
  - `agenticoverlord` - Cloudflare tunnel servers
  - `digitalocean` - Production cloud servers
  - `all` - Complete server network
  - Comma-separated list: `mesh01,mesh02,mesh05`
- **branch**: Git branch to deploy (default: main)
- **options**: Additional deployment parameters
  - `--workers=N` - Number of LAVINMQ worker agents to deploy
  - `--queue=queue-name` - Specific LAVINMQ queue for worker agents
  - `--health-check` - Enable deployment health checks
  - `--rollback` - Enable automatic rollback on failure
  - `--env=environment` - Target environment (dev/staging/prod)

### Claude Code Environment Options

- **--claude-code**: Deploy Claude Code environment with agent ecosystem
- **--agents=agent-list**: Comma-separated list of agents to deploy (default: all)
- **--commands=command-list**: Comma-separated list of slash commands to deploy
- **--claude-version=version**: Claude Code version to deploy (default: latest)
- **--agent-config=config-file**: Custom agent configuration file path
- **--workspace=workspace-path**: Claude Code workspace directory
- **--orchestrator**: Deploy orchestrator system with agent management
- **--templates=template-list**: Agent templates to deploy and configure
- **--mcp-servers=server-list**: MCP servers to integrate with environment

## LAVINMQ Worker Agent Deployment

### Worker Agent Configuration

When deploying applications with worker agents, the system automatically:

1. **Queue Setup**: Creates LAVINMQ queues for each worker type
2. **Agent Deployment**: Deploys worker agents to specified servers
3. **Load Balancing**: Distributes workers across available servers
4. **Health Monitoring**: Sets up health checks for all workers
5. **Failover**: Configures automatic worker restart on failure

### Supported Worker Agent Types

- **lavinmq-worker**: Standard LAVINMQ message processing workers
- **api-specialist**: API endpoint and service workers
- **database-architect**: Database operation workers
- **security-auditor**: Security monitoring workers
- **integration-specialist**: External service integration workers

## Claude Code Environment Deployment

### Claude Code Agent Ecosystem

When deploying with `--claude-code`, the system creates a comprehensive Claude Code environment with distributed agent orchestration:

1. **Environment Setup**: Install Claude Code CLI and dependencies
2. **Agent Deployment**: Deploy specialized agents across server network
3. **Command Installation**: Install custom slash commands for orchestration
4. **Workspace Configuration**: Set up workspace and project structure
5. **MCP Integration**: Configure Model Context Protocol servers
6. **Orchestrator Setup**: Deploy multi-agent orchestration system

### Claude Code Environment Architecture

```
Claude Code Environment
├── .claude/
│   ├── agents/           # Deployed agents
│   │   ├── api-specialist.md
│   │   ├── database-architect.md
│   │   ├── deployment-specialist.md
│   │   └── orchestrator-agent.md
│   ├── commands/         # Custom slash commands
│   │   ├── deploy.md
│   │   ├── scale.md
│   │   ├── orchestrate.md
│   │   └── agents.md
│   └── config.yml        # Environment configuration
├── mcp-servers/          # MCP server configurations
├── workspaces/           # Agent workspaces
└── orchestrator/         # Multi-agent orchestration
    ├── database/         # Orchestrator database
    ├── websocket/        # Real-time communication
    └── monitoring/       # Agent performance monitoring
```

### Agent Deployment Patterns

#### Specialized Agent Deployment
```bash
# Deploy specific agents for different tasks
/deploy claude-env mesh main --claude-code --agents=api-specialist,database-architect,security-auditor

# Deploy with custom agent configurations
/deploy claude-env digitalocean main --claude-code --agent-config=./custom-agents.yml
```

#### Complete Agent Ecosystem
```bash
# Deploy full agent ecosystem with orchestrator
/deploy claude-env all main --claude-code --orchestrator --agents=all

# Deploy with specific agent templates
/deploy claude-env mesh main --claude-code --templates=web-development,api-testing,database-migration
```

### MCP Server Integration

#### MCP Server Deployment
```bash
# Deploy with specific MCP servers
/deploy claude-env mesh main --claude-code --mcp-servers=filesystem,web-search,database

# Deploy with custom MCP configurations
/deploy claude-env digitalocean main --claude-code --mcp-servers=custom-mcp-server --workspace=/projects
```

#### Supported MCP Servers
- **filesystem**: File system operations and management
- **web-search**: Web search and content retrieval
- **database**: Database query and management
- **webhook**: HTTP webhook handling and integration
- **lavinmq**: LAVINMQ message queue integration
- **monitoring**: System monitoring and metrics collection

### Custom Slash Command Deployment

#### Command Installation
```bash
# Deploy specific slash commands
/deploy claude-env mesh main --claude-code --commands=deploy,scale,orchestrate,agents

# Deploy all available commands
/deploy claude-env all main --claude-code --commands=all
```

#### Command Categories
- **Deployment Commands**: `/deploy`, `/scale`, `/status`
- **Orchestration Commands**: `/orchestrate`, `/agents`, `/queues`
- **Management Commands**: `/servers`, `/monitoring`, `/logs`
- **Development Commands**: `/test`, `/build`, `/debug`

### Workspace and Project Management

#### Workspace Configuration
```bash
# Deploy with workspace setup
/deploy claude-env mesh main --claude-code --workspace=/opt/projects --orchestrator

# Deploy with project templates
/deploy claude-env digitalocean main --claude-code --templates=enterprise,saas,microservices
```

#### Project Structure
```
/opt/projects/
├── claude-env/           # Main Claude Code environment
├── agent-workspaces/     # Individual agent workspaces
├── shared-workspaces/    # Collaborative workspaces
└── project-templates/    # Reusable project templates
```

### Multi-Agent Orchestration

#### Orchestrator Deployment
```bash
# Deploy with full orchestrator system
/deploy claude-env all main --claude-code --orchestrator --agents=all

# Deploy orchestrator with custom configuration
/deploy claude-env mesh main --claude-code --orchestrator --agent-config=./orchestrator-config.yml
```

#### Orchestrator Features
- **Agent Lifecycle Management**: Deploy, monitor, and scale agents
- **Task Distribution**: Intelligent task routing to specialized agents
- **Resource Management**: Optimize agent resource allocation
- **Performance Monitoring**: Real-time agent performance metrics
- **Health Management**: Agent health checks and auto-recovery

### Environment-Specific Deployment

#### Development Environment
```bash
# Deploy development-focused Claude Code environment
/deploy claude-dev mesh main --claude-code --agents=api-specialist,database-architect --commands=build,test,debug

# Include development tools and debugging agents
/deploy claude-dev mesh main --claude-code --templates=development --mcp-servers=filesystem,web-search
```

#### Production Environment
```bash
# Deploy production-ready Claude Code environment
/deploy claude-prod digitalocean main --claude-code --orchestrator --agents=all --health-check

# Include monitoring and security agents
/deploy claude-prod all main --claude-code --agents=security-auditor,monitoring-specialist --mcp-servers=monitoring
```

## Deployment Workflow

### Phase 1: Pre-Deployment Checks
- **Server Availability**: Verify target servers are accessible
- **Resource Assessment**: Check CPU, memory, and disk space
- **Dependency Validation**: Ensure required services are available
- **LAVINMQ Status**: Verify message queue connectivity
- **Git Validation**: Confirm branch exists and is deployable

### Phase 2: Application Deployment
- **Code Checkout**: Clone specified branch to deployment directory
- **Environment Setup**: Configure environment variables and secrets
- **Service Installation**: Install dependencies and system services
- **Database Migration**: Run database migrations if required
- **Asset Building**: Compile and build application assets

### Phase 3: Worker Agent Deployment
- **Queue Creation**: Set up LAVINMQ queues for worker communication
- **Agent Distribution**: Deploy worker agents across target servers
- **Configuration**: Configure worker agent connections and parameters
- **Load Balancer Setup**: Configure worker load distribution
- **Monitoring Setup**: Deploy monitoring and logging agents

### Phase 4: Claude Code Environment Deployment (when --claude-code specified)
- **Claude Code Installation**: Install Claude Code CLI and dependencies
- **Agent Deployment**: Deploy specified agents to target servers
- **Command Installation**: Install custom slash commands in .claude/commands/
- **MCP Server Setup**: Configure and start MCP servers
- **Workspace Creation**: Set up workspace directories and permissions
- **Orchestrator Setup**: Deploy multi-agent orchestration system
- **Environment Configuration**: Configure .claude/config.yml and settings

### Phase 5: Post-Deployment Validation
- **Application Health Checks**: Verify application and worker agent health
- **Claude Code Environment Validation**: Test agent deployment and functionality
- **Integration Testing**: Test critical functionality, APIs, and agent interactions
- **Performance Monitoring**: Begin collecting performance metrics for both app and agents
- **Rollback Preparation**: Prepare rollback configuration if needed

## Server Network Details

### Mesh Servers (Local High-Performance)
- **Range**: mesh01-mesh13 (192.168.2.201-213)
- **Characteristics**: High performance, low latency, local network
- **Best For**: Development, testing, high-throughput workloads
- **Worker Capacity**: 5-8 worker agents per server

### AgenticOverlord Servers (Cloudflare Tunnel)
- **Range**: aidev + mesh11-13.agenticoverlord.com
- **Characteristics**: Remote access, secure tunneling
- **Best For**: Staging, remote development, external access
- **Worker Capacity**: 3-5 worker agents per server

### DigitalOcean Servers (Production Cloud)
- **Range**: do-small + do-medium
- **Characteristics**: Professional hosting, high availability
- **Best For**: Production workloads, critical services
- **Worker Capacity**: 10-15 worker agents per server

## LAVINMQ Integration

### Message Queue Architecture

```
Application Server
├── Main Queue (app.main)
├── Worker Queues
│   ├── app.workers.api
│   ├── app.workers.database
│   ├── app.workers.security
│   └── app.workers.integration
├── Priority Queues
│   ├── app.priority.high
│   ├── app.priority.medium
│   └── app.priority.low
└── Monitoring Queues
    ├── app.monitoring.health
    ├── app.monitoring.metrics
    └── app.monitoring.logs
```

### Worker Agent Communication

- **AMQP Protocol**: Standard message queue communication
- **Message Routing**: Intelligent message routing based on content type
- **Load Balancing**: Automatic worker load distribution
- **Error Handling**: Dead letter queues for failed messages
- **Monitoring**: Real-time worker health and performance metrics

## Deployment Examples

### Basic Application Deployment
```bash
/deploy myapp mesh main
```

### Application with Worker Agents
```bash
/deploy myapp mesh01,mesh02,mesh03 develop --workers=12 --queue=myapp.workers
/deploy myapp-workers 12 mesh --queue=myapp.workers
```

### Production Deployment with Health Checks
```bash
/deploy critical-app digitalocean main --workers=20 --health-check --rollback --env=prod
```

### Multi-Environment Deployment
```bash
/deploy myapp all main --workers=8 --env=staging
/deploy myapp digitalocean main --workers=15 --env=prod --health-check
```

### Claude Code Environment Deployment
```bash
# Deploy basic Claude Code environment
/deploy claude-env mesh main --claude-code

# Deploy Claude Code with specific agents
/deploy claude-dev mesh main --claude-code --agents=api-specialist,database-architect --workspace=/opt/dev

# Deploy full Claude Code ecosystem with orchestrator
/deploy claude-prod all main --claude-code --orchestrator --agents=all --health-check --env=prod

# Deploy Claude Code with custom commands and MCP servers
/deploy claude-env digitalocean main --claude-code --commands=deploy,scale,orchestrate --mcp-servers=filesystem,database,lavinmq

# Deploy with agent templates for specific use cases
/deploy web-automation mesh main --claude-code --templates=web-development,testing --mcp-servers=web-search,playwright
```

## Deployment Configuration

### Environment Variables

```bash
# Application Configuration
APP_NAME=myapp
APP_VERSION=1.0.0
APP_ENV=production

# LAVINMQ Configuration
LAVINMQ_HOST=localhost
LAVINMQ_PORT=5672
LAVINMQ_USER=app_user
LAVINMQ_PASSWORD=secure_password
LAVINMQ_VHOST=myapp_vhost

# Worker Agent Configuration
WORKER_COUNT=12
WORKER_QUEUE=myapp.workers
WORKER_CONCURRENCY=4
WORKER_TIMEOUT=300

# Claude Code Environment Configuration
CLAUDE_CODE_VERSION=latest
CLAUDE_WORKSPACE=/opt/projects
CLAUDE_AGENT_CONFIG=/opt/claude-config/agents.yml
CLAUDE_ORCHESTRATOR_ENABLED=true
MCP_SERVERS=filesystem,database,lavinmq,web-search
CLAUDE_ENVIRONMENT=production
```

### Docker Deployment

```yaml
version: '3.8'
services:
  app:
    image: myapp:latest
    environment:
      - LAVINMQ_HOST=lavinmq
      - WORKER_COUNT=8
    depends_on:
      - lavinmq

  lavinmq-worker:
    image: lavinmq-worker:latest
    environment:
      - LAVINMQ_HOST=lavinmq
      - WORKER_QUEUE=myapp.workers
    deploy:
      replicas: 4

  lavinmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"

# Claude Code Environment Docker Deployment
  claude-code-environment:
    image: claude-code-environment:latest
    environment:
      - CLAUDE_WORKSPACE=/workspace
      - CLAUDE_ORCHESTRATOR_ENABLED=true
      - MCP_SERVERS=filesystem,database,lavinmq
      - LAVINMQ_HOST=lavinmq
    volumes:
      - ./workspace:/workspace
      - ./claude-config:/root/.claude
    depends_on:
      - lavinmq
    deploy:
      replicas: 2

  claude-orchestrator:
    image: claude-orchestrator:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/orchestrator
      - LAVINMQ_HOST=lavinmq
      - WEBSOCKET_PORT=8002
    depends_on:
      - postgres
      - lavinmq
    ports:
      - "8002:8002"

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=orchestrator
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Monitoring and Management

### Deployment Health Monitoring

- **Application Health**: HTTP endpoints, database connectivity
- **Worker Agent Health**: Queue connectivity, message processing rates
- **Resource Monitoring**: CPU, memory, disk, network usage
- **LAVINMQ Metrics**: Queue depths, message rates, consumer counts
- **Claude Code Environment Health**: Agent deployment status, command functionality
- **Orchestrator Health**: WebSocket connections, database operations, agent coordination
- **MCP Server Health**: Server connectivity, protocol communication, response times

### Management Commands

```bash
# Check deployment status
/status myapp --verbose

# Monitor worker agents
/queues status --queue=myapp.workers

# Scale workers after deployment
/scale myapp-workers 6 mesh

# Update worker configuration
/orchestrate update-workers myapp --queue=myapp.workers --workers=10

# Claude Code environment management
/agents status --environment=claude-env
/orchestrate status --claude-code
/queues status --mcp-servers
/servers mesh --claude-code-status
```

## Rollback and Recovery

### Automatic Rollback Triggers

- **Health Check Failures**: Application or worker agents unhealthy
- **High Error Rates**: >5% error rate sustained for 5 minutes
- **Performance Degradation**: Response times >2x baseline
- **Worker Agent Failures**: >50% workers unavailable
- **Claude Code Environment Failures**: Agent deployment failures, command malfunctions
- **Orchestrator Failures**: WebSocket connection drops, database errors
- **MCP Server Failures**: Server connectivity issues, protocol errors

### Manual Rollback

```bash
# Rollback to previous version
/deploy myapp mesh main --rollback --version=previous

# Emergency rollback (immediate)
/deploy myapp all main --rollback --emergency

# Claude Code environment rollback
/deploy claude-env mesh main --rollback --claude-code --restore-agents
/deploy claude-prod all main --rollback --claude-code --emergency --preserve-workspace
```

## Best Practices

### Deployment Strategy

1. **Blue-Green Deployment**: Maintain two production environments
2. **Canary Releases**: Gradual rollout to subset of servers
3. **Feature Flags**: Control feature availability without redeployment
4. **Database Migrations**: Run migrations before application deployment
5. **Health Checks**: Implement comprehensive health check endpoints

### Worker Agent Optimization

1. **Queue Partitioning**: Separate queues for different worker types
2. **Message Prioritization**: Use priority queues for critical tasks
3. **Worker Scaling**: Auto-scale workers based on queue depth
4. **Error Handling**: Implement dead letter queues and retry logic
5. **Monitoring**: Real-time metrics and alerting

### Security Considerations

1. **Network Isolation**: Separate networks for different environments
2. **Access Control**: Implement proper AMQP authentication
3. **Secret Management**: Use secure secret management systems
4. **SSL/TLS**: Encrypt all communication channels
5. **Audit Logging**: Log all deployment and configuration changes

### Claude Code Environment Best Practices

1. **Agent Specialization**: Deploy specific agents for different task types
2. **Workspace Organization**: Use organized workspace structures for different projects
3. **Command Management**: Version and manage custom slash commands carefully
4. **MCP Server Integration**: Choose appropriate MCP servers for your use case
5. **Orchestrator Configuration**: Properly configure agent coordination and task distribution
6. **Environment Isolation**: Separate Claude Code environments for different deployment stages
7. **Agent Resource Management**: Monitor and optimize agent resource usage
8. **Backup and Recovery**: Regularly backup agent configurations and workspace data

## Troubleshooting

### Common Issues

1. **Server Unreachable**: Check network connectivity and SSH access
2. **Resource Exhaustion**: Verify CPU, memory, and disk availability
3. **LAVINMQ Connection Issues**: Check message broker status and credentials
4. **Worker Agent Failures**: Review worker logs and queue configurations
5. **Health Check Failures**: Validate application endpoints and dependencies
6. **Claude Code Environment Issues**: Agent deployment failures, command malfunctions
7. **Orchestrator Connection Problems**: WebSocket failures, database connectivity issues
8. **MCP Server Failures**: Server startup issues, protocol communication errors
9. **Workspace Permission Issues**: Incorrect file permissions, workspace access problems
10. **Agent Configuration Errors**: Invalid agent definitions, missing dependencies

### Debug Commands

```bash
# Check server status
/servers mesh --monitoring=high

# Diagnose LAVINMQ issues
/queues status --diagnose

# Check worker agent health
/orchestrate status --workers-only

# Review deployment logs
/status myapp --logs=50

# Claude Code environment debugging
/agents status --environment=claude-env --verbose
/orchestrate status --claude-code --diagnostics
/queues status --mcp-servers --connection-test
/servers mesh --claude-code-status --resource-usage
```