# Scale Applications, Worker Agents, and Claude Code Environments

Horizontally scale applications, LAVINMQ worker agents, and Claude Code environments across your distributed server network with intelligent load balancing, auto-scaling, and agent orchestration capabilities. Supports traditional application scaling as well as Claude Code environment scaling with agent management.

## Usage

```bash
# Traditional Application/Worker Scaling
/scale [app-name] [instances] [server-category] [options]

# Claude Code Environment Scaling
/scale [environment-name] [instances] [server-category] --claude-code [claude-options]
```

## Parameters

- **app-name**: Name of the application, worker agent pool, or Claude Code environment to scale (required)
- **instances**: Target number of instances, workers, or agent environments (required)
- **server-category**: Target server category for scaling (default: mesh)
  - `mesh` - Local mesh servers (high performance)
  - `agenticoverlord` - Cloudflare tunnel servers
  - `digitalocean` - Production cloud servers
  - `all` - Scale across all available servers
- **options**: Scaling configuration options
  - `--workers-only` - Scale only worker agents, not main application
  - `--queue=queue-name` - Scale specific LAVINMQ queue workers
  - `--auto-scale` - Enable auto-scaling based on metrics
  - `--min=N` - Minimum instances for auto-scaling
  - `--max=N` - Maximum instances for auto-scaling
  - `--cpu-threshold=X%` - CPU threshold for auto-scaling
  - `--memory-threshold=X%` - Memory threshold for auto-scaling
  - `--queue-depth=N` - Queue depth threshold for worker scaling
  - `--strategy=strategy` - Scaling strategy (round-robin, least-connections, weighted)

### Claude Code Environment Scaling Options

- **--claude-code**: Scale Claude Code environment with agent ecosystem
- **--agents=agent-list**: Comma-separated list of agents to scale (default: all)
- **--agent-type=type** - Scale specific agent types (api-specialist, database-architect, etc.)
- **--orchestrator** - Scale orchestrator instances for agent coordination
- **--workspaces=N** - Number of workspace environments to create
- **--mcp-servers=server-list** - Scale specific MCP servers
- **--workspace-size=size** - Workspace size configuration (small, medium, large)
- **--agent-memory=memory** - Memory allocation per agent (default: 2GB)
- **--concurrent-tasks=N** - Maximum concurrent tasks per agent environment

## LAVINMQ Worker Agent Scaling

### Worker Pool Management

The scaling system manages LAVINMQ worker agents through intelligent pool management:

1. **Dynamic Worker Allocation**: Automatically distribute workers across available servers
2. **Queue-Based Scaling**: Scale workers based on message queue depth and processing rates
3. **Load-Aware Distribution**: Place workers on servers with available resources
4. **Health Monitoring**: Continuously monitor worker health and performance
5. **Graceful Scaling**: Add/remove workers without message loss

### Scaling Strategies

#### Horizontal Application Scaling
```bash
# Scale application instances across servers
/scale myapp 6 mesh --strategy=least-connections

# Scale with auto-scaling enabled
/scale myapp 4 all --auto-scale --min=2 --max=10 --cpu-threshold=70%
```

#### Worker Agent Scaling
```bash
# Scale specific worker queue
/scale myapp-workers 12 mesh --queue=myapp.workers.api

# Scale workers with queue-depth auto-scaling
/scale myapp-workers 8 all --auto-scale --queue-depth=100 --min=4 --max=20
```

#### Hybrid Scaling
```bash
# Scale both application and workers
/scale myapp 4 mesh
/scale myapp-workers 16 mesh --queue=myapp.workers.database
```

## Claude Code Environment Scaling

### Agent Environment Scaling

Claude Code environment scaling manages distributed agent ecosystems with intelligent resource allocation and load balancing:

1. **Agent Instance Management**: Scale individual agent types across server network
2. **Workspace Scaling**: Create and manage multiple workspace environments
3. **Orchestrator Scaling**: Scale coordination layers for multi-agent systems
4. **MCP Server Scaling**: Scale protocol servers for enhanced capabilities
5. **Resource Optimization**: Intelligent allocation of CPU, memory, and storage

### Claude Code Scaling Architecture

```
Claude Code Environment Scaling
├── Agent Instances
│   ├── API Specialists: 6 instances (2 per mesh server)
│   ├── Database Architects: 4 instances (distributed)
│   ├── Security Auditors: 3 instances (high-security servers)
│   └── Integration Specialists: 5 instances (network edge)
├── Workspace Environments
│   ├── Development Workspaces: 10 environments
│   ├── Staging Workspaces: 5 environments
│   └── Production Workspaces: 3 environments
├── Orchestrator Layer
│   ├── Main Orchestrator: 3 instances (HA)
│   ├── Task Distributors: 6 instances
│   └── Monitoring Agents: 4 instances
└── MCP Server Infrastructure
    ├── File System Servers: 8 instances
    ├── Database Servers: 4 instances
    └── Web Search Servers: 6 instances
```

### Agent-Specific Scaling

#### Scale Individual Agent Types
```bash
# Scale specific agent types
/scale claude-env 8 mesh --claude-code --agent-type=api-specialist
/scale claude-env 6 digitalocean --claude-code --agent-type=database-architect

# Scale multiple agent types
/scale claude-env 12 all --claude-code --agents=api-specialist,database-architect,security-auditor

# Scale agents with custom memory allocation
/scale claude-env 4 mesh --claude-code --agent-type=integration-specialist --agent-memory=4GB
```

#### Agent Scaling Strategies
- **Task-Based Scaling**: Scale agents based on task queue depth
- **Performance-Based Scaling**: Scale based on agent response times and throughput
- **Resource-Based Scaling**: Scale based on CPU/memory utilization
- **Priority Scaling**: Prioritize critical agent types during resource constraints

### Orchestrator Scaling

#### Scale Multi-Agent Coordination
```bash
# Scale orchestrator for high-throughput scenarios
/scale claude-orchestrator 6 mesh --claude-code --orchestrator --concurrent-tasks=50

# Scale orchestrator across server network
/scale claude-orchestrator 9 all --claude-code --orchestrator --min=3 --max=15

# Scale orchestrator with auto-scaling
/scale claude-orchestrator 4 digitalocean --claude-code --orchestrator --auto-scale --cpu-threshold=70%
```

#### Orchestrator Components
- **Main Orchestrator**: Central coordination and task distribution
- **Agent Managers**: Individual agent lifecycle management
- **Load Balancers**: Task distribution across agent instances
- **Monitoring Agents**: Real-time performance and health monitoring

### Workspace Environment Scaling

#### Scale Development and Production Workspaces
```bash
# Scale workspace environments for teams
/scale claude-workspaces 15 mesh --claude-code --workspaces=15 --workspace-size=medium

# Scale workspace with different sizes
/scale claude-workspaces 8 digitalocean --claude-code --workspaces=8 --workspace-size=large

# Scale workspaces with auto-scaling based on usage
/scale claude-workspaces 10 all --claude-code --auto-scale --workspaces=10 --min=5 --max=25
```

#### Workspace Configurations
- **Small**: 2GB RAM, 2 CPU cores, 50GB storage (development/testing)
- **Medium**: 4GB RAM, 4 CPU cores, 100GB storage (staging/collaboration)
- **Large**: 8GB RAM, 8 CPU cores, 200GB storage (production/enterprise)

### MCP Server Scaling

#### Scale Protocol Servers for Enhanced Capabilities
```bash
# Scale specific MCP servers
/scale claude-env 12 mesh --claude-code --mcp-servers=filesystem,database

# Scale web search and content retrieval
/scale claude-env 8 digitalocean --claude-code --mcp-servers=web-search,content-fetch

# Scale all MCP servers with load balancing
/scale claude-env 16 all --claude-code --mcp-servers=all --strategy=least-connections
```

#### MCP Server Types
- **File System**: File operations, directory management, file processing
- **Database**: Database queries, schema management, data analysis
- **Web Search**: Content retrieval, research, competitive analysis
- **Webhook**: HTTP integrations, API callbacks, event processing
- **Monitoring**: System metrics, performance monitoring, alerting

### Advanced Claude Code Scaling

#### Auto-Scaling Based on Agent Metrics
```bash
# Enable comprehensive auto-scaling
/scale claude-env 10 all --claude-code --auto-scale --min=5 --max=30 \
  --cpu-threshold=75% --memory-threshold=80% --concurrent-tasks=25

# Task-based auto-scaling for agents
/scale claude-env 8 mesh --claude-code --auto-scale --agents=all \
  --queue-depth=20 --strategy=queue-aware

# Performance-based agent scaling
/scale claude-env 12 digitalocean --claude-code --auto-scale --agents=api-specialist \
  --response-time-threshold=2s --throughput-target=100tasks/min
```

#### Blue-Green Agent Scaling
```bash
# Scale green agent environment while blue serves traffic
/scale claude-env-green 8 mesh --claude-code --agents=all --workspace-size=large

# Switch traffic and scale down blue environment
/scale claude-env-blue 0 mesh --claude-code --preserve-workspaces
```

#### Canary Agent Deployment
```bash
# Deploy new agent versions to subset of environments
/scale claude-env 4 mesh --claude-code --agents=new-api-specialist --canary=25%

# Monitor and expand if healthy
/scale claude-env 8 mesh --claude-code --agents=new-api-specialist --canary=50%

# Full rollout
/scale claude-env 12 mesh --claude-code --agents=new-api-specialist
```

## Auto-Scaling Configuration

### Metrics-Based Auto-Scaling

Auto-scaling can be triggered by multiple metrics:

```bash
# CPU-based auto-scaling
/scale myapp 6 all --auto-scale --cpu-threshold=75% --min=3 --max=12

# Memory-based auto-scaling
/scale myapp 8 digitalocean --auto-scale --memory-threshold=80% --min=4 --max=16

# Queue-based auto-scaling for workers
/scale myapp-workers 10 mesh --auto-scale --queue-depth=50 --min=6 --max=25

# Combined metrics auto-scaling
/scale myapp 5 all --auto-scale --cpu-threshold=70% --memory-threshold=75% --min=3 --max=15
```

### Claude Code Environment Auto-Scaling

Auto-scaling for Claude Code environments includes agent-specific metrics and intelligent resource allocation:

```bash
# Agent task-based auto-scaling
/scale claude-env 8 all --claude-code --auto-scale --agents=all \
  --task-queue-depth=50 --response-time-threshold=3s --min=4 --max=20

# Workspace utilization-based scaling
/scale claude-workspaces 10 mesh --claude-code --auto-scale --workspaces=10 \
  --workspace-utilization=80% --min=5 --max=25

# Orchestrator load-based scaling
/scale claude-orchestrator 6 digitalocean --claude-code --auto-scale --orchestrator \
  --concurrent-tasks=40 --coordination-load=70% --min=3 --max=12

# MCP server demand-based scaling
/scale claude-env 12 all --claude-code --auto-scale --mcp-servers=all \
  --mcp-request-rate=100req/min --server-response-time=2s --min=6 --max=30
```

#### Agent-Specific Auto-Scaling Metrics

- **Task Queue Depth**: Number of pending tasks per agent type
- **Response Time**: Agent task completion and response times
- **Throughput**: Tasks processed per minute per agent
- **Error Rate**: Agent task failure rates
- **Resource Utilization**: CPU, memory, and storage per agent
- **Concurrent Task Capacity**: Maximum simultaneous tasks per agent

#### Advanced Auto-Scaling Triggers

```bash
# Multi-metric agent scaling with cooldowns
/scale claude-env 15 all --claude-code --auto-scale --agents=api-specialist \
  --cpu-threshold=70% --memory-threshold=75% --task-queue-depth=30 \
  --response-time-threshold=2s --scale-up-cooldown=300s --scale-down-cooldown=900s

# Priority-based agent scaling
/scale claude-env 8 digitalocean --claude-code --auto-scale --agents=security-auditor \
  --priority=high --min=4 --max=10 --scale-up-threshold=60% --scale-down-threshold=25%
```

### Auto-Scaling Rules

The system follows these auto-scaling rules:

#### Traditional Application Scaling Rules

1. **Scale-Up Triggers**:
   - CPU usage > threshold for 5 minutes
   - Memory usage > threshold for 5 minutes
   - Queue depth > threshold for 3 minutes
   - Response time > 2x baseline for 5 minutes

2. **Scale-Down Triggers**:
   - CPU usage < 30% for 15 minutes
   - Memory usage < 40% for 15 minutes
   - Queue depth < 10 for 10 minutes
   - Response time < baseline for 15 minutes

3. **Cooldown Periods**:
   - Scale-up cooldown: 5 minutes
   - Scale-down cooldown: 15 minutes

#### Claude Code Environment Auto-Scaling Rules

1. **Agent Scale-Up Triggers**:
   - Task queue depth > threshold for 3 minutes
   - Agent response time > threshold for 5 minutes
   - Agent error rate > 5% for 5 minutes
   - Concurrent task capacity > 90% for 2 minutes
   - Workspace utilization > 80% for 5 minutes

2. **Agent Scale-Down Triggers**:
   - Task queue depth < 5 for 15 minutes
   - Agent response time < 50% threshold for 10 minutes
   - Agent error rate < 1% for 15 minutes
   - Concurrent task capacity < 30% for 20 minutes
   - Workspace utilization < 40% for 15 minutes

3. **Orchestrator Scale-Up Triggers**:
   - Coordination load > threshold for 3 minutes
   - Task distribution latency > threshold for 5 minutes
   - Agent management requests > capacity for 2 minutes
   - WebSocket connection count > 80% capacity for 5 minutes

4. **MCP Server Scale-Up Triggers**:
   - MCP request rate > threshold for 3 minutes
   - Server response time > threshold for 5 minutes
   - Protocol error rate > 3% for 5 minutes
   - Connection pool utilization > 85% for 2 minutes

5. **Claude Code Cooldown Periods**:
   - Agent scale-up cooldown: 3 minutes
   - Agent scale-down cooldown: 10 minutes
   - Orchestrator scale-up cooldown: 2 minutes
   - MCP server scale-up cooldown: 4 minutes
   - Workspace scale-up cooldown: 5 minutes

## Load Balancing Strategies

### Round-Robin Distribution
Evenly distribute instances/workers across all target servers.

```bash
/scale myapp 6 all --strategy=round-robin
```

### Least Connections
Place new instances on servers with the fewest active connections.

```bash
/scale myapp 8 mesh --strategy=least-connections
```

### Weighted Distribution
Distribute based on server capacity and performance metrics.

```bash
/scale myapp 10 digitalocean --strategy=weighted
```

### Queue-Aware Distribution
Place worker agents based on queue affinity and message routing patterns.

```bash
/scale myapp-workers 15 mesh --strategy=queue-aware --queue=myapp.workers.api
```

### Agent-Aware Distribution (Claude Code)
Distribute Claude Code agents based on task types, capabilities, and workload patterns.

```bash
# Distribute agents based on task specialization
/scale claude-env 12 all --claude-code --strategy=agent-aware --agents=api-specialist,database-architect

# Distribute based on agent workload patterns
/scale claude-env 8 mesh --claude-code --strategy=workload-aware --workspace-size=medium
```

### Workspace-Based Distribution
Distribute agents and workspaces based on project requirements and team collaboration needs.

```bash
# Distribute workspaces across servers for optimal collaboration
/scale claude-workspaces 15 all --claude-code --strategy=workspace-distribution --workspace-size=large

# Team-based workspace distribution
/scale claude-env 10 digitalocean --claude-code --strategy=team-based --teams=backend,frontend,devops
```

### Capability-Based Scaling
Scale agents based on their specific capabilities and current demand.

```bash
# Scale high-demand agent capabilities
/scale claude-env 6 mesh --claude-code --strategy=capability-based --capability=web-automation

# Multi-capability agent scaling
/scale claude-env 8 all --claude-code --strategy=capability-based --capability=security-auditing,performance-testing
```

## Server-Specific Scaling

### Mesh Servers (Local High-Performance)
- **Max Instances**: 8-12 per server
- **Best For**: CPU-intensive, low-latency workloads
- **Worker Capacity**: 5-8 workers per server
- **Load Balancing**: Round-robin or least-connections
- **Claude Code Agent Capacity**: 6-10 agents per server
- **Workspace Capacity**: 4-6 workspaces per server

```bash
# Scale across mesh servers with capacity limits
/scale myapp 24 mesh --strategy=least-connections --max-per-server=8
/scale myapp-workers 40 mesh --max-per-server=8 --queue=myapp.workers.database

# Claude Code environment scaling on mesh servers
/scale claude-env 20 mesh --claude-code --max-per-server=10 --agent-memory=3GB
/scale claude-workspaces 12 mesh --claude-code --workspace-size=large --max-per-server=6
```

### AgenticOverlord Servers (Cloudflare Tunnel)
- **Max Instances**: 4-6 per server
- **Best For**: Remote access, external API workloads
- **Worker Capacity**: 3-5 workers per server
- **Load Balancing**: Weighted or round-robin
- **Claude Code Agent Capacity**: 3-5 agents per server
- **Workspace Capacity**: 2-3 workspaces per server

```bash
# Scale across agenticoverlord with tunnel considerations
/scale myapp 12 agenticoverlord --strategy=weighted --max-per-server=4
/scale myapp-workers 20 agenticoverlord --max-per-server=5 --queue=myapp.workers.api

# Claude Code scaling for remote access scenarios
/scale claude-env 8 agenticoverlord --claude-code --max-per-server=5 --agent-memory=2GB
/scale claude-workspaces 6 agenticoverlord --claude-code --workspace-size=medium --max-per-server=3
```

### DigitalOcean Servers (Production Cloud)
- **Max Instances**: 15-20 per server
- **Best For**: Production workloads, high availability
- **Worker Capacity**: 10-15 workers per server
- **Load Balancing**: Weighted or queue-aware
- **Claude Code Agent Capacity**: 12-18 agents per server
- **Workspace Capacity**: 8-12 workspaces per server

```bash
# Production scaling with high availability
/scale myapp 40 digitalocean --strategy=weighted --max-per-server=15
/scale myapp-workers 60 digitalocean --max-per-server=15 --queue=myapp.workers.security

# Production Claude Code environment scaling
/scale claude-env 50 digitalocean --claude-code --max-per-server=18 --agent-memory=4GB
/scale claude-workspaces 30 digitalocean --claude-code --workspace-size=large --max-per-server=12
```

## LAVINMQ Queue Integration

### Queue-Worker Mapping

The scaling system automatically maps worker agents to appropriate LAVINMQ queues:

```
Application: myapp
├── Main Application Instances: 6
├── Worker Agent Pools:
│   ├── API Workers: 12 (myapp.workers.api)
│   ├── Database Workers: 8 (myapp.workers.database)
│   ├── Security Workers: 4 (myapp.workers.security)
│   └── Integration Workers: 6 (myapp.workers.integration)
└── Priority Queues:
    ├── High Priority: 2 workers
    ├── Medium Priority: 4 workers
    └── Low Priority: 2 workers
```

### Queue-Based Scaling Logic

1. **Monitor Queue Depth**: Track message count in each queue
2. **Calculate Required Workers**: Determine optimal worker count based on processing rates
3. **Distribute Workers**: Place workers on servers with available capacity
4. **Balance Load**: Distribute workers across multiple servers for redundancy
5. **Monitor Performance**: Track worker processing rates and queue drain times

### Advanced Queue Scaling

```bash
# Scale specific queue workers with custom thresholds
/scale myapp-workers 20 mesh --queue=myapp.workers.api --queue-depth=30 --min=10 --max=50

# Scale multiple queue types
/scale myapp-workers 15 all --queue=myapp.workers.database --auto-scale
/scale myapp-workers 8 all --queue=myapp.workers.security --strategy=weighted

# Priority queue scaling
/scale myapp-workers 6 digitalocean --queue=myapp.priority.high --min=4 --max=10
```

## Monitoring and Analytics

### Scaling Metrics

The system provides comprehensive metrics for scaling decisions:

- **Resource Utilization**: CPU, memory, disk, network usage per server
- **Application Performance**: Response times, throughput, error rates
- **Queue Metrics**: Message rates, processing times, queue depths
- **Worker Health**: Worker availability, processing rates, error rates
- **Load Distribution**: Connection counts, request distribution
- **Claude Code Agent Metrics**: Agent task completion times, error rates, resource usage
- **Workspace Utilization**: Workspace usage patterns, collaboration metrics
- **Orchestrator Performance**: Task distribution efficiency, coordination latency
- **MCP Server Metrics**: Protocol performance, request rates, response times

### Real-Time Monitoring

```bash
# Monitor scaling status
/status myapp --scaling --verbose

# Check worker agent distribution
/queues status --workers --distribution

# Monitor auto-scaling activity
/scale myapp --monitoring --auto-scale-status

# Server resource usage during scaling
/servers mesh --monitoring=high --resource-usage

# Claude Code environment monitoring
/scale claude-env --monitoring --claude-code --agent-metrics
/agents status --scaling --performance --resource-usage
/orchestrate status --monitoring --coordination-metrics
/queues status --mcp-servers --performance-monitoring
/servers all --claude-code-status --scaling-metrics
```

### Performance Analytics

```bash
# Analyze scaling performance
/scale myapp --analytics --period=24h

# Worker performance analysis
/queues analytics --queue=myapp.workers.api --period=1h

# Load balancing effectiveness
/scale myapp --load-balancing-report --strategy=least-connections

# Claude Code environment performance analytics
/scale claude-env --analytics --claude-code --period=24h --agent-performance
/agents analytics --scaling-history --resource-efficiency --period=1h
/orchestrate analytics --coordination-performance --scaling-decisions --period=6h
/queues analytics --mcp-server-performance --protocol-efficiency --period=3h
```

## Advanced Scaling Features

### Blue-Green Scaling

Maintain two separate environments for zero-downtime deployments:

```bash
# Scale green environment while blue serves traffic
/scale myapp-green 8 mesh --strategy=round-robin
# Switch traffic to green
/deploy myapp mesh main --target=green
# Scale down blue environment
/scale myapp-blue 0 mesh
```

### Canary Scaling

Gradual rollout to subset of servers:

```bash
# Start with 20% of servers
/scale myapp 4 mesh --strategy=canary --canary-percentage=20
# Monitor and expand if healthy
/scale myapp 10 mesh --strategy=canary --canary-percentage=50
# Full rollout
/scale myapp 20 mesh --strategy=round-robin
```

### Burst Scaling

Handle temporary traffic spikes:

```bash
# Enable burst scaling for events
/scale myapp 15 all --strategy=burst --burst-duration=2h --burst-factor=2

# Automatic burst scaling based on traffic patterns
/scale myapp 10 mesh --auto-scale --burst-mode --traffic-threshold=200%
```

## Configuration Management

### Scaling Configuration Files

```yaml
# scaling-config.yml
applications:
  myapp:
    min_instances: 3
    max_instances: 20
    auto_scale: true
    cpu_threshold: 75
    memory_threshold: 80
    strategy: least-connections
    servers:
      mesh:
        max_per_server: 8
        weight: 1.0
      digitalocean:
        max_per_server: 15
        weight: 1.2

    workers:
      api:
        queue: myapp.workers.api
        min_workers: 6
        max_workers: 30
        auto_scale: true
        queue_depth_threshold: 50

      database:
        queue: myapp.workers.database
        min_workers: 4
        max_workers: 20
        auto_scale: true
        queue_depth_threshold: 25

  claude_code_environments:
    claude-env:
      min_agents: 5
      max_agents: 30
      auto_scale: true
      cpu_threshold: 75
      memory_threshold: 80
      agent_memory_default: 2GB
      workspace_size_default: medium
      servers:
        mesh:
          max_agents_per_server: 10
          weight: 1.0
        digitalocean:
          max_agents_per_server: 18
          weight: 1.2

      agents:
        api-specialist:
          min_instances: 3
          max_instances: 15
          auto_scale: true
          memory_per_agent: 3GB
          task_queue_threshold: 20

        database-architect:
          min_instances: 2
          max_instances: 10
          auto_scale: true
          memory_per_agent: 4GB
          task_queue_threshold: 15

        security-auditor:
          min_instances: 2
          max_instances: 8
          auto_scale: true
          memory_per_agent: 2GB
          priority: high

      workspaces:
        small:
          memory: 2GB
          cpu_cores: 2
          storage: 50GB
        medium:
          memory: 4GB
          cpu_cores: 4
          storage: 100GB
        large:
          memory: 8GB
          cpu_cores: 8
          storage: 200GB

      mcp_servers:
        filesystem:
          min_instances: 4
          max_instances: 20
          auto_scale: true
          request_rate_threshold: 50req/min

        database:
          min_instances: 2
          max_instances: 12
          auto_scale: true
          request_rate_threshold: 30req/min

        web-search:
          min_instances: 3
          max_instances: 15
          auto_scale: true
          request_rate_threshold: 40req/min
```

### Claude Code Environment-Specific Scaling

```bash
# Development environment Claude Code scaling
/scale claude-dev 3 mesh --claude-code --env=dev --workspace-size=small --agents=api-specialist,database-architect

# Staging environment Claude Code scaling
/scale claude-staging 6 agenticoverlord --claude-code --env=staging --auto-scale --min=4 --max=12 --workspace-size=medium

# Production environment Claude Code scaling
/scale claude-prod 15 digitalocean --claude-code --env=prod --auto-scale --min=10 --max=40 --workspace-size=large --cpu-threshold=70
```

### Environment-Specific Scaling

```bash
# Development environment scaling
/scale myapp 3 mesh --env=dev --strategy=round-robin

# Staging environment scaling
/scale myapp 6 agenticoverlord --env=staging --auto-scale --min=4 --max=10

# Production environment scaling
/scale myapp 15 digitalocean --env=prod --auto-scale --min=10 --max=30 --cpu-threshold=70
```

## Troubleshooting Scaling Issues

### Common Scaling Problems

1. **Resource Exhaustion**: Servers lack CPU/memory for new instances
2. **Network Connectivity**: Cannot reach target servers
3. **LAVINMQ Connection Issues**: Workers cannot connect to message queues
4. **Load Balancer Misconfiguration**: Traffic not distributed correctly
5. **Health Check Failures**: New instances failing health checks
6. **Agent Scaling Failures**: Claude Code agents failing to scale or initialize
7. **Workspace Resource Issues**: Insufficient workspace resources or configuration errors
8. **Orchestrator Scaling Problems**: Coordination layer scaling failures
9. **MCP Server Scaling Issues**: Protocol server scaling or connectivity problems
10. **Agent Memory Allocation**: Incorrect memory allocation for agent instances

### Diagnostic Commands

```bash
# Check server capacity
/servers all --capacity-check --resource-usage

# Diagnose scaling failures
/scale myapp --diagnose --last-operation

# Check LAVINMQ connectivity
/queues status --connection-test --workers

# Load balancer health check
/scale myapp --load-balancer-test --strategy=least-connections

# Worker agent diagnostics
/queues diagnostics --queue=myapp.workers.api --worker-health

# Claude Code environment scaling diagnostics
/scale claude-env --diagnose --last-operation --claude-code
/agents diagnostics --scaling-issues --resource-allocation
/orchestrate diagnostics --coordination-scaling --agent-distribution
/queues diagnostics --mcp-servers --scaling-problems
/servers all --claude-code-diagnostic --resource-check --scaling-capacity
```

### Recovery Procedures

```bash
# Emergency scaling down
/scale myapp 2 mesh --force --emergency

# Redistribute workers after server failure
/scale myapp-workers 10 mesh --redistribute --exclude=failed-server

# Reset auto-scaling configuration
/scale myapp --reset-auto-scale --defaults

# Claude Code environment scaling recovery
/scale claude-env 2 mesh --force --emergency --claude-code --preserve-workspaces
/scale claude-orchestrator 1 digitalocean --force --emergency --restore-coordination
/scale claude-workspaces 0 all --force --cleanup --preserve-data
/agents recovery --scaling-failures --reset-to-defaults
/orchestrate recovery --coordination-scaling --reinitialize
/queues recovery --mcp-servers --restart-scaling
```