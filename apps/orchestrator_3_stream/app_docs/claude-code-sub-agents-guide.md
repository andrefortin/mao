# Claude Code Sub-Agents Documentation

## Overview

Sub-agents are pre-configured AI assistants that Claude Code can delegate tasks to. Each sub-agent has a specific purpose, separate context window, configured tools, and custom system prompts. They enable context preservation, specialized expertise, reusability, and flexible tool access management.

## Key Benefits

### Context Preservation
- Prevents pollution of the main conversation
- Maintains separate context windows for different tasks
- Allows focused work without interference

### Specialized Expertise
- Fine-tuned with detailed instructions for specific domains
- Can be optimized for particular programming languages or frameworks
- Provide consistent, domain-specific responses

### Reusability
- Can be used across different projects
- Shareable with team members
- Reduce repetitive setup work

### Flexible Permissions
- Different tool access levels based on agent requirements
- Can restrict or enable specific tools as needed
- Granular control over agent capabilities

---

## Quick Start

### Creating a Sub-Agent

1. **Open the agents interface**: Navigate to `/agents`
2. **Select "Create New Agent"** from the interface
3. **Define the sub-agent**:
   - Set a clear purpose and description
   - Configure appropriate tools
   - Write a detailed system prompt
4. **Save the agent** and use automatically or via explicit invocation

### Basic Example

```markdown
---
name: python-debugger
description: Debug Python code issues and provide solutions
tools: Read, Write, Bash
model: sonnet
permissionMode: default
skills: python, debugging, troubleshooting
---

You are an expert Python debugger. Your role is to analyze Python code, identify bugs, and provide comprehensive solutions.

When debugging:
1. First read the relevant code files to understand the context
2. Use Bash to run diagnostic commands if needed
3. Provide clear explanations of the issues
4. Suggest specific fixes with explanations
5. Only make changes when explicitly requested

Focus on:
- Syntax errors and exceptions
- Logic bugs and edge cases
- Performance optimization
- Code readability improvements
- Best practices adherence
```

---

## Configuration Format

### Frontmatter Requirements

```markdown
---
name: sub-agent-name              # Required: Unique identifier
description: When this subagent should be invoked  # Required: Clear purpose
tools: tool1, tool2              # Optional: Comma-separated list; inherits all if omitted
model: sonnet                     # Optional: Model selection; defaults to configured model
permissionMode: default          # Optional: Permission configuration
skills: skill1, skill2           # Optional: Skill categorization
---

System prompt content...
```

### Frontmatter Fields

#### Required Fields
- **`name`**: Unique identifier for the sub-agent
- **`description`**: Clear explanation of when and how to use the sub-agent

#### Optional Fields
- **`tools`**: Comma-separated list of allowed tools. If omitted, inherits all available tools
- **`model`**: Model selection (e.g., `sonnet`, `haiku`). Defaults to the configured model
- **`permissionMode`**: Permission configuration (`default`, `restricted`, etc.)
- **`skills`**: Comma-separated skill categorization for better organization

---

## File Locations and Priority

### Project-Level Agents (Highest Priority)
- Location: `.claude/agents/`
- Purpose: Project-specific configurations
- Override behavior: Takes precedence over user-level agents

### User-Level Agents (Lower Priority)
- Location: `~/.claude/agents/`
- Purpose: Personal configurations across projects
- Override behavior: Used when no project-level agent exists

### CLI Agents (Dynamic)
- Location: Specified via `--agents` flag
- Purpose: One-time or temporary configurations
- Override behavior: Highest priority when used

---

## Best Practices

### Agent Design Principles

#### 1. Generate with Claude First
- Start by generating agent configurations with Claude's help
- Use Claude's understanding of your project requirements
- Customize based on specific needs

#### 2. Single Responsibility Focus
- Create agents with clear, single purposes
- Avoid trying to make agents do too many things
- Specialized agents are more effective than general ones

#### 3. Detailed System Prompts
- Write comprehensive, specific instructions
- Include examples of desired behavior
- Define boundaries and limitations clearly
- Specify file handling preferences
- Define output format requirements

#### 4. Minimal Tool Access
- Only enable tools necessary for the agent's purpose
- Reduce security risks by limiting tool access
- Start with minimal permissions and add as needed

#### 5. Version Control
- Include project-specific agents in version control
- Track changes to agent configurations
- Maintain documentation for agent purposes

### Prompt Engineering Guidelines

#### Role Definition
```
You are [specific role] with expertise in [domain].
Your primary responsibilities include:
- [specific task 1]
- [specific task 2]
- [specific task 3]

You should NOT:
- [unwanted behavior 1]
- [unwanted behavior 2]
```

#### Working Methods
```
When working on tasks:
1. [step-by-step approach]
2. [consideration points]
3. [output format]
```

#### Examples and Boundaries
```
Examples:
- [example of desired behavior]
- [example of unwanted behavior]

Boundaries:
- [clear limits on scope]
- [types of tasks to reject]
```

---

## Built-in Sub-Agents

### Plan Sub-Agent
- **Purpose**: Used during plan mode for codebase research
- **Model**: Uses Sonnet model
- **Tools**: Read, Glob, Grep, Bash
- **Function**: Assists with research and planning tasks

---

## Advanced Features

### Chaining Sub-Agents
- Combine multiple agents for complex workflows
- Each agent handles a specific part of the process
- Enable sequential task delegation

#### Example: Code Review Workflow
1. **Code Analyzer Agent**: Reads and analyzes code structure
2. **Bug Detector Agent**: Identifies potential issues
3. **Performance Optimizer Agent**: Suggests improvements
4. **Documentation Agent**: Generates documentation

### Resumable Sub-Agents
- Each sub-agent has a unique agent ID
- Can resume previous conversations
- Maintain context across sessions

### Plugin-Provided Agents
- Available through the `/agents` interface
- Can be discovered and installed
- Update automatically from trusted sources

---

## Usage Examples

### 1. Frontend Development Agent
```markdown
---
name: frontend-specialist
description: Frontend development tasks including React, Vue, and CSS
tools: Read, Write, Bash, Glob, Grep
model: sonnet
skills: react, vue, javascript, css, html
---

You are an expert frontend developer specializing in modern JavaScript frameworks.

Your capabilities include:
- React component development and optimization
- Vue.js application architecture
- CSS/SCSS styling and responsive design
- HTML5 semantic markup
- Performance optimization techniques
- Accessibility improvements

When working on frontend tasks:
1. First analyze existing codebase structure
2. Follow project coding standards and patterns
3. Ensure responsive design principles
4. Optimize for performance and accessibility
5. Provide explanations for your decisions
```

### 2. Database Migration Agent
```markdown
---
name: database-migrator
description: Database migration and schema management
tools: Read, Write, Bash, Grep, Glob
model: haiku
skills: sql, postgres, migrations, database
---

You are an expert database migration specialist focused on schema evolution and data integrity.

Your responsibilities include:
- Designing database schemas
- Creating migration files
- Optimizing query performance
- Ensuring data consistency
- Managing database relationships

Migration workflow:
1. Analyze existing schema and requirements
2. Create migration files with clear descriptions
3. Generate rollback strategies
4. Test migrations on development environment
5. Provide clear documentation of changes
```

### 3. Testing Agent
```markdown
---
name: qa-engineer
description: Software testing and quality assurance
tools: Read, Write, Bash, Glob, Grep
model: sonnet
skills: testing, pytest, quality-assurance, automation
---

You are a dedicated Quality Assurance engineer focused on comprehensive testing strategies.

Your expertise covers:
- Unit testing frameworks
- Integration testing
- End-to-end testing
- Performance testing
- Security testing
- Test-driven development

When creating tests:
1. Understand business requirements and use cases
2. Create comprehensive test scenarios
3. Follow testing best practices
4. Ensure good test coverage
5. Document test cases and expected results
```

---

## Troubleshooting

### Common Issues

#### Agent Not Being Invoked
- Check that description clearly defines when to use the agent
- Ensure the frontmatter is properly formatted
- Verify that the agent's purpose matches your current task

#### Tool Access Problems
- Review the `tools` field in frontmatter
- Check if required tools are available in the environment
- Adjust permissionMode as needed

#### Performance Issues
- Consider using a lighter model (haiku) for simpler tasks
- Break complex tasks into smaller, focused agents
- Review prompt length and complexity

### Debugging Tips
- Use simpler agents first to isolate issues
- Check the agent's response patterns
- Verify tool execution permissions
- Review system prompt clarity and specificity