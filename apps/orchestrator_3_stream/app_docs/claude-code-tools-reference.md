# Claude Code Tools Reference

## Overview

Claude Code provides a comprehensive suite of powerful tools for understanding and modifying codebases. Each tool is designed for specific tasks, enabling efficient code analysis, editing, and execution. Tools can be configured via the `/allowed-tools` interface or in `settings.json` for fine-grained control.

---

## Core File Operations

### Read
**Description**: Reads file contents
**Use Case**: Analyzing existing code, understanding context, reviewing files

**Characteristics**:
- Supports various file types (source code, configuration, documentation)
- Preserves formatting and syntax
- Efficient for understanding code structure
- Essential for context building

**Best Practices**:
- Use before making changes to understand existing code
- Read multiple related files to understand system architecture
- Use for documentation review and understanding

**Example Usage**:
```
Read: main.py
Read: src/utils/helpers.js
Read: README.md
```

### Write
**Description**: Creates or overwrites files
**Use Case**: Creating new files, complete rewrites, starting fresh files

**Characteristics**:
- Creates new files if they don't exist
- Overwrites existing content completely
- Preserves formatting and indentation
- Atomic file operations

**Important Notes**:
- Will overwrite existing files without warning
- Must read existing files first before editing (unless intentional overwrite)
- Use with caution for existing project files

**Example Usage**:
```
Write: src/components/Header.js
Write: new_feature.md
```

### Edit
**Description**: Performs exact string replacements in files
**Use Case**: Targeted modifications, bug fixes, feature enhancements

**Characteristics**:
- Precise string-based replacements
- Preserves file structure and formatting
- Multiple replacement options (single or all occurrences)
- Context-aware editing

**Best Practices**:
- Use exact string matching from the file
- Include sufficient context for unique matches
- Read the file first to understand its structure
- Test changes in safe environments

**Example Usage**:
```
Edit: src/app.js
  old_string: "const oldFunction = () => {"
  new_string: "const newFunction = () => {"

Edit: config.py
  old_string: "DEBUG = True"
  new_string: "DEBUG = False"
  replace_all: true
```

---

## File Discovery and Search

### Glob
**Description**: Finds files by pattern matching
**Use Case**: Discovering files by name patterns, finding specific file types

**Characteristics**:
- Unix-style pattern matching (*, ?, [])
- Recursively searches directories
- Returns file paths matching patterns
- Flexible file discovery

**Pattern Examples**:
- `*.js` - All JavaScript files
- `src/**/*.vue` - All Vue files in src directory
- `test_*.py` - All Python test files
- `*.md` - All markdown files

**Example Usage**:
```
Glob: src/**/*.js
Glob: *.config.js
Glob: docs/**/*.md
```

### Grep
**Description**: Searches file contents
**Use Case**: Finding specific code patterns, variable references, function calls

**Characteristics**:
- Searches through file contents
- Supports regular expressions
- Returns file paths and matching lines
- Powerful code analysis tool

**Search Patterns**:
- `import React` - Find React imports
- `function.*validate` - Find validation functions
- `TODO:` - Find TODO comments
- `console.log` - Find debug statements

**Example Usage**:
```
Grep: "useState"
Grep: "class.*Component"
Grep: "TODO:.*fix"
```

---

## Code Execution

### Bash
**Description**: Executes shell commands
**Use Case**: Running build commands, package management, git operations, testing

**Characteristics**:
- Executes shell commands in the current environment
- Supports complex command chaining
- Returns command output and execution status
- Essential for build and deployment tasks

**Safety Considerations**:
- Use with caution for destructive operations
- Test commands in development first
- Avoid commands that modify system files
- Consider security implications

**Common Use Cases**:
- Package management: `npm install`, `pip install`
- Build processes: `npm run build`, `make build`
- Git operations: `git commit`, `git push`
- Testing: `npm test`, `pytest`

**Example Usage**:
```
Bash: npm install
Bash: git add . && git commit -m "feat: add new feature"
Bash: python -m pytest tests/
Bash: docker build -t myapp .
```

---

## Notebook Operations

### NotebookRead
**Description**: Reads Jupyter notebook contents
**Use Case**: Analyzing existing notebooks, understanding data analysis workflows

**Characteristics**:
- Reads Jupyter notebook (.ipynb) files
- Extracts code cells and markdown
- Preserves cell structure and metadata
- Useful for data analysis workflows

**Example Usage**:
```
NotebookRead: analysis.ipynb
NotebookRead: experiments/experiment_1.ipynb
```

### NotebookEdit
**Description**: Modifies Jupyter notebook cells
**Use Case**: Updating notebook code, adding analysis steps, modifying data processing

**Characteristics**:
- Targets specific notebook cells
- Supports code and markdown cells
- Preserves notebook metadata
- Useful for data science workflows

**Example Usage**:
```
NotebookEdit: analysis.ipynb
  cell_index: 3
  old_content: "# Old analysis code"
  new_content: "# Improved analysis code"
```

---

## Workflow and Task Management

### Task
**Description**: Handles multi-step tasks
**Use Case**: Complex workflows, multi-file changes, coordinated operations

**Characteristics**:
- Orchestrates multiple tool calls
- Manages task dependencies
- Provides structured workflows
- Handles error recovery

**Best Practices**:
- Break complex tasks into logical steps
- Handle dependencies between operations
- Include error handling and recovery
- Provide clear progress feedback

**Example Usage**:
```
Task: "Update user authentication flow"
  steps:
    - Read: src/auth/user.js
    - Read: src/auth/middleware.js
    - Edit: src/auth/user.js (implement new validation)
    - Edit: src/auth/middleware.js (update authentication logic)
    - Bash: npm test
```

### TodoWrite
**Description**: Manages task lists
**Use Case**: Tracking progress, managing development workflows, organizing work

**Characteristics**:
- Creates and manages to-do lists
- Tracks task completion
- Provides progress visibility
- Useful for complex projects

**Example Usage**:
```
TodoWrite: "Frontend Refactoring Tasks"
  items:
    - "Migrate to React 18"
    - "Update component styling"
    - "Add TypeScript support"
    - "Optimize bundle size"
```

---

## Web Operations

### WebFetch
**Description**: Fetches content from specified URLs and processes it with AI
**Use Case**: Research, documentation gathering, external resource analysis

**Characteristics**:
- Automatically upgrades HTTP to HTTPS
- Handles redirects transparently
- Processes content with AI models
- Includes 15-minute cache for performance

**Usage Notes**:
- Requires valid URLs
- Processes content with small, fast models
- Returns analyzed summaries
- Handles redirects automatically

**Example Usage**:
```
WebFetch: https://api.example.com/docs
  prompt: "Extract API endpoints and authentication methods"

WebFetch: https://github.com/example/repo
  prompt: "Analyze project structure and main features"
```

### WebSearch
**Description**: Performs filtered web searches
**Use Case**: Research, finding documentation, solving problems, gathering information

**Characteristics**:
- Filtered search results
- Web research capabilities
- Information gathering tool
- Useful for problem-solving

**Example Usage**:
```
WebSearch: "React performance optimization best practices"
WebSearch: "Python async/await tutorial 2024"
```

---

## Custom Operations

### SlashCommand
**Description**: Runs custom commands
**Use Case**: Project-specific workflows, custom automation, team processes

**Characteristics**:
- Executes project-specific commands
- Integrates with team workflows
- Extensible command system
- Custom automation capabilities

**Configuration**:
- Commands defined in project settings
- Can be customized per team or project
- Supports complex multi-step operations

**Example Usage**:
```
SlashCommand: "deploy-staging"
SlashCommand: "run-security-scan"
SlashCommand: "generate-docs"
```

---

## Tool Configuration

### Permission Management

#### Default Permission Mode
- All available tools are accessible
- No restrictions on tool usage
- Suitable for development environments

#### Restricted Permission Mode
- Limited set of allowed tools
- Enhanced security for production environments
- Can be customized per tool

#### Tool Whitelisting
```json
{
  "allowed-tools": ["Read", "Write", "Glob", "Grep", "Bash"]
}
```

### Settings Configuration

#### Via `/allowed-tools` Interface
- Interactive tool configuration
- Real-time permission changes
- Visual feedback on tool status

#### Via settings.json
```json
{
  "allowedTools": ["Read", "Write", "Glob", "Grep", "Bash"],
  "permissionMode": "restricted",
  "tools": {
    "Bash": {
      "allowedCommands": ["npm install", "npm test", "git.*"]
    }
  }
}
```

---

## Best Practices by Tool Category

### File Operations (Read, Write, Edit)
1. **Always read before editing** to understand context
2. **Preserve formatting** and existing code structure
3. **Use exact string matching** for Edit operations
4. **Test changes** in safe environments first
5. **Keep atomic** - make minimal, focused changes

### Search and Discovery (Glob, Grep)
1. **Use specific patterns** to avoid irrelevant results
2. **Combine tools** for comprehensive analysis
3. **Validate findings** by reading relevant files
4. **Document search patterns** for common queries
5. **Use regular expressions** for complex pattern matching

### Code Execution (Bash)
1. **Test commands locally** before execution
2. **Use absolute paths** for reliability
3. **Handle errors** gracefully in workflows
4. **Log output** for debugging purposes
5. **Consider security implications** of commands

### Web Operations (WebFetch, WebSearch)
1. **Validate URLs** before fetching
2. **Use specific prompts** for targeted information extraction
3. **Handle redirects** automatically
4. **Cache results** for performance
5. **Verify information** from multiple sources

### Task Management (Task, TodoWrite)
1. **Break complex tasks** into logical steps
2. **Handle dependencies** between operations
3. **Include error handling** and recovery mechanisms
4. **Track progress** and provide feedback
5. **Document task workflows** for future reference

---

## Common Workflows

### Code Review Workflow
```
1. Read: main.js, src/**/*.js
2. Grep: "TODO:", "FIXME:", "console.log"
3. Bash: npm lint
4. Write: review-report.md
```

### Refactoring Workflow
```
1. Glob: src/**/*.js
2. Read: identified files
3. Edit: refactor code
4. Bash: npm test
5. TodoWrite: refactoring-tasks
```

### Documentation Generation
```
1. Glob: src/**/*.js
2. Read: identified files
3. WebSearch: "best practices for documentation"
4. Write: API-documentation.md
5. WebFetch: external-docs-url
```

### Bug Fix Workflow
```
1. Grep: error patterns
2. Read: relevant files
3. Bash: reproduce error
4. Edit: fix the bug
5. Bash: test the fix
```

---

## Troubleshooting

### Common Tool Issues

#### Permission Denied
- Check allowed-tools configuration
- Verify tool is enabled in settings
- Review permissionMode settings

#### File Not Found
- Use Glob to verify file existence
- Check working directory
- Verify file paths are correct

#### Command Execution Failed
- Test command manually in terminal
- Check command syntax
- Verify environment variables

### Performance Optimization

#### Caching Strategy
- Use WebFetch cache for repeated URL access
- Batch multiple file operations
- Minimize unnecessary tool calls

#### Memory Management
- Use lighter models for simple tasks
- Break large operations into smaller steps
- Clean up temporary files

### Error Handling
```bash
# Example: Safe bash execution
Bash: "command || echo 'Command failed, continuing...'"
```

```bash
# Example: File operation with error handling
Read: config.json || echo "Config not found, using defaults"
```

---

## Tool Integration Patterns

### Chain Operations
```bash
# Example: Code analysis pipeline
Read: src/main.js
Grep: "function.*process"
Glob: src/utils/*.js
Bash: npm analyze
Write: analysis-report.md
```

### Conditional Execution
```bash
# Example: Conditional file processing
Glob: test-*.js
if test files exist:
  Bash: npm test
  Write: test-report.md
else:
  Write: no-tests.md
```

### Parallel Operations
```bash
# Example: Multi-file processing
Task: "Process multiple files"
  steps:
    - Read: file1.js
    - Read: file2.js
    - Read: file3.js
    - Edit: file1.js
    - Edit: file2.js
    - Edit: file3.js
```