# Orchestrator 3 Stream API Documentation

## Overview

The Orchestrator 3 Stream API provides a comprehensive REST and WebSocket interface for managing AI agent orchestration with PostgreSQL backend. The API supports real-time agent lifecycle management, event streaming, cost tracking, and multi-agent workflows.

**Base URL:** `http://localhost:8002` (configurable via `BACKEND_PORT`)
**WebSocket URL:** `ws://localhost:8002/ws`

## Authentication

All API requests are currently open. For production deployment, implement X-Access-Token header authentication:

```bash
curl -H "X-Access-Token: your-api-key" http://localhost:8002/health
```

## API Endpoints

### 1. Health Check

**GET** `/health`

Check the health status of the orchestrator service.

**Response:**
```json
{
  "status": "healthy",
  "service": "orchestrator-3-stream",
  "websocket_connections": 3
}
```

---

### 2. Get Orchestrator Information

**GET** `/get_orchestrator`

Retrieves orchestrator metadata including session ID, costs, available slash commands, and agent templates.

**Response:**
```json
{
  "status": "success",
  "orchestrator": {
    "id": "uuid-string",
    "session_id": "claude-sdk-session-id",
    "status": "idle",
    "working_dir": "/path/to/working/directory",
    "input_tokens": 1250,
    "output_tokens": 850,
    "total_cost": 0.0125,
    "metadata": {
      "system_message_info": {
        "session_id": "current-session-id",
        "cwd": "/path/to/working/directory",
        "tools": ["Bash", "Read", "Write", "Task", "mcp__mgmt__create_agent"],
        "model": "claude-sonnet-4-5-20250929",
        "subtype": "text_content",
        "captured_at": "2025-01-20T15:30:45Z",
        "slash_commands": [...]
      }
    }
  },
  "slash_commands": [
    {
      "name": "test-script",
      "description": "Run test scripts",
      "path": ".claude/commands/test-script.md"
    }
  ],
  "agent_templates": [
    {
      "name": "backend-developer",
      "description": "Backend development specialist",
      "color": "blue",
      "tools": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
    }
  ],
  "orchestrator_tools": [
    "create_agent(name: string, system_prompt?: string, model?: string, subagent_template?: string)",
    "list_agents()",
    "command_agent(agent_name: string, command: string)",
    "check_agent_status(agent_name: string, tail_count = 10, offset = 0, verbose_logs = false)",
    "delete_agent(agent_name: string)",
    "interrupt_agent(agent_name: string)",
    "read_system_logs(offset = 0, limit = 50, message_contains?: string, level?: string)",
    "report_cost()"
  ]
}
```

---

### 3. Send Chat Message

**POST** `/send_chat`

Send a message to the orchestrator agent for processing. Returns immediately with execution happening in the background.

**Request Body:**
```json
{
  "message": "Create a new agent for backend development",
  "orchestrator_agent_id": "uuid-string"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Message received, processing with streaming"
}
```

The actual response is streamed via WebSocket events. See WebSocket Events section for details.

---

### 4. Load Chat History

**POST** `/load_chat`

Retrieve chat history for an orchestrator agent including text blocks, thinking blocks, and tool usage blocks.

**Request Body:**
```json
{
  "orchestrator_agent_id": "uuid-string",
  "limit": 50
}
```

**Response:**
```json
{
  "status": "success",
  "messages": [
    {
      "id": "uuid-string",
      "sender_type": "user",
      "receiver_type": "orchestrator",
      "message": "Hello, create an agent for me",
      "metadata": {},
      "created_at": "2025-01-20T15:30:45Z",
      "updated_at": "2025-01-20T15:30:45Z"
    },
    {
      "id": "uuid-string",
      "sender_type": "orchestrator",
      "receiver_type": "user",
      "message": "",
      "metadata": {
        "type": "thinking",
        "thinking": "I need to create a new agent with appropriate tools..."
      },
      "created_at": "2025-01-20T15:31:00Z",
      "updated_at": "2025-01-20T15:31:00Z"
    }
  ],
  "turn_count": 12
}
```

---

### 5. Get Events

**GET** `/get_events`

Retrieve unified event stream from multiple sources (agent logs, system logs, orchestrator chat).

**Query Parameters:**
- `agent_id` (optional): Filter by specific agent UUID
- `task_slug` (optional): Filter by task identifier
- `event_types` (optional): Comma-separated list of event types. Default: "agent_logs,orchestrator_chat"
- `limit` (optional): Maximum events to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "status": "success",
  "events": [
    {
      "id": "uuid-string",
      "sourceType": "agent_log",
      "agent_id": "uuid-string",
      "agent_name": "backend-dev",
      "task_slug": "create-api-endpoint",
      "entry_index": 0,
      "event_category": "response",
      "event_type": "TextBlock",
      "content": "I'll create the API endpoint...",
      "summary": "Creating API endpoint for user management",
      "payload": {
        "text": "I'll create the API endpoint..."
      },
      "timestamp": "2025-01-20T15:30:45Z"
    },
    {
      "id": "uuid-string",
      "sourceType": "system_log",
      "level": "INFO",
      "message": "Agent created successfully",
      "summary": "Agent creation successful",
      "metadata": {
        "agent_name": "backend-dev",
        "template_used": "backend-developer"
      },
      "timestamp": "2025-01-20T15:31:00Z"
    }
  ],
  "count": 2
}
```

---

### 6. List Agents

**GET** `/list_agents`

Retrieve all active agents for the current orchestrator, enriched with log counts.

**Response:**
```json
{
  "status": "success",
  "agents": [
    {
      "id": "uuid-string",
      "orchestrator_agent_id": "uuid-string",
      "name": "backend-dev",
      "model": "claude-sonnet-4-5-20250929",
      "system_prompt": "You are a backend development specialist...",
      "status": "idle",
      "session_id": "claude-sdk-session-id",
      "input_tokens": 500,
      "output_tokens": 350,
      "total_cost": 0.0085,
      "archived": false,
      "metadata": {
        "template_name": "backend-developer",
        "template_color": "blue"
      },
      "log_count": 15,
      "created_at": "2025-01-20T15:30:45Z",
      "updated_at": "2025-01-20T15:31:00Z"
    }
  ]
}
```

---

### 7. Get Headers

**GET** `/get_headers`

Retrieve header information for the frontend display.

**Response:**
```json
{
  "status": "success",
  "cwd": "/path/to/working/directory"
}
```

---

### 8. Open File in IDE

**POST** `/api/open-file`

Open a file in the configured IDE (Cursor or VS Code).

**Request Body:**
```json
{
  "file_path": "/path/to/file.py"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Opened /path/to/file.py in code",
  "file_path": "/path/to/file.py"
}
```

---

## WebSocket API

### WebSocket Endpoint

**WebSocket URL:** `ws://localhost:8002/ws`

The WebSocket endpoint provides real-time updates for:

- Agent lifecycle events (created, updated, deleted, status changes)
- Agent execution logs (text blocks, thinking blocks, tool usage)
- System logs and errors
- Chat streaming and completion
- Orchestrator metadata updates

### Connection Example

```javascript
// JavaScript
const ws = new WebSocket('ws://localhost:8002/ws');

ws.onopen = () => {
  console.log('Connected to orchestrator');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);

  switch (data.type) {
    case 'agent_created':
      console.log('New agent created:', data.agent);
      break;
    case 'agent_log':
      console.log('Agent log:', data.log);
      break;
    case 'chat_stream':
      console.log('Chat chunk:', data.chunk);
      break;
  }
};
```

### WebSocket Event Types

#### Connection Events

**`connection_established`**
Sent when client connects to WebSocket.

```json
{
  "type": "connection_established",
  "client_id": "client_1",
  "timestamp": "2025-01-20T15:30:45Z",
  "message": "Connected to Orchestrator Backend"
}
```

---

#### Agent Lifecycle Events

**`agent_created`**
Broadcast when a new agent is created.

```json
{
  "type": "agent_created",
  "agent": {
    "id": "uuid-string",
    "name": "backend-dev",
    "model": "claude-sonnet-4-5-20250929",
    "status": "idle"
  },
  "timestamp": "2025-01-20T15:30:45Z"
}
```

**`agent_updated`**
Broadcast when agent data changes (costs, tokens, etc.).

```json
{
  "type": "agent_updated",
  "agent_id": "uuid-string",
  "agent": {
    "input_tokens": 1250,
    "output_tokens": 850,
    "total_cost": 0.0210
  },
  "timestamp": "2025-01-20T15:30:45Z"
}
```

**`agent_deleted`**
Broadcast when an agent is deleted.

```json
{
  "type": "agent_deleted",
  "agent_id": "uuid-string",
  "timestamp": "2025-01-20T15:30:45Z"
}
```

**`agent_status_changed`**
Broadcast when agent status changes.

```json
{
  "type": "agent_status_changed",
  "agent_id": "uuid-string",
  "old_status": "idle",
  "new_status": "executing",
  "timestamp": "2025-01-20T15:30:45Z"
}
```

---

#### Agent Execution Events

**`agent_log`**
Broadcast agent response blocks and activity.

```json
{
  "type": "agent_log",
  "log": {
    "id": "uuid-string",
    "agent_id": "uuid-string",
    "agent_name": "backend-dev",
    "task_slug": "create-api-endpoint",
    "entry_index": 0,
    "event_category": "response",
    "event_type": "TextBlock",
    "content": "I'll create the API endpoint...",
    "summary": "Creating API endpoint for user management",
    "payload": {
      "text": "I'll create the API endpoint..."
    },
    "timestamp": "2025-01-20T15:30:45Z"
  },
  "timestamp": "2025-01-20T15:30:45Z"
}
```

**`thinking_block`**
Broadcast agent thinking blocks.

```json
{
  "type": "thinking_block",
  "data": {
    "id": "uuid-string",
    "orchestrator_agent_id": "uuid-string",
    "thinking": "I need to analyze the requirements and create appropriate endpoints...",
    "timestamp": "2025-01-20T15:30:45Z"
  },
  "timestamp": "2025-01-20T15:30:45Z"
}
```

**`tool_use_block`**
Broadcast agent tool usage.

```json
{
  "type": "tool_use_block",
  "data": {
    "id": "uuid-string",
    "orchestrator_agent_id": "uuid-string",
    "tool_name": "Write",
    "tool_input": {
      "file_path": "/path/to/file.py",
      "content": "..."
    },
    "tool_use_id": "tool-use-id",
    "timestamp": "2025-01-20T15:30:45Z"
  },
  "timestamp": "2025-01-20T15:30:45Z"
}
```

---

#### Orchestrator Events

**`orchestrator_updated`**
Broadcast when orchestrator metadata changes.

```json
{
  "type": "orchestrator_updated",
  "orchestrator": {
    "id": "uuid-string",
    "input_tokens": 2500,
    "output_tokens": 1700,
    "total_cost": 0.0420,
    "updated_at": "2025-01-20T15:30:45Z"
  },
  "timestamp": "2025-01-20T15:30:45Z"
}
```

---

#### Chat Events

**`orchestrator_chat`**
Broadcast chat messages between user, orchestrator, and agents.

```json
{
  "type": "orchestrator_chat",
  "message": {
    "id": "uuid-string",
    "orchestrator_agent_id": "uuid-string",
    "sender_type": "orchestrator",
    "receiver_type": "user",
    "message": "I've created the backend developer agent for you.",
    "agent_id": null,
    "metadata": {},
    "timestamp": "2025-01-20T15:30:45Z"
  },
  "timestamp": "2025-01-20T15:30:45Z"
}
```

**`chat_stream`**
Broadcast streaming chat responses.

```json
{
  "type": "chat_stream",
  "orchestrator_agent_id": "uuid-string",
  "chunk": "I'm creating a new agent for backend development...",
  "is_complete": false,
  "timestamp": "2025-01-20T15:30:45Z"
}
```

---

#### System Events

**`system_log`**
Broadcast system-level log entries.

```json
{
  "type": "system_log",
  "log": {
    "id": "uuid-string",
    "level": "INFO",
    "message": "Agent created successfully",
    "summary": "Agent creation successful",
    "metadata": {
      "agent_name": "backend-dev"
    },
    "timestamp": "2025-01-20T15:30:45Z"
  },
  "timestamp": "2025-01-20T15:30:45Z"
}
```

**`error`**
Broadcast error events.

```json
{
  "type": "error",
  "message": "Failed to create agent",
  "details": {
    "error": "Agent name already exists",
    "suggestion": "Choose a different name"
  },
  "timestamp": "2025-01-20T15:30:45Z"
}
```

---

## MCP Management Tools

The orchestrator provides 8 management tools accessible via MCP server to the orchestrator agent:

### 1. create_agent

Create a new agent with optional template configuration.

**Parameters:**
- `name` (required): Unique agent name
- `system_prompt` (optional): Agent's system prompt (can be empty if using template)
- `model` (optional): Model to use (default: "claude-sonnet-4-5-20250929")
- `subagent_template` (optional): Template name from `.claude/agents/` directory

**Example:**
```bash
# Create agent with custom system prompt
create_agent(
  name="backend-dev",
  system_prompt="You are a backend development specialist...",
  model="sonnet"
)

# Create agent from template
create_agent(
  name="frontend-dev",
  subagent_template="frontend-developer"
)
```

**Response:**
```
✅ Created agent 'backend-dev'
ID: 123e4567-e89b-12d3-a456-426614174000
Session: session_abc123
Model: claude-sonnet-4-5-20250929
```

---

### 2. list_agents

List all active agents with their status and statistics.

**Parameters:** None

**Example:**
```bash
list_agents()
```

**Response:**
```
📋 Active Agents:

• backend-dev (ID: 123e4567-e89b-12d3-a456-426614174000)
  Status: idle
  Model: claude-sonnet-4-5-20250929
  Tokens: 850
  Cost: $0.0085
```

---

### 3. command_agent

Send a command to an agent for execution in background.

**Parameters:**
- `agent_name` (required): Name of agent to command
- `command` (required): Command text for the agent

**Example:**
```bash
command_agent(
  agent_name="backend-dev",
  command="Create a REST API endpoint for user management with CRUD operations"
)
```

**Response:**
```
✅ Command dispatched to 'backend-dev'
Command: Create a REST API endpoint for user management with CRUD operations
Agent will execute in background.
```

---

### 4. check_agent_status

Check agent status and recent activity.

**Parameters:**
- `agent_name` (required): Name of agent
- `tail_count` (optional, default: 10): Number of recent entries to show
- `offset` (optional, default: 0): Offset for pagination
- `verbose_logs` (optional, default: false): Show full logs vs summaries

**Example:**
```bash
check_agent_status(
  agent_name="backend-dev",
  tail_count=5,
  verbose_logs=true
)
```

**Response:**
```
📊 Agent Status: backend-dev
Status: idle
Model: claude-sonnet-4-5-20250929
Tokens: 1250
Cost: $0.0125

🔍 Recent Activity (Task: create-api-endpoint):

• [UserPromptSubmit] Create a REST API endpoint for user management
  Payload: {"author": "orchestrator_agent", "prompt": "..."}
• [TextBlock] I'll create a comprehensive REST API...
  Payload: {"text": "I'll create a comprehensive REST API..."}
```

---

### 5. delete_agent

Delete an agent and clean up resources.

**Parameters:**
- `agent_name` (required): Name of agent to delete

**Example:**
```bash
delete_agent(agent_name="backend-dev")
```

**Response:**
```
✅ Deleted agent 'backend-dev'
```

---

### 6. interrupt_agent

Interrupt a running agent.

**Parameters:**
- `agent_name` (required): Name of agent to interrupt

**Example:**
```bash
interrupt_agent(agent_name="backend-dev")
```

**Response:**
```
✅ Interrupted agent 'backend-dev'
```

---

### 7. read_system_logs

Read recent system logs with filtering options.

**Parameters:**
- `offset` (optional, default: 0): Starting offset
- `limit` (optional, default: 50): Maximum entries to return
- `message_contains` (optional): Filter by message content
- `level` (optional): Filter by log level (DEBUG, INFO, WARNING, ERROR)

**Example:**
```bash
read_system_logs(
  limit=25,
  level="WARNING",
  message_contains="agent"
)
```

**Response:**
```
📋 System Logs (showing 2 of max 25):

[2025-01-20T15:30:45Z] WARNING: Agent creation timeout for frontend-dev
[2025-01-20T15:30:45Z] WARNING: Agent memory usage high for backend-dev
```

---

### 8. report_cost

Report orchestrator costs, tokens, and session information.

**Parameters:** None

**Example:**
```bash
report_cost()
```

**Response:**
```
💰 Orchestrator Cost Report:

Session ID: session_abc123
Status: idle

Total Cost: $0.0420
Input Tokens: 2,500
Output Tokens: 1,700
Total Tokens: 4,200
Context Usage: 2.1%
```

---

## Database Schema

The system uses PostgreSQL with the following main tables:

### orchestrator_agents

Singleton table for the main orchestrator agent.

```sql
CREATE TABLE orchestrator_agents (
    id UUID PRIMARY KEY,
    session_id TEXT,
    system_prompt TEXT,
    status TEXT,
    working_dir TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10,6) DEFAULT 0.0,
    archived BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### agents

Registry for managed agents.

```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    orchestrator_agent_id UUID REFERENCES orchestrator_agents(id),
    name TEXT NOT NULL,
    model TEXT NOT NULL,
    system_prompt TEXT,
    working_dir TEXT,
    git_worktree TEXT,
    status TEXT,
    session_id TEXT,
    adw_id TEXT,
    adw_step TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10,6) DEFAULT 0.0,
    archived BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### agent_logs

Unified event log for agent execution and hooks.

```sql
CREATE TABLE agent_logs (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    session_id TEXT,
    task_slug TEXT,
    adw_id TEXT,
    adw_step TEXT,
    entry_index INTEGER,
    event_category TEXT,
    event_type TEXT,
    content TEXT,
    payload JSONB DEFAULT '{}',
    summary TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### system_logs

Application-level system logs.

```sql
CREATE TABLE system_logs (
    id UUID PRIMARY KEY,
    file_path TEXT,
    adw_id TEXT,
    adw_step TEXT,
    level TEXT,
    message TEXT,
    summary TEXT,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### orchestrator_chat

Append-only conversation log capturing 3-way communication.

```sql
CREATE TABLE orchestrator_chat (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    orchestrator_agent_id UUID REFERENCES orchestrator_agents(id),
    sender_type TEXT,
    receiver_type TEXT,
    message TEXT,
    summary TEXT,
    agent_id UUID REFERENCES agents(id),
    metadata JSONB DEFAULT '{}'
);
```

### prompts

Prompts sent to agents from engineers or orchestrator.

```sql
CREATE TABLE prompts (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    task_slug TEXT,
    author TEXT,
    prompt_text TEXT,
    summary TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id TEXT
);
```

---

## Integration Examples

### Python Example

```python
import asyncio
import aiohttp
import json
import websockets

async def main():
    # REST API calls
    async with aiohttp.ClientSession() as session:
        # Get orchestrator info
        async with session.get('http://localhost:8002/get_orchestrator') as resp:
            data = await resp.json()
            orchestrator_id = data['orchestrator']['id']

        # Send chat message
        chat_data = {
            'message': 'Create a new agent for backend development',
            'orchestrator_agent_id': orchestrator_id
        }
        async with session.post('http://localhost:8002/send_chat', json=chat_data) as resp:
            print(await resp.json())

    # WebSocket connection for real-time updates
    async with websockets.connect('ws://localhost:8002/ws') as ws:
        async for message in ws:
            data = json.loads(message)
            print(f"Received: {data['type']}")

asyncio.run(main())
```

### JavaScript Example

```javascript
class OrchestratorClient {
    constructor(baseUrl = 'http://localhost:8002') {
        this.baseUrl = baseUrl;
        this.ws = null;
        this.eventHandlers = {};
    }

    async connect() {
        // Connect WebSocket
        this.ws = new WebSocket(`${this.baseUrl.replace('http', 'ws')}/ws`);

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleEvent(data);
        };

        return new Promise((resolve) => {
            this.ws.onopen = resolve;
        });
    }

    async getOrchestrator() {
        const response = await fetch(`${this.baseUrl}/get_orchestrator`);
        return await response.json();
    }

    async sendChat(message, orchestratorId) {
        const response = await fetch(`${this.baseUrl}/send_chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                orchestrator_agent_id: orchestratorId
            })
        });
        return await response.json();
    }

    on(eventType, handler) {
        this.eventHandlers[eventType] = handler;
    }

    handleEvent(data) {
        const handler = this.eventHandlers[data.type];
        if (handler) {
            handler(data);
        }
    }
}

// Usage
const client = new OrchestratorClient();

client.on('agent_created', (data) => {
    console.log('New agent:', data.agent);
});

client.on('chat_stream', (data) => {
    console.log('Chat chunk:', data.chunk);
});

await client.connect();
const orchestrator = await client.getOrchestrator();
await client.sendChat('Hello orchestrator', orchestrator.orchestrator.id);
```

### cURL Examples

```bash
# Health check
curl http://localhost:8002/health

# Get orchestrator info
curl http://localhost:8002/get_orchestrator

# Send chat message
curl -X POST http://localhost:8002/send_chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a new agent",
    "orchestrator_agent_id": "123e4567-e89b-12d3-a456-426614174000"
  }'

# Load chat history
curl -X POST http://localhost:8002/load_chat \
  -H "Content-Type: application/json" \
  -d '{
    "orchestrator_agent_id": "123e4567-e89b-12d3-a456-426614174000",
    "limit": 20
  }'

# Get events
curl "http://localhost:8002/get_events?event_types=agent_logs,system_logs&limit=25"

# List agents
curl http://localhost:8002/list_agents
```

---

## Error Handling

### HTTP Error Responses

The API returns appropriate HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

### WebSocket Error Events

The WebSocket may broadcast error events:
```json
{
  "type": "error",
  "message": "Failed to create agent",
  "details": {
    "error": "Agent name already exists",
    "suggestion": "Choose a different name"
  },
  "timestamp": "2025-01-20T15:30:45Z"
}
```

---

## Configuration

### Environment Variables

The backend is configured via environment variables in `.env` file:

```bash
# Server Configuration
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8002
FRONTEND_HOST=127.0.0.1
FRONTEND_PORT=5175

# Database
DATABASE_URL=postgresql://user:pass@host:port/database
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# CORS
CORS_ORIGINS=http://localhost:5175

# Logging
LOG_LEVEL=INFO
LOG_DIR=backend/logs

# Models
ORCHESTRATOR_MODEL=claude-sonnet-4-5-20250929
DEFAULT_AGENT_MODEL=claude-sonnet-4-5-20250929

# Paths
ORCHESTRATOR_WORKING_DIR=/path/to/codebase
ORCHESTRATOR_SYSTEM_PROMPT_PATH=backend/prompts/orchestrator_agent_system_prompt.md

# Agent Limits
MAX_AGENT_TURNS=500

# Query Limits
DEFAULT_AGENT_LOG_LIMIT=50
DEFAULT_SYSTEM_LOG_LIMIT=50
DEFAULT_CHAT_HISTORY_LIMIT=300

# IDE Integration
IDE_COMMAND=code
IDE_ENABLED=true
```

---

## Rate Limiting

Currently no rate limiting is implemented. For production deployment, consider implementing:

- Request rate limiting per client IP
- Concurrent agent execution limits
- Cost limits per session
- Token usage limits

---

## WebSocket Connection Management

- Connections are automatically cleaned up when clients disconnect
- Failed WebSocket sends result in client disconnection
- Server broadcasts to all connected clients by default
- Connection metadata is tracked for debugging

## File Tracking

The system automatically tracks file operations performed by agents:

- Modified files are tracked and summarized
- Read files are monitored
- File change summaries are attached to text blocks
- Real-time file tracking events are broadcast via WebSocket

## AI Summarization

The system uses AI summarization (Claude Haiku) for:

- Chat messages and prompts
- Agent execution logs
- System logs
- File change summaries

Summaries help with:
- Quick scanning of long conversations
- Performance optimization of event streams
- Better search and filtering capabilities

## Subagent Templates

The system supports subagent templates in `.claude/agents/` directory:

- Templates provide predefined agent configurations
- Includes system prompts, tools, and model settings
- Color coding for visual organization
- Automatic template discovery and loading

## Security Considerations

For production deployment:

1. **Authentication**: Implement X-Access-Token or JWT authentication
2. **CORS**: Configure appropriate CORS origins
3. **Database**: Use connection pooling and SSL
4. **WebSocket**: Implement connection rate limiting
5. **File Access**: Restrict agent file access to working directories
6. **API Keys**: Secure management of Anthropic API keys

## Monitoring and Observability

### Logging

- Hourly rotating log files in `backend/logs/`
- Rich console logging for development
- Structured JSON logging for production
- WebSocket event logging
- HTTP request logging

### Metrics

- WebSocket connection count (health endpoint)
- Agent execution statistics
- Token usage and cost tracking
- Database query performance
- File operation tracking

### Database Queries

The system uses efficient database queries with:

- Connection pooling
- Proper indexing on UUID columns
- Pagination for large datasets
- JSONB operations for metadata
- Asynchronous query execution

---

This documentation provides a comprehensive reference for building integrations with the Orchestrator 3 Stream API. For questions or specific integration needs, refer to the source code or contact the development team.