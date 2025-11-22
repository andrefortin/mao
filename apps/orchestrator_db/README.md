# Orchestrator Database Schema & Models

**AI-native database schema and model definitions for the Multi-Agent Orchestration system**

🤖 **Optimized for AI Agents**: Designed specifically to support multi-agent workflows, agent lifecycle management, and AI-driven development patterns.

## 📁 Directory Structure

```
apps/orchestrator_db/
├── migrations/              # Idempotent SQL migration files
│   ├── 0_orchestrator_agents.sql
│   ├── 1_agents.sql
│   ├── 2_prompts.sql
│   ├── 3_agent_logs.sql
│   ├── 4_system_logs.sql
│   ├── 5_indexes.sql
│   ├── 6_functions.sql
│   ├── 7_triggers.sql
│   └── README.md            # Migration system documentation
├── models.py                # Pydantic models (source of truth)
├── run_migrations.py        # Migration runner script
├── sync_models.py           # Model synchronization script
└── README.md                # This file
```

## 🎯 Purpose

This directory serves as the **single source of truth** for:

1. **Database Schema** - PostgreSQL table definitions (via migrations)
2. **Data Models** - Pydantic models for type-safe database operations
3. **Model Distribution** - Syncing models to orchestrator apps
4. **AI Agent Support** - Optimized data structures for multi-agent workflows

## 🤖 Multi-Agent Architecture Support

The database schema is specifically designed to support AI-native development workflows:

### Agent Lifecycle Management
- **Agent Creation/Deletion**: Full lifecycle tracking with timestamps
- **Session Management**: Claude SDK session persistence across interactions
- **Cost Tracking**: Token usage and cost monitoring for budget optimization
- **Status Management**: Real-time agent status updates (idle, executing, blocked)

### Event-Driven Architecture
- **Unified Logging**: All agent activities captured in structured event logs
- **Hook Integration**: Pre/post tool execution tracking
- **Message Blocks**: Text, thinking, and tool use event preservation
- **Task Organization**: Events grouped by task_slug for workflow analysis

### AI-Optimized Queries
- **Performance Indexes**: Optimized for agent-centric query patterns
- **Temporal Queries**: Efficient time-based event retrieval
- **Agent Filtering**: Fast status and metadata-based filtering
- **Context Management**: Efficient conversation history storage

## 🚀 Quick Start

### Apply Database Schema

Run all migrations to set up or update the database:

```bash
uv run apps/orchestrator_db/run_migrations.py
```

This will:
- ✅ Create all 5 tables (orchestrator_agents, agents, prompts, agent_logs, system_logs)
- ✅ Add performance indexes optimized for AI agent workflows
- ✅ Set up trigger functions for auto-timestamps
- ✅ Preserve existing data (idempotent operations)

### Sync Models to Apps

After modifying `models.py`, sync to both orchestrator apps:

```bash
python apps/orchestrator_db/sync_models.py
```

This copies models to:
- `apps/orchestrator_1_term/modules/orch_database_models.py`
- `apps/orchestrator_3_stream/backend/modules/orch_database_models.py`

## 📋 Files Explained

### `models.py` - AI-Optimized Pydantic Models

**Purpose:** Central definition of all database models with automatic type conversion and AI agent support.

**Models:**
- `OrchestratorAgent` - Singleton orchestrator that manages other agents
- `Agent` - Managed agent registry with status and usage tracking
- `Prompt` - Prompt history from engineers or orchestrator with AI metadata
- `AgentLog` - Unified event log (hooks + responses) with block structure
- `SystemLog` - Application-level system logs for debugging AI workflows

**AI-Enhanced Features:**
- Automatic UUID conversion (handles asyncpg UUID objects)
- JSON field parsing (metadata, payload, AI context)
- Decimal to float conversion for cost tracking
- Type validation with Pydantic for agent reliability
- **AI Agent Metadata Support**: Special fields for AI agent context

**Usage:**
```python
from models import Agent, OrchestratorAgent, Prompt, AgentLog, SystemLog

# Automatically handles UUID conversion from database
agent = Agent(**row_dict)
print(agent.id)  # Works with both UUID objects and strings

# AI agent context support
agent_logs = await get_agent_logs(
    agent_id=agent_uuid,
    task_slug="ai-analysis-task",
    limit=50
)
```

### `migrations/` - Database Schema for AI Workflows

**Purpose:** Ordered, idempotent SQL migrations optimized for multi-agent systems.

**AI-Specific Design:**
- ✅ **Agent-Centric Design**: Tables optimized for agent lifecycle queries
- ✅ **Event Storage**: Efficient storage of AI agent events and responses
- ✅ **Metadata Support**: JSONB fields for flexible AI context storage
- ✅ **Performance Optimization**: Indexes for common AI agent query patterns

**Order of Execution:**
1. `0_orchestrator_agents.sql` - Singleton orchestrator (no dependencies)
2. `1_agents.sql` - Managed agents with AI metadata support
3. `2_prompts.sql` - Prompt history with AI context (FK → agents)
4. `3_agent_logs.sql` - Event logs with block structure (FK → agents)
5. `4_system_logs.sql` - System logs for AI debugging (nullable FK → agents)
6. `5_indexes.sql` - Performance indexes for AI agent workflows
7. `6_functions.sql` - Trigger functions for auto-timestamps
8. `7_triggers.sql` - Auto-update triggers

**See:** `migrations/README.md` for detailed migration documentation.

### `run_migrations.py` - AI-Aware Migration Runner

**Purpose:** Execute all migrations with rich terminal output and AI system validation.

**AI-Specific Features:**
- Rich progress tracking with spinners
- Colorized output (green ✓ / red ✗)
- Summary table of created schema
- **AI System Validation**: Validates AI agent compatibility
- Error reporting with AI context
- Loads DATABASE_URL from root `.env`

## 🗄️ Database Schema for AI Agents

### Tables

| Table                | AI Agent Purpose                           | Key Relationships   |
| -------------------- | ----------------------------------------- | ------------------- |
| `orchestrator_agents`| Master orchestrator agent management       | None                |
| `agents`             | Specialized agent registry with AI context | None                |
| `prompts`            | AI agent prompt history and metadata       | FK → agents         |
| `agent_logs`         | AI agent event logs (hooks + responses)   | FK → agents         |
| `system_logs`        | Application logs for AI debugging         | Nullable FK → agents|

### AI-Optimized Indexes

36 total indexes optimized for AI agent workflows:
- **Agent Status Indexes**: Fast filtering of active/executing agents
- **Temporal Indexes**: Efficient chronological queries for agent history
- **Task-based Indexes**: Quick retrieval of events by task_slug
- **Metadata Indexes**: JSONB field indexing for AI context queries
- **Foreign Key Indexes**: Optimized agent relationship queries

### AI Event Structure

The schema supports sophisticated AI agent event tracking:

```sql
-- Agent logs support structured AI events
CREATE TABLE agent_logs (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    task_slug TEXT,                    -- AI workflow grouping
    entry_index INTEGER,               -- Event sequence
    event_category TEXT,               -- 'request', 'response'
    event_type TEXT,                   -- 'TextBlock', 'ToolUseBlock', 'ThinkingBlock'
    content TEXT,                      -- Event content
    payload JSONB,                     -- AI-specific metadata
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔧 AI Agent Development Tasks

### Add New Agent-Specific Tables

1. Create `8_ai_feature.sql` in `migrations/`
2. Use `CREATE TABLE IF NOT EXISTS` with AI-specific fields
3. Include JSONB metadata columns for flexibility
4. Add indexes for AI agent query patterns
5. Update `run_migrations.py` MIGRATIONS list
6. Run migrations

### Extend Models for AI Features

1. Edit `models.py` with new Pydantic models
2. Include AI metadata fields (JSON, optional types)
3. Add validation for AI-specific data structures
4. Sync to apps: `python apps/orchestrator_db/sync_models.py`

### Query Patterns for AI Agents

```python
# Efficient AI agent queries
async def get_agent_workflow_history(agent_id: uuid.UUID, task_slug: str):
    """Get all events for an AI agent workflow"""
    return await fetch(
        """
        SELECT * FROM agent_logs 
        WHERE agent_id = $1 AND task_slug = $2
        ORDER BY entry_index ASC
        """,
        agent_id, task_slug
    )

async def get_active_ai_agents():
    """Get currently executing AI agents"""
    return await fetch(
        """
        SELECT * FROM agents 
        WHERE status = 'executing'
        ORDER BY created_at DESC
        """
    )
```

## 🤖 AI Agent Integration Guide

### For AI Agents Using This Database

#### 1. Agent Lifecycle Management
```python
# Create new specialized agent
agent_id = await create_agent(
    orchestrator_agent_id=orchestrator_uuid,
    name="ai-specialist",
    model="claude-sonnet-4-5-20250929",
    system_prompt="You are an AI specialist for...",
    metadata={
        "template_name": "ai-specialist",
        "ai_capabilities": ["analysis", "optimization"]
    }
)
```

#### 2. Event Logging
```python
# Log AI agent events with context
await insert_agent_log(
    agent_id=agent_uuid,
    task_slug="ai-analysis",
    entry_index=0,
    event_category="request",
    event_type="UserPromptSubmit",
    content="Analyze this data for patterns",
    payload={
        "ai_model": "claude-sonnet-4-5-20250929",
        "context_tokens": 1500,
        "tools_available": ["Read", "Write", "Analyze"]
    }
)
```

#### 3. Performance Monitoring
```python
# Track AI agent performance
await update_agent_costs(
    agent_id=agent_uuid,
    input_tokens=1200,
    output_tokens=800,
    cost_usd=0.0156
)
```

### Best Practices for AI Agents

1. **Use Task Slugs**: Group related events with meaningful task_slug values
2. **Rich Metadata**: Include AI context in JSONB metadata fields
3. **Event Sequencing**: Use entry_index for proper event ordering
4. **Status Updates**: Keep agent status current for orchestration
5. **Cost Tracking**: Monitor token usage for budget optimization

## 📚 Related Documentation

- **Migration System:** `migrations/README.md` - Detailed migration docs
- **Multi-Agent System:** `../orchestrator_3_stream/README.md` - AI orchestration guide
- **Main README:** `../../README.md` - Project overview
- **AI Development:** `../../specs/` - AI development specifications

## 🤝 Contributing to AI-Native Database

### AI-Focused Guidelines

1. **AI-First Design**: Always consider AI agent workflows in schema changes
2. **Metadata Support**: Include JSONB fields for flexible AI context storage
3. **Performance for AI**: Optimize indexes for AI agent query patterns
4. **Event Structure**: Support structured AI event logging
5. **Agent Lifecycle**: Consider full agent lifecycle in table design

### AI Development Workflow

```bash
# 1. Design AI schema changes
vim apps/orchestrator_db/migrations/8_ai_feature.sql

# 2. Update AI models
vim apps/orchestrator_db/models.py

# 3. Sync to AI apps
python apps/orchestrator_db/sync_models.py

# 4. Apply migrations
uv run apps/orchestrator_db/run_migrations.py

# 5. Test with AI agents
cd apps/orchestrator_3_stream
# Test AI workflows with new schema
```

## 🚨 AI-Specific Troubleshooting

### "Agent events not appearing"

**Cause:** Agent not properly logging events or metadata issues.

**Solution:**
```python
# Check agent logs
logs = await get_agent_logs(agent_id=agent_uuid, limit=10)

# Verify event structure
for log in logs:
    print(f"Event: {log.event_type}, Category: {log.event_category}")
```

### "High query latency for agent workflows"

**Cause:** Missing AI-optimized indexes.

**Solution:**
```bash
# Check if AI-specific indexes exist
psql $DATABASE_URL -c "\d agents"
psql $DATABASE_URL -c "\d agent_logs"

# Add AI workflow indexes if missing
```

### "Agent metadata not persisting"

**Cause:** JSONB field issues or model sync problems.

**Solution:**
```bash
# Sync models to ensure latest AI metadata fields
python apps/orchestrator_db/sync_models.py

# Test metadata handling
agent = Agent(metadata={"ai_context": {"version": "1.0"}})
```

## 📊 AI Agent Statistics

- **5 Tables** - Optimized for AI agent workflows
- **36 Indexes** - AI agent query performance optimization
- **2 Triggers** - Auto-update timestamps for agent tracking
- **8 Migrations** - AI-aware schema evolution
- **5 Models** - Type-safe AI agent data structures

---

**Last Updated:** 2025-11-20 (Enhanced for AI Agent Integration)
**Maintainer:** AI-Native Development Team
**AI Optimization**: Full multi-agent orchestration support
