# Multi-Agent Orchestration System - Orchestrator 3 Stream

A sophisticated multi-agent orchestration system with PostgreSQL backend, Vue 3 frontend, and WebSocket streaming. This system enables AI agents to delegate tasks, coordinate complex workflows, and maintain real-time communication.

## 🎯 Overview

The Orchestrator 3 Stream system serves as a central hub for managing multiple specialized AI agents. It provides:

- **Task Delegation**: Orchestrator can create and command specialized agents
- **Real-time Coordination**: WebSocket-based communication with live updates
- **Template System**: Pre-configured agent templates for common tasks
- **Cost Management**: Token tracking and cost reporting for all agents
- **Workflow Automation**: Built-in workflow orchestrators for complex tasks
- **File Tracking**: Automatic monitoring of file operations by agents

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + TypeScript)            │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ Agent List  │  │ Event Stream │  │ Orchestrator Chat │   │
│  └─────────────┘  └──────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │ WebSocket (Real-time)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI + PostgreSQL)            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    Orchestrator                          │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐   │ │
│  │  │ Agent Mgmt  │  │ 8 Mgmt Tools │  │ WS Manager    │   │ │
│  │  └─────────────┘  └──────────────┘  └───────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                    │          │          │                   │
│             ┌──────┘          │          └──────┐           │
│   ┌─────────┴─────┐          │          ┌───────┴──────┐    │
│   │ Agents        │          │          │ Database     │    │
│   └───────────────┘          │          └──────────────┘    │
│                             │                             │
│                        ┌─────┴─────────┐                  │
│                        │ Agent Logs    │                  │
│                        │ Templates     │                  │
│                        │ File Tracking │                  │
│                        └───────────────┚                  │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Master Orchestrator Agent
The central agent that coordinates all activities:

- **8 Management Tools**: Complete lifecycle management for agents
- **Template Registry**: Dynamic loading of agent templates
- **WebSocket Communication**: Real-time event broadcasting
- **Database Integration**: Persistent state and logging

#### 2. Agent Management System
Complete agent lifecycle management:

- **create_agent**: Create new agents with template support
- **list_agents**: View all active agents and their status
- **command_agent**: Send commands to specific agents
- **check_agent_status**: Monitor agent activity and logs
- **delete_agent**: Remove agents and clean up resources
- **interrupt_agent**: Stop running agents
- **read_system_logs**: Access system-level logs
- **report_cost**: Track token usage and costs

#### 3. Agent Templates
Specialized pre-configured agents:

- **build-agent**: File implementation specialist
- **api-specialist**: FastAPI/NestJS development expert
- **database-architect**: PostgreSQL/Prisma schema design
- **security-auditor**: Code security assessment expert
- **mcp-server-developer**: Model Context Protocol specialist
- **integration-specialist**: System connectivity expert
- **ai-workflow-optimizer**: Process automation expert
- **review-agent**: Code review and validation specialist
- **meta-agent**: Prompt engineering specialist
- **docs-scraper**: Documentation extraction expert
- **playwright-validator**: Frontend testing specialist

#### 4. WebSocket Manager
Real-time event coordination:

- **Agent Events**: Creation, deletion, status changes
- **Log Streaming**: Live updates from all agents
- **Cost Tracking**: Real-time token and cost updates
- **File Tracking**: Automatic file operation monitoring

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (NeonDB recommended)
- Anthropic API key

### Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd apps/orchestrator_3_stream
   cp .env.sample .env
   # Edit .env with your configuration
   ```

2. **Backend Setup**
   ```bash
   # Install dependencies
   uv sync

   # Start backend
   ./start_be.sh
   ```

3. **Frontend Setup**
   ```bash
   # Install dependencies
   npm install

   # Start frontend
   ./start_fe.sh
   ```

4. **Access Application**
   - Frontend: http://localhost:5175
   - Backend API: http://localhost:8002

## 📚 Documentation

### 1. Orchestrator System

The Master Orchestrator Agent is the central coordinator that manages all agent activities.

#### Key Responsibilities

- **Task Delegation**: Assign specialized tasks to appropriate agent templates
- **Resource Management**: Monitor agent status, costs, and sessions
- **Event Coordination**: Broadcast real-time updates via WebSocket
- **Workflow Orchestration**: Execute complex multi-step workflows

#### Delegation Patterns

```python
# Template-based delegation (recommended)
await orchestrator.create_agent(
    name="api-developer",
    subagent_template="api-specialist",
    model="sonnet"
)

# Custom agent creation
await orchestrator.create_agent(
    name="custom-builder",
    system_prompt="You are a specialized file implementation agent...",
    model="sonnet",
    allowed_tools=["Read", "Write", "Edit", "Bash"]
)
```

#### Agent States

- **idle**: Ready to receive commands
- **executing**: Processing commands
- **waiting**: Awaiting user input or resources
- **blocked**: Encountered errors
- **complete**: Task finished successfully

### 2. Agent Management

#### Creating Agents

**Using Templates (Recommended):**
```python
# Use pre-configured templates
result = await create_agent(
    name="project-api-developer",
    subagent_template="api-specialist",  # Uses template's system prompt, tools, model
    model="sonnet"  # Optional override
)
```

**Manual Creation:**
```python
result = await create_agent(
    name="custom-agent",
    system_prompt="You are a specialized agent for...",
    model="sonnet",
    allowed_tools=["Read", "Write", "Edit", "Bash", "Grep"]
)
```

**Template Features:**
- **Pre-configured System Prompts**: Specialized behavior for each domain
- **Tool Restrictions**: Limited tool sets for focused work
- **Color Coding**: Visual identification in frontend
- **Model Selection**: Default model per template

#### Commanding Agents

```python
# Send command to agent
await command_agent("api-developer", "Create a REST API endpoint for user management")

# Monitor progress
status = await check_agent_status("api-developer", verbose_logs=True)

# Interrupt if needed
await interrupt_agent("api-developer")

# Clean up when done
await delete_agent("api-developer")
```

#### Agent Monitoring

**Real-time Status:**
```python
# Check recent activity
status = await check_agent_status(
    agent_name="api-developer",
    tail_count=20,          # Show last 20 events
    offset=0,              # Starting position
    verbose_logs=False     # Show summaries instead of full logs
)
```

**Cost Tracking:**
```python
# Get detailed cost report
cost_report = await report_cost()
# Returns: total tokens, costs, context usage percentage
```

### 3. MCP Integration

The system implements MCP (Model Context Protocol) for enhanced agent capabilities.

#### Management Tools

The orchestrator provides 8 built-in management tools:

1. **create_agent**: Create new agents with template support
2. **list_agents**: View all active agents
3. **command_agent**: Send commands to specific agents
4. **check_agent_status**: Monitor agent activity
5. **delete_agent**: Remove agents and clean up
6. **interrupt_agent**: Stop running agents
7. **read_system_logs**: Access system logs
8. **report_cost**: Track token usage and costs

#### MCP Server Development

**Creating MCP Servers:**
```python
# Use mcp-server-developer template
await create_agent(
    name="mcp-server-dev",
    subagent_template="mcp-server-developer"
)
```

**MCP Server Capabilities:**
- **Tool Definitions**: Define custom tools for agents
- **Resource Management**: Handle file and data resources
- **Protocol Compliance**: Follow MCP standards
- **Integration Ready**: Seamless integration with orchestrator

### 4. Agent Templates Reference

#### Build Agent (`build-agent`)
```yaml
---
name: build-agent
description: Specialist for implementing one specific file
tools: Write, Read, Edit, Grep, Bash, TodoWrite
model: sonnet
color: blue
---
```

**Purpose**: Production-quality file implementation with context awareness
**Best For**: Single file creation, refactoring, implementing specifications
**Key Features**:
- Context analysis from referenced files
- Code pattern recognition
- Production-ready implementation
- Comprehensive documentation

#### API Specialist (`api-specialist`)
```yaml
---
name: api-specialist
description: Specialist for API development and integration
tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, TodoWrite
model: sonnet
color: purple
---
```

**Purpose**: FastAPI/NestJS API development with OpenAPI documentation
**Best For**: REST APIs, WebSocket endpoints, API documentation
**Key Features**:
- Framework-specific code (FastAPI, NestJS)
- Automatic OpenAPI generation
- Authentication integration
- Comprehensive testing

#### Database Architect (`database-architect`)
```yaml
---
name: database-architect
description: Specialist for database architecture and migrations
tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, TodoWrite
model: sonnet
color: teal
---
```

**Purpose**: PostgreSQL/Prisma schema design and migration management
**Best For**: Database design, migrations, query optimization
**Key Features**:
- Prisma schema generation
- Migration planning
- Performance optimization
- Data modeling best practices

#### Security Auditor (`security-auditor`)
```yaml
---
name: security-auditor
description: Specialist for security assessment and review
tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch, TodoWrite
model: sonnet
color: red
---
```

**Purpose**: Security code review and vulnerability assessment
**Best For**: Security audits, compliance checks, secure coding
**Key Features**:
- Static code analysis
- Vulnerability assessment
- Security documentation
- Compliance reporting

#### Integration Specialist (`integration-specialist`)
```yaml
---
name: integration-specialist
description: Specialist for system integration and connectivity
tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch, TodoWrite
model: sonnet
color: orange
---
```

**Purpose**: System integration and external service connections
**Best For**: API integrations, webhook handling, data pipelines
**Key Features**:
- External API integration
- Data pipeline design
- Webhook management
- System architecture

#### AI Workflow Optimizer (`ai-workflow-optimizer`)
```yaml
---
name: ai-workflow-optimizer
description: Specialist for AI workflow automation
tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch, TodoWrite
model: sonnet
color: green
---
```

**Purpose**: AI workflow optimization and automation
**Best For**: Process automation, workflow design, optimization
**Key Features**:
- Workflow analysis
- Process optimization
- Automation strategies
- Performance tuning

#### Review Agent (`review-agent`)
```yaml
---
name: review-agent
description: Specialist for code review and validation
tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, TodoWrite
model: sonnet
color: gray
---
```

**Purpose**: Code review and validation with risk assessment
**Best For**: Code validation, quality assurance, risk assessment
**Key Features**:
- Git diff analysis
- Risk-tiered reporting
- Code quality assessment
- Validation recommendations

#### Meta Agent (`meta-agent`)
```yaml
---
name: meta-agent
description: Specialist for metacognitive and prompt engineering
tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch, TodoWrite
model: sonnet
color: violet
---
```

**Purpose**: Advanced prompt engineering and metacognitive strategies
**Best For**: Prompt optimization, metacognitive planning, strategy
**Key Features**:
- Prompt engineering
- Metacognitive strategies
- Planning optimization
- Advanced reasoning

#### Docs Scraper (`docs-scraper`)
```yaml
---
name: docs-scraper
description: Specialist for documentation extraction
tools: Read, Write, Edit, WebFetch, Bash, Glob, Grep, TodoWrite
model: sonnet
color: blue
---
```

**Purpose**: Documentation extraction and processing
**Best For**: Documentation analysis, API docs processing, research
**Key Features**:
- Web documentation scraping
- Markdown processing
- Documentation analysis
- Research assistance

#### Playwright Validator (`playwright-validator`)
```yaml
---
name: playwright-validator
description: Specialist for frontend testing and validation
tools: mcp__playwright__*, Read, Write, Edit, Bash, Glob, Grep, TodoWrite
model: sonnet
color: pink
---
```

**Purpose**: Frontend testing and UI validation with Playwright
**Best For**: E2E testing, UI validation, browser automation
**Key Features**:
- Browser automation
- E2E testing
- UI validation
- Performance testing

#### MCP Server Developer (`mcp-server-developer`)
```yaml
---
name: mcp-server-developer
description: Specialist for MCP server development
tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, TodoWrite
model: sonnet
color: indigo
---
```

**Purpose**: Model Context Protocol server development
**Best For**: MCP server creation, tool definitions, protocol implementation
**Key Features**:
- MCP tool definitions
- Server architecture
- Protocol implementation
- Integration development

### 5. Development Guide

#### Creating New Agent Templates

**Template Structure:**
```markdown
---
name: custom-template
description: Description of template purpose
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
color: custom-color
---

# Custom Template System Prompt

## Purpose
Describe what this template specializes in...

## Workflow
1. Step-by-step process
2. Key considerations
3. Best practices

## Tools Configuration
- Tools: List allowed tools
- Restrictions: Any disallowed tools
- Model: Preferred model (sonnet/haiku)
```

**Template Requirements:**
- **YAML Frontmatter**: Must include `name`, `description`, `tools`, `model`, `color`
- **System Prompt**: Comprehensive instructions for specialized behavior
- **Tool Selection**: Minimal, focused tool set for efficiency
- **Color Coding**: Unique color for frontend identification

**Adding Templates:**
1. Create template in `.claude/agents/` directory
2. Use kebab-case naming (e.g., `api-developer.md`)
3. Template is automatically discovered and registered
4. Available in orchestrator management tools

#### Extending the System

**Adding Management Tools:**
```python
# In agent_manager.py
@tool("new_tool", "Tool description", {"param": str})
async def new_tool_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    # Implementation
    pass
```

**Custom Event Types:**
```python
# In websocket_manager.py
await ws_manager.broadcast_custom_event(event_type, data)
```

**Database Extensions:**
- Add new tables to migration schema
- Update Pydantic models accordingly
- Add database queries to existing modules

#### Configuration

**Environment Variables (.env):**
```env
# Backend Configuration
BACKEND_PORT=8002
BACKEND_HOST=0.0.0.0
WEBSOCKET_PORT=8002

# Database Configuration
DATABASE_URL=postgresql://user:pass@host:port/db

# CORS Configuration
CORS_ORIGINS=http://localhost:5175,http://127.0.0.1:5175

# Model Configuration
DEFAULT_AGENT_MODEL=claude-sonnet-4-5-20250929
MAX_AGENT_TURNS=100
```

### 6. API Reference

#### Backend Endpoints

**Health Check**
```
GET /health
```
Response:
```json
{
  "status": "healthy",
  "service": "orchestrator-3-stream",
  "websocket_connections": 0
}
```

**Orchestrator Information**
```
GET /get_orchestrator
```
Response:
```json
{
  "status": "success",
  "orchestrator": {
    "id": "uuid",
    "session_id": "session-id",
    "status": "idle",
    "working_dir": "/path/to/workdir",
    "input_tokens": 1000,
    "output_tokens": 500,
    "total_cost": 0.0150,
    "metadata": {}
  },
  "slash_commands": [...],
  "agent_templates": [...],
  "orchestrator_tools": [...]
}
```

**Chat Interface**
```
POST /send_chat
Content-Type: application/json

{
  "message": "Hello, orchestrator",
  "orchestrator_agent_id": "uuid"
}
```

**Event Stream**
```
GET /get_events?agent_id=uuid&task_slug=name&limit=50&offset=0
```

**Agent Management**
```
GET /list_agents
POST /load_chat
```

**WebSocket Connection**
```
ws://localhost:8002/ws
```

#### Database Schema

**Orchestrator Agents Table**
```sql
CREATE TABLE orchestrator_agents (
    id UUID PRIMARY KEY,
    session_id TEXT UNIQUE,
    status TEXT NOT NULL,
    working_dir TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10,6) DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Agent Logs Table**
```sql
CREATE TABLE agent_logs (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES orchestrator_agents(id),
    task_slug TEXT,
    entry_index INTEGER,
    event_category TEXT,
    event_type TEXT,
    content TEXT,
    summary TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**System Logs Table**
```sql
CREATE TABLE system_logs (
    id UUID PRIMARY KEY,
    level TEXT,
    message TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 🔄 Workflows

### Three-Phase Development Workflow

Use `/orch_plan_w_scouts_build_review` for comprehensive development:

1. **Planning Phase**: Create custom planner agent
2. **Building Phase**: Use build-agent template for implementation
3. **Review Phase**: Validate with review-agent template

**Example Usage:**
```python
# Execute three-phase workflow
await command_agent("orchestrator", "/orch_plan_w_scouts_build_review 'Create a React login component'")
```

### Parallel Agent Workflow

Use `/parallel_subagents` for concurrent execution:

```python
# Launch multiple agents simultaneously
await command_agent("orchestrator", "/parallel_subagents 'Analyze this codebase' 3")
```

### Custom Workflow Example

```python
# Create specialized agents for a project
await create_agent("architect", subagent_template="meta-agent")
await create_agent("frontend-dev", subagent_template="build-agent")
await create_agent("backend-dev", subagent_template="api-specialist")
await create_agent("tester", subagent_template="playwright-validator")

# Execute coordinated workflow
await command_agent("architect", "Design project architecture")
await command_agent("frontend-dev", "Implement frontend based on architecture")
await command_agent("backend-dev", "Create API endpoints")
await command_agent("tester", "Test complete implementation")
```

## 📊 Monitoring & Analytics

### Real-time Monitoring

**Agent Status Dashboard:**
- Live agent activity tracking
- Token usage visualization
- Cost tracking per agent
- Task completion monitoring

**Event Stream:**
- Real-time agent log streaming
- File operation tracking
- Error monitoring and alerts
- Performance metrics

### Cost Management

**Token Tracking:**
- Input/output token monitoring
- Cost calculation per agent
- Context usage percentage
- Usage alerts and limits

**Optimization Strategies:**
- Context compaction when approaching limits
- Model selection based on task complexity
- Session management for long-running tasks

## 🔧 Best Practices

### Agent Coordination

1. **Clear Responsibilities**: Each template has specific, focused purpose
2. **Minimal Tool Access**: Restrict tools to prevent unnecessary complexity
3. **Template Reuse**: Leverage existing templates rather than creating new ones
4. **Status Monitoring**: Regularly check agent progress and adjust as needed

### Workflow Design

1. **Phased Execution**: Break complex tasks into logical phases
2. **Error Handling**: Implement proper error handling and recovery
3. **Resource Management**: Monitor costs and context usage
4. **Documentation**: Maintain clear logs and summaries

### Performance Optimization

1. **Context Management**: Monitor context limits and compact when needed
2. **Parallel Processing**: Use parallel workflows for independent tasks
3. **Template Selection**: Choose appropriate templates for each task
4. **Cost Awareness**: Track and optimize token usage

## 🚨 Troubleshooting

### Common Issues

**Agent Creation Failures:**
- Check template availability in `.claude/agents/`
- Verify tool restrictions don't block required operations
- Ensure proper model configuration

**WebSocket Connection Issues:**
- Verify CORS configuration
- Check WebSocket port accessibility
- Monitor connection count limits

**Database Problems:**
- Verify database connection string
- Check table permissions
- Monitor connection pool usage

### Debug Commands

```python
# Check agent status
await check_agent_status("agent-name", verbose_logs=True)

# View system logs
await read_system_logs(limit=100, level="ERROR")

# Get cost report
await report_cost()

# List active agents
await list_agents()
```

## 🤝 Contributing

### Development Setup

1. **Backend Development**:
   ```bash
   uv sync
   uv run pytest tests/
   ```

2. **Frontend Development**:
   ```bash
   npm run dev
   npm run test
   ```

3. **Template Development**:
   - Create templates in `.claude/agents/`
   - Test with orchestrator tools
   - Update documentation

### Guidelines

- **Template Quality**: Ensure templates are well-documented and tested
- **Tool Restriction**: Keep tool sets minimal and focused
- **Error Handling**: Implement comprehensive error handling
- **Documentation**: Keep README and API documentation current

## 📄 License

[Add your license information here]

## 🆘 Support

For support and questions:
- Create GitHub issues for bugs
- Use Discord/Slack for general questions
- Review existing documentation before asking

---

**Note**: This documentation is designed for both developers and AI agents. AI agents can use this information to understand the orchestration system capabilities and design appropriate workflows for their specific tasks.