# Multi-Agent Orchestration System (MAO)

> A production-ready web-based orchestration system for managing and coordinating multiple Claude Code agents at scale with real-time streaming, PostgreSQL persistence, and comprehensive observability.

## 🎯 System Overview

The Multi-Agent Orchestration System (MAO) is a sophisticated platform that enables seamless collaboration between specialized AI agents through coordinated, parallel workflows. It provides real-time coordination, comprehensive logging, cost tracking, and a sophisticated template system for rapid agent specialization.

**Key Features:**
- 🔄 **Real-time coordination** via WebSocket broadcasting
- 🧠 **Specialized agent templates** for different task types
- 📊 **Comprehensive logging & cost tracking**
- ⚡ **Parallel execution** with state management
- 🛠️ **Production-grade tools** for AI development

---

## 1. Multi-Agent Orchestration System

### How the Orchestrator Delegates Tasks

The orchestrator acts as a central coordinator that delegates tasks to specialized agents through a sophisticated management system.

#### Core Delegation Architecture

```python
# AgentManager Class - Central coordination hub
class AgentManager:
    # 8 core management tools for orchestrator
    - create_agent: Creates new agents with template support
    - list_agents: Lists all active agents
    - command_agent: Sends commands to specific agents
    - check_agent_status: Monitors agent activity
    - delete_agent: Removes agents and resources
    - interrupt_agent: Stops running agents
    - read_system_logs: Access system logs
    - report_cost: Tracks token usage and costs
```

#### Agent Creation Process

```bash
# Template-based agent creation
result = orchestrator.create_agent(
    name="api-developer",
    subagent_template="api-specialist",
    model="sonnet",
    working_dir="/project/api"
)

# Manual agent creation
result = orchestrator.create_agent(
    name="custom-planner",
    system_prompt="You are a planning specialist...",
    model="sonnet",
    tools=["Read", "Write", "Grep", "Glob"],
    working_dir="/project"
)
```

#### Session Management & State Tracking

- **Session Resumption**: Agents maintain context across multiple commands
- **Token Tracking**: Real-time monitoring of input/output tokens and costs
- **Status Management**: Agents transition between states (idle, executing, waiting, blocked, complete)
- **File Tracking**: Each agent has dedicated FileTracker for file operations

---

## 2. Available Agent Templates

The system uses a sophisticated template system for rapid agent specialization. Templates are stored as markdown files with YAML frontmatter.

### Template Structure

```yaml
---
name: template-name
description: Brief description of agent purpose
tools: Read,Write,Edit,Glob,Grep,Bash,TodoWrite  # Allowed tools
model: sonnet
color: purple  # UI color coding
---

# Detailed system prompt content
## Specialized workflow instructions
## Example usage patterns
```

### Complete Template Inventory

| Template | Purpose | Key Tools | Use Cases |
|----------|---------|-----------|-----------|
| **api-specialist** | API development, integration, endpoint creation | Read,Write,Edit,Glob,Grep,Bash,WebFetch | FastAPI, NestJS, REST APIs, WebSocket |
| **database-architect** | Database design, migrations, optimization | Read,Write,Edit,Glob,Grep,Bash,TodoWrite | PostgreSQL, Prisma, schema design |
| **security-auditor** | Code security review, vulnerability assessment | Read,Glob,Grep,Bash,WebSearch,Task | Security analysis, penetration testing |
| **build-agent** | Single file implementation specialist | Write,Read,Edit,Grep,Glob,Bash,TodoWrite | Targeted file creation/modification |
| **review-agent** | Code review and validation specialist | Read,Glob,Grep,Bash,Task | Code validation, risk assessment |
| **mcp-server-developer** | Model Context Protocol server development | Read,Write,Edit,Glob,Grep,Bash | Creating MCP servers, AI-native APIs |
| **integration-specialist** | System integration and connectivity | Read,Write,Edit,Grep,Bash,WebFetch | API integrations, external connections |
| **ai-workflow-optimizer** | Workflow optimization specialist | Read,Glob,Grep,Bash,Task,WebSearch | AI process optimization, automation |
| **docs-scraper** | Documentation extraction and processing | mcp__firecrawl-mcp__firecrawl_scrape,WebFetch | Fetching and processing documentation |
| **playwright-validator** | Frontend testing and validation | mcp__playwright__*,Read,Write,Edit | Web UI testing, validation |
| **meta-agent** | Metacognitive and prompt engineering | Read,Write,Edit,WebSearch,Task | Prompt design, agent configuration |

### Specialized Capabilities

#### API Specialist Workflow
```python
# Example: Building a REST API
1. Requirements Analysis: Understand API purpose and consumers
2. Design Phase: Plan endpoints, schemas, authentication
3. Implementation: Write controllers/services with FastAPI/NestJS
4. Documentation: Create OpenAPI specs and examples
5. Testing: Integration tests and validation
```

#### Database Architect Workflow
```python
# Example: Database design
1. Data Analysis: Understand business entities and relationships
2. Schema Design: Create Prisma schemas and migration plans
3. Implementation: Write migrations and complex queries
4. Optimization: Add indexes and performance tuning
5. Documentation: Data dictionaries and rollback plans
```

#### Build Agent Workflow
```python
# Example: File implementation
1. Specification Analysis: Extract requirements and constraints
2. Context Gathering: Read referenced files and understand patterns
3. Implementation: Write production-quality code with error handling
4. Validation: Type checking, linting, basic tests
5. Documentation: Implementation summary and integration notes
```

---

## 3. Getting Started Guide

### For Human Developers

#### Quick Start
```bash
# Start the orchestrator backend
cd apps/orchestrator_3_stream
./start_be.sh  # Runs on port 8002

# Start the frontend
./start_fe.sh  # Runs on port 5175

# Access the web interface
open http://localhost:5175
```

#### Using Slash Commands
```bash
# Three-phase development workflow
/orch_plan_w_scouts_build_review "Build a user authentication API"

# Parallel agent execution
/parallel_subagents "Analyze project dependencies" 4

# Quick implementation planning
/quick-plan "Implement a caching layer"

# Build from existing plan
/build specs/my-project-plan.md
```

### For AI Agents

#### Understanding Your Role
When you're created as a subagent, you should:

1. **Review Your Template**: Check your available tools and capabilities
2. **Understand the Context**: Read the orchestrator's metadata and task description
3. **Follow the Workflow**: Execute the specific workflow defined for your template
4. **Communicate Progress**: Use the provided tools to report status
5. **Maintain State**: Keep context across multiple commands

#### Agent Communication Pattern
```python
# 1. Receiving a task
task_description = "Create a REST API for user management"
orchestrator_metadata = orchestrator.get_metadata()

# 2. Executing the task
result = orchestrator.command_agent(
    agent_id="api-specialist-123",
    command=task_description,
    tools=["Read", "Write", "Edit", "Bash", "Grep"],
    system_prompt="You are an API development specialist..."
)

# 3. Reporting progress
while result.status == "executing":
    status = orchestrator.check_agent_status(result.agent_id)
    # WebSocket events broadcast automatically
    time.sleep(15)

# 4. Final report
final_report = orchestrator.read_agent_logs(result.agent_id)
```

---

## 4. Architecture Overview

### Communication Flow

```
User Frontend (Vue 3)
    ↕ WebSocket
WebSocket Manager (Backend)
    ↕ Command/Events
Agent Manager + Specialized Agents
    ↕ Database
PostgreSQL (Agents, Logs, Events)
```

### Event Broadcasting System

```python
# Real-time coordination via WebSocket
event_types = [
    "agent_created",          # New agent created
    "agent_status_change",   # Status transition
    "agent_log",             # Activity logging
    "agent_summary_update",  # AI-generated summaries
    "orchestrator_log",      # System events
    "chat_message"           # User communication
]

# Event structure
{
    "event_type": "agent_log",
    "agent_id": "abc-123",
    "timestamp": "2024-01-01T12:00:00Z",
    "event_category": "response",
    "event_type": "TextBlock",
    "data": {
        "content": "Task completed successfully",
        "tool_calls": [...],
        "file_changes": [...]
    }
}
```

### Coordination Patterns

#### 1. Centralized Orchestration
- Orchestrator coordinates all agent activities
- Commands flow: User → Orchestrator → Agents
- Events flow: Agents → WebSocket → Frontend

#### 2. Template-Based Specialization
- Pre-defined templates provide specialized capabilities
- Tools are restricted based on template requirements
- Models are optimized for task types

#### 3. Real-Time Monitoring
- WebSocket provides live updates of all agent activities
- Cost tracking and token usage monitoring
- File operation tracking and change detection

#### 4. Persistent State Management
- PostgreSQL stores agent metadata and logs
- Sessions can be resumed across system restarts
- Complete audit trail of all agent activities

---

## 5. Development Workflow

### Best Practices for Agentic AI Development

#### 1. Agent Creation Best Practices
```python
# Always use appropriate templates
bad_create_agent(
    name="api-developer",
    system_prompt="I can do anything..."  # Too generic
)

good_create_agent(
    name="api-developer",
    subagent_template="api-specialist"   # Specialized template
)
```

#### 2. Task Delegation Patterns
```python
# Sequential workflow for complex tasks
def sequential_delegation(task):
    # Phase 1: Planning
    planner = orchestrator.create_agent(
        name="planner",
        subagent_template="meta-agent"
    )
    orchestrator.command_agent(planner.id, task)

    # Phase 2: Implementation
    builder = orchestrator.create_agent(
        name="builder",
        subagent_template="build-agent"
    )
    plan = orchestrator.read_agent_logs(planner.id)
    orchestrator.command_agent(builder.id, task + " with plan: " + plan)

    # Phase 3: Review
    reviewer = orchestrator.create_agent(
        name="reviewer",
        subagent_template="review-agent"
    )
    orchestrator.command_agent(reviewer.id, task + " based on implementation")
```

#### 3. Parallel Execution Patterns
```python
# Parallel analysis for comprehensive understanding
def parallel_analysis(project_path):
    agents = orchestrator.create_agents([
        ("code-analyzer", "security-auditor"),
        ("arch-reviewer", "database-architect"),
        ("tech-writer", "docs-scraper")
    ], count=3)

    results = orchestrator.command_agents_parallel([
        agents[0].id, "Analyze code quality and security",
        agents[1].id, "Review database architecture",
        agents[2].id, "Generate technical documentation"
    ])

    return results
```

#### 4. Communication Best Practices
```python
# Always provide complete context
bad_command = "Fix the API"

good_command = """
Fix the user authentication API at /api/auth:
- Current issue: JWT tokens are not being properly refreshed
- Use the api-specialist template
- Reference existing authentication in src/auth/
- Follow OAuth 2.0 best practices
- Include proper error handling and logging
"""

# Use thinking mode for complex tasks
complex_command = """
Analyze the microservices architecture and identify optimization opportunities.

Use 'ultrathink' mode for comprehensive analysis:
1. Map all services and their dependencies
2. Identify performance bottlenecks
3. Suggest scaling strategies
4. Document findings in architecture-review.md
"""
```

### Common Workflow Examples

#### Example 1: API Development Workflow
```bash
# Step 1: Three-phase API development
/orch_plan_w_scouts_build_review "Build a REST API for user management"

# Step 2: Monitor progress via web interface
# Open http://localhost:5175 to see live updates
# View agent status, logs, and file changes

# Step 3: Review results
# Check final validation report from review agent
# Test the implemented API endpoints
```

#### Example 2: Database Migration Workflow
```bash
# Step 1: Create database architecture specialist
# Using database-architect template

# Step 2: Design new schema
/database-architect "Design normalized schema for e-commerce platform"

# Step 3: Implement migrations
/build-agent "Create migration files for new schema"

# Step 4: Review and optimize
/security-auditor "Review database security and performance"
```

#### Example 3: Documentation Generation Workflow
```bash
# Step 1: Parallel documentation generation
/parallel_subagents "Generate comprehensive project documentation" 3

# Step 3: Each agent specializes in different documentation types:
# - API documentation (api-specialist)
# - User guides (docs-scraper)
# - Technical architecture (meta-agent)

# Step 4: Review and consolidate
/review-agent "Review and consolidate all documentation"
```

### Advanced Agent Coordination

#### Multi-Agent Projects
For complex projects requiring multiple specialized agents:

```python
# Create coordinated team of specialists
def create_project_team(project_type):
    templates = {
        "web_app": ["api-specialist", "database-architect", "security-auditor"],
        "data_project": ["database-architect", "integration-specialist", "ai-workflow-optimizer"],
        "microservices": ["api-specialist", "integration-specialist", "security-auditor"]
    }

    team = {}
    for template in templates[project_type]:
        agent = orchestrator.create_agent(
            name=f"{template}-{project_type}",
            subagent_template=template
        )
        team[template] = agent

    return team
```

#### Cross-Agent Communication
Agents can communicate by reading each other's logs:

```python
def cross_agent_collaboration():
    # Agent 1: Analysis
    analyzer = orchestrator.create_agent(
        name="code-analyzer",
        subagent_template="security-auditor"
    )

    orchestrator.command_agent(analyzer.id, "Analyze codebase for vulnerabilities")

    # Agent 2: Remediation
    fixer = orchestrator.create_agent(
        name="security-fixer",
        subagent_template="build-agent"
    )

    # Pass analysis results to fixer
    analysis = orchestrator.read_agent_logs(analyzer.id)
    orchestrator.command_agent(fixer.id, f"Fix vulnerabilities based on analysis:\n{analysis}")
```

---

## 6. Quick Start (Technical Details)

### Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **Anthropic API key** ([Get one here](https://console.anthropic.com/))
- **PostgreSQL database** - We recommend [NeonDB](https://neon.tech) (free serverless PostgreSQL)

### Database Setup

**Option A: NeonDB (Recommended - Free Tier Available)**
```bash
# Go to https://console.neon.tech/ and create a new project
# Copy connection string:
# postgresql://username:password@ep-xxx-xxx.aws.neon.tech/neondb?sslmode=require
```

**Option B: Docker (Quick Local Setup)**
```bash
docker run --name postgres-orch \
  -e POSTGRES_PASSWORD=mypassword \
  -e POSTGRES_DB=orchestrator \
  -p 5432:5432 \
  -d postgres:15
```

### Environment Setup
```bash
# Install Astral UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Bun
curl -fsSL https://bun.sh/install | bash

# Configure environment
cp .env.sample .env
# Edit .env with your API key and database URL
cp .env apps/orchestrator_3_stream/.env
cp .env apps/orchestrator_db/.env

# Initialize database
uv run apps/orchestrator_db/run_migrations.py
```

### Start Applications

**Backend:**
```bash
cd apps/orchestrator_3_stream
./start_be.sh
# Backend starts on http://127.0.0.1:8002
```

**Frontend:**
```bash
cd apps/orchestrator_3_stream/frontend
bun install  # First time only
cd ..
./start_fe.sh
# Frontend starts on http://127.0.0.1:5175
```

**Access the Application:**
Open http://localhost:5175 to see the 3-column interface:
- **Left**: Agent sidebar
- **Center**: Event stream (real-time logs)
- **Right**: Orchestrator chat

---

## 7. Project Structure

```
multi-agent-orchestration/
├── .env                          # Root environment config
├── apps/
│   ├── orchestrator_db/          # Database schema & models
│   │   ├── models.py             # Pydantic models
│   │   ├── migrations/           # SQL migration files
│   │   └── run_migrations.py     # Apply migrations
│   │
│   └── orchestrator_3_stream/    # Web orchestrator application
│       ├── .env                  # App-specific config
│       ├── start_be.sh           # Start backend
│       ├── start_fe.sh           # Start frontend
│       │
│       ├── .claude/              # Claude Code configuration
│       │   ├── agents/           # Specialized sub-agent templates
│       │   │   ├── build-agent.md
│       │   │   ├── api-specialist.md
│       │   │   ├── database-architect.md
│       │   │   ├── security-auditor.md
│       │   │   └── ... (other templates)
│       │   │
│       │   └── commands/         # Slash command workflows
│       │       ├── orch_plan_w_scouts_build_review.md
│       │       ├── parallel_subagents.md
│       │       └── ... (other commands)
│       │
│       ├── backend/              # Python FastAPI backend
│       │   ├── main.py           # FastAPI app + WebSocket
│       │   ├── modules/          # Core modules
│       │   │   ├── agent_manager.py    # Agent lifecycle
│       │   │   ├── websocket_manager.py  # WebSocket broadcasting
│       │   │   ├── orchestrator_service.py  # Orchestrator logic
│       │   │   └── database.py         # PostgreSQL operations
│       │   └── tests/            # Integration tests
│       │
│       └── frontend/             # Vue 3 TypeScript frontend
│           ├── src/
│           │   ├── App.vue       # 3-column layout
│           │   ├── components/   # UI components
│           │   ├── stores/       # Pinia state management
│           │   └── services/     # HTTP/WebSocket services
│           └── package.json
│
├── CLAUDE.md                     # Engineering rules for AI agents
└── README.md                     # This file
```

---

## 8. Configuration and Environment

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://...

# Backend configuration
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8002

# Frontend configuration
FRONTEND_HOST=127.0.0.1
FRONTEND_PORT=5175

# Orchestrator settings
ORCHESTRATOR_MODEL=claude-sonnet-4-5-20250929
ORCHESTRATOR_WORKING_DIR=/path/to/project
```

### Agent Configuration
```yaml
# Custom template example
---
name: custom-developer
description: Developer with specific toolset
tools: Read,Write,Edit,Bash,Grep,Glob  # Custom tool set
model: sonnet
color: blue
---

# Custom workflow instructions
Follow these steps for development tasks:
1. Analyze existing codebase structure
2. Implement changes following established patterns
3. Test changes thoroughly
4. Document changes in CHANGELOG.md
```

---

## 9. Monitoring and Debugging

### Real-time Monitoring
```python
# Check agent status
status = orchestrator.check_agent_status(agent_id)

# Monitor WebSocket events for live updates
# Events include: agent_created, agent_log, agent_status_change, etc.

# Cost tracking
cost_report = orchestrator.report_cost(agent_id)
```

### Debugging Tools
```bash
# View system logs
/read_system_logs

# Check specific agent status
/check_agent_status [agent_id]

# Interrupt problematic agents
/interrupt_agent [agent_id]

# Delete failed agents
/delete_agent [agent_id]
```

### CLI Options (Backend)
```bash
# Resume existing session
uv run python backend/main.py --session sess_abc123...

# Set custom working directory
uv run python backend/main.py --cwd /path/to/project

# Combine both
uv run python backend/main.py --session sess_xyz --cwd /my/project
```

---

## 10. Best Practices and Patterns

### For AI Agents
1. **Always use appropriate templates** - Never work without a specialized template
2. **Think before acting** - Use 'ultrathink' mode for complex analysis
3. **Maintain context** - Reference previous work and existing code
4. **Communicate clearly** - Report progress and obstacles promptly
5. **Validate work** - Always test and verify your implementations

### For Human Users
1. **Start with planning** - Use `/orch_plan_w_scouts_build_review` for complex tasks
2. **Monitor progress** - Watch the web interface for real-time updates
3. **Review thoroughly** - Always check the validation reports
4. **Iterate** - Use feedback from review agents to improve work
5. **Document** - Keep updated documentation for future reference

---

## 🔧 Troubleshooting

### Common Issues

**"Database connection failed"**
- Check `DATABASE_URL` in `.env`
- Verify database is running
- Run migrations: `uv run apps/orchestrator_db/run_migrations.py`

**"Port already in use"**
```bash
# Kill processes
lsof -ti:8002 | xargs kill -9  # Backend
lsof -ti:5175 | xargs kill -9  # Frontend
```

**"ANTHROPIC_API_KEY not found"**
- Add to root `.env` file
- Copy `.env` to `apps/orchestrator_3_stream/.env`
- Restart backend

**Frontend won't connect to backend**
- Check backend is running on port 8002
- Verify `VITE_API_BASE_URL` in `.env`
- Check browser console for CORS errors

---

## 🚀 Quick Start Commands

```bash
# For simple tasks
/quick-plan "Implement user authentication"

# For complex development
/orch_plan_w_scouts_build_review "Build a complete e-commerce platform"

# For parallel analysis
/parallel_subagents "Analyze project architecture" 4

# For documentation
/docs-scraper "Generate API documentation from OpenAPI spec"

# For code review
/review-agent "Review recent changes and provide risk assessment"
```

---

## 📚 Additional Resources

- **Web Interface**: http://localhost:5175 (when running)
- **Backend API**: http://localhost:8002 (when running)
- **Agent Templates**: `.claude/agents/` directory
- **Slash Commands**: `.claude/commands/` directory
- **Database Docs**: `apps/orchestrator_db/README.md`
- **App Docs**: `apps/orchestrator_3_stream/README.md`

---

*The Multi-Agent Orchestration System represents the future of AI-powered development, enabling seamless collaboration between specialized agents to accomplish complex tasks with unprecedented efficiency and quality.*