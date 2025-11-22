---
description: Clone, setup, and manage GitHub repositories with proper configuration
argument-hint: [repo-url] [local-dir] [setup-type]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, MultiEdit
---

# Git Repo

Clone, setup, and manage GitHub repositories with proper configuration and development environment. This command handles repository cloning, environment setup, and maintenance tasks.

## Variables

REPO_URL: $1  (GitHub repository URL)
LOCAL_DIR: $2  (local directory name, defaults to repo name)
SETUP_TYPE: $3  (development, production, minimal, custom)

## Instructions

- IMPORTANT: If no `REPO_URL` is provided, stop and ask for it.
- IMPORTANT: Validate REPO_URL is a valid GitHub repository
- Use repo name from URL if LOCAL_DIR not provided
- Set SETUP_TYPE to development if not provided
- Configure repository with proper Git settings
- Set up development environment based on repository type
- Handle authentication and permissions

## Workflow

1. Validate Repository - Check REPO_URL validity and accessibility
2. Clone Repository - Clone with proper settings and configuration
3. Setup Environment - Configure development environment based on type
4. Install Dependencies - Set up package management and dependencies
5. Configure Git - Set up proper Git configuration and hooks
6. Initialize Development - Create development scripts and tools
7. Repository Maintenance - Set up maintenance and monitoring

## Error Handling

- If repository is not accessible, provide authentication guidance
- If clone fails due to permissions, provide setup instructions
- If dependencies installation fails, provide alternative approaches
- If Git configuration fails, provide manual setup steps
- Always clean up partial setups on failure

## Setup Types

### Development (default)
- Full development environment setup
- Install all dependencies including dev dependencies
- Set up pre-commit hooks and linting
- Create development scripts and tools
- Configure IDE settings if applicable

### Production
- Production-ready setup
- Install only production dependencies
- Set up environment variables and configuration
- Create deployment scripts
- Configure monitoring and logging

### Minimal
- Basic clone and setup only
- Install essential dependencies
- Basic Git configuration
- No additional development tools

### Custom
- Interactive setup with user choices
- Choose which components to install
- Custom configuration options
- Selective tool installation

## Implementation Steps

### 1. Repository Validation
```bash
# Validate repository URL
if [ -z "$REPO_URL" ]; then
    echo "❌ Error: Repository URL is required"
    echo "Usage: /git-repo https://github.com/user/repo [local-dir] [setup-type]"
    echo "Example: /git-repo https://github.com/andrefortin/my-project my-project dev"
    exit 1
fi

# Extract GitHub username and repo name
if [[ "$REPO_URL" =~ ^https://github\.com/([^/]+)/([^/\.]+)(\.git)?$ ]]; then
    GITHUB_USER="${BASH_REMATCH[1]}"
    REPO_NAME="${BASH_REMATCH[2]}"
elif [[ "$REPO_URL" =~ ^git@github\.com:([^/]+)/([^/\.]+)(\.git)?$ ]]; then
    GITHUB_USER="${BASH_REMATCH[1]}"
    REPO_NAME="${BASH_REMATCH[2]}"
else
    echo "❌ Error: Invalid GitHub repository URL"
    echo "Expected format: https://github.com/user/repo or git@github.com:user/repo"
    exit 1
fi

# Set local directory if not provided
if [ -z "$LOCAL_DIR" ]; then
    LOCAL_DIR="$REPO_NAME"
fi

# Set default setup type if not provided
if [ -z "$SETUP_TYPE" ]; then
    SETUP_TYPE="development"
fi

# Validate setup type
case "$SETUP_TYPE" in
    "development"|"production"|"minimal"|"custom")
        ;;
    *)
        echo "❌ Error: Invalid setup type. Use: development, production, minimal, or custom"
        exit 1
        ;;
esac

# Check if local directory already exists
if [ -d "$LOCAL_DIR" ]; then
    echo "❌ Error: Directory '$LOCAL_DIR' already exists"
    echo "Choose a different local directory name or remove the existing directory"
    exit 1
fi

echo "🔍 Repository Analysis:"
echo "  URL: $REPO_URL"
echo "  User: $GITHUB_USER"
echo "  Repository: $REPO_NAME"
echo "  Local Directory: $LOCAL_DIR"
echo "  Setup Type: $SETUP_TYPE"
```

### 2. Accessibility Check
```bash
echo "🔗 Checking repository accessibility..."

# Check if GitHub CLI is available
if command -v gh &> /dev/null; then
    # Use GitHub CLI to check repository
    if gh repo view "$GITHUB_USER/$REPO_NAME" &> /dev/null; then
        echo "✅ Repository accessible via GitHub CLI"

        # Get repository information
        REPO_INFO=$(gh repo view "$GITHUB_USER/$REPO_NAME" --json name,description,primaryLanguage,visibility,isPrivate)
        echo "📋 Repository Info:"
        echo "$REPO_INFO" | jq -r '"  - Name: \(.name)"'
        echo "$REPO_INFO" | jq -r '"  - Language: \(.primaryLanguage.name // "Unknown")"'
        echo "$REPO_INFO" | jq -r '"  - Visibility: \(.visibility)"'
    else
        echo "❌ Repository not accessible via GitHub CLI"
        echo "Check authentication: gh auth status"
        exit 1
    fi
else
    echo "⚠️  GitHub CLI not found, checking via git..."

    # Check via git ls-remote
    if git ls-remote "$REPO_URL" &> /dev/null; then
        echo "✅ Repository accessible via git"
    else
        echo "❌ Repository not accessible"
        echo "Check:"
        echo "  - Repository URL is correct"
        echo "  - You have permission to access the repository"
        echo "  - Network connectivity"
        exit 1
    fi
fi
```

### 3. Clone Repository
```bash
echo "📥 Cloning repository..."

# Create clone command based on setup type
CLONE_CMD="git clone"

case "$SETUP_TYPE" in
    "production")
        CLONE_CMD="$CLONE_CMD --depth 1 --single-branch"
        echo "  Using shallow clone for production setup"
        ;;
    "minimal")
        CLONE_CMD="$CLONE_CMD --depth 1"
        echo "  Using shallow clone for minimal setup"
        ;;
    *)
        echo "  Using full clone for development setup"
        ;;
esac

# Execute clone
if $CLONE_CMD "$REPO_URL" "$LOCAL_DIR"; then
    echo "✅ Repository cloned successfully"
    cd "$LOCAL_DIR"
else
    echo "❌ Failed to clone repository"
    exit 1
fi

# Set up remote tracking
git remote set-url origin "$REPO_URL"
git fetch origin

echo "📁 Working directory: $(pwd)"
```

### 4. Environment Analysis and Setup
```bash
echo "🔍 Analyzing repository structure..."

# Detect project type
PROJECT_TYPE="unknown"
if [ -f "package.json" ]; then
    PROJECT_TYPE="node"
elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
    PROJECT_TYPE="python"
elif [ -f "Cargo.toml" ]; then
    PROJECT_TYPE="rust"
elif [ -f "go.mod" ]; then
    PROJECT_TYPE="go"
elif [ -f "pom.xml" ]; then
    PROJECT_TYPE="java"
elif [ -f "composer.json" ]; then
    PROJECT_TYPE="php"
elif [ -f "Gemfile" ]; then
    PROJECT_TYPE="ruby"
elif [ -f "Dockerfile" ] || [ -f "docker-compose.yml" ]; then
    PROJECT_TYPE="docker"
fi

echo "  Detected project type: $PROJECT_TYPE"

# Analyze repository features
FEATURES=()
[ -f "Dockerfile" ] && FEATURES+=("docker")
[ -f "docker-compose.yml" ] && FEATURES+=("docker-compose")
[ -d ".github/workflows" ] && FEATURES+=("github-actions")
[ -f "Makefile" ] && FEATURES+=("make")
[ -f "justfile" ] && FEATURES+=("just")
[ -d "tests" ] || [ -d "test" ] || [ -d "__tests__" ] && FEATURES+=("tests")
[ -f ".gitignore" ] && FEATURES+=("gitignore")
[ -f "README.md" ] && FEATURES+=("readme")

echo "  Detected features: ${FEATURES[*]}"

# Create setup report
cat > "REPO_SETUP_REPORT.md" << EOF
# Repository Setup Report

## Repository Information
- **URL**: $REPO_URL
- **User**: $GITHUB_USER
- **Name**: $REPO_NAME
- **Local Directory**: $LOCAL_DIR
- **Setup Type**: $SETUP_TYPE
- **Setup Date**: $(date)

## Repository Analysis
- **Project Type**: $PROJECT_TYPE
- **Detected Features**: ${FEATURES[*]}
- **Git Branch**: $(git branch --show-current)
- **Last Commit**: $(git log -1 --format="%h - %s (%cr)")

## Setup Configuration
- **Git User**: $(git config user.name || "Not configured")
- **Git Email**: $(git config user.email || "Not configured")
- **Remote Origin**: $(git remote get-url origin)

## Dependencies Status
[To be filled after dependency installation]

## Development Tools
[To be filled after tool installation]

## Next Steps
[Custom next steps based on project type]
EOF
```

### 5. Dependency Installation
```bash
echo "📦 Installing dependencies..."

install_dependencies() {
    case "$PROJECT_TYPE" in
        "node")
            if [ "$SETUP_TYPE" = "production" ]; then
                if command -v npm &> /dev/null; then
                    npm ci --only=production
                elif command -v yarn &> /dev/null; then
                    yarn install --production
                fi
            else
                if command -v npm &> /dev/null; then
                    npm install
                elif command -v yarn &> /dev/null; then
                    yarn install
                fi
            fi
            ;;

        "python")
            if command -v uv &> /dev/null; then
                if [ "$SETUP_TYPE" = "production" ]; then
                    uv venv
                    source .venv/bin/activate
                    uv pip install -r requirements.txt 2>/dev/null || true
                else
                    uv venv
                    source .venv/bin/activate
                    uv pip install -e ".[dev]" 2>/dev/null || uv pip install -e .
                fi
            elif command -v python3 &> /dev/null; then
                python3 -m venv .venv
                source .venv/bin/activate
                pip install --upgrade pip

                if [ -f "requirements.txt" ]; then
                    pip install -r requirements.txt
                elif [ -f "pyproject.toml" ]; then
                    pip install -e ".[dev]"
                fi
            fi
            ;;

        "rust")
            if command -v cargo &> /dev/null; then
                cargo build
                if [ "$SETUP_TYPE" != "production" ]; then
                    cargo build
                fi
            fi
            ;;

        "go")
            if command -v go &> /dev/null; then
                go mod download
                go build ./...
            fi
            ;;
    esac
}

# Execute dependency installation
if install_dependencies; then
    echo "✅ Dependencies installed successfully"

    # Update setup report
    sed -i '/## Dependencies Status/,/## Development Tools/c\
## Dependencies Status\
✅ Dependencies installed successfully\
- Project type: '$PROJECT_TYPE'\
- Setup type: '$SETUP_TYPE'' REPO_SETUP_REPORT.md
else
    echo "⚠️  Dependency installation failed or not applicable"

    # Update setup report
    sed -i '/## Dependencies Status/,/## Development Tools/c\
## Dependencies Status\
⚠️ Dependency installation failed or not applicable\
- Project type: '$PROJECT_TYPE'\
- Setup type: '$SETUP_TYPE'' REPO_SETUP_REPORT.md
fi
```

### 6. Development Tools Setup
```bash
if [ "$SETUP_TYPE" = "development" ] || [ "$SETUP_TYPE" = "custom" ]; then
    echo "🛠️  Setting up development tools..."

    TOOLS_INSTALLED=()

    # Git hooks
    if [ -d ".git/hooks" ]; then
        # Set up pre-commit hook
        cat > ".git/hooks/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit hook

echo "🔍 Running pre-commit checks..."

# Run tests if available
if [ -f "package.json" ] && command -v npm &> /dev/null; then
    npm test 2>/dev/null || echo "⚠️  Tests failed or not available"
elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    if command -v pytest &> /dev/null; then
        pytest tests/ -q 2>/dev/null || echo "⚠️  Tests failed or not available"
    fi
fi

# Run linter if available
if [ -f ".eslintrc.js" ] || [ -f ".eslintrc.json" ]; then
    npx eslint . 2>/dev/null || echo "⚠️  ESLint issues found"
elif [ -f "pyproject.toml" ] && grep -q "flake8\|black\|ruff" pyproject.toml; then
    ruff check . 2>/dev/null || echo "⚠️  Code style issues found"
fi

echo "✅ Pre-commit checks completed"
EOF
        chmod +x ".git/hooks/pre-commit"
        TOOLS_INSTALLED+=("pre-commit-hook")
    fi

    # Environment variables
    if [ ! -f ".env" ] && [ -f ".env.sample" ]; then
        cp .env.sample .env
        echo "✅ Created .env from .env.sample"
        echo "⚠️  Please update .env with your configuration"
        TOOLS_INSTALLED+=("env-file")
    fi

    # Development scripts
    cat > "dev-helper.sh" << 'EOF'
#!/bin/bash

# Development Helper Script

PROJECT_NAME=$(basename "$(pwd)")
BRANCH_NAME=$(git branch --show-current 2>/dev/null || echo "detached")

dev_status() {
    echo "📋 Development Status: $PROJECT_NAME"
    echo "📍 Current Branch: $BRANCH_NAME"
    echo "📁 Working Directory: $(pwd)"
    echo "🔧 Modified Files: $(git status --porcelain | wc -l)"
    echo "📦 Uncommitted Changes: $(git diff --name-only | wc -l)"
}

dev_clean() {
    echo "🧹 Cleaning development environment..."

    # Clean dependencies
    if [ -f "package.json" ]; then
        rm -rf node_modules package-lock.json
        echo "  Cleaned Node.js dependencies"
    elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
        rm -rf .venv __pycache__ *.pyc
        echo "  Cleaned Python environment"
    fi

    # Clean git
    git clean -fd 2>/dev/null || echo "  Git clean completed"
    git reset --hard HEAD 2>/dev/null || echo "  Git reset completed"

    echo "✅ Development environment cleaned"
}

dev_test() {
    echo "🧪 Running tests..."

    if [ -f "package.json" ]; then
        npm test
    elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        fi
        python -m pytest tests/ -v
    else
        echo "⚠️  No test framework detected"
    fi
}

dev_update() {
    echo "🔄 Updating dependencies..."

    if [ -f "package.json" ]; then
        npm update
        echo "✅ Node.js dependencies updated"
    elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
        if command -v uv &> /dev/null; then
            uv pip install --upgrade -e .
        else
            pip install --upgrade -e .
        fi
        echo "✅ Python dependencies updated"
    else
        echo "⚠️  No package manager detected"
    fi
}

case "$1" in
    "status")
        dev_status
        ;;
    "clean")
        dev_clean
        ;;
    "test")
        dev_test
        ;;
    "update")
        dev_update
        ;;
    *)
        echo "Development Helper for $PROJECT_NAME"
        echo "Usage: ./dev-helper.sh [command]"
        echo ""
        echo "Commands:"
        echo "  status  - Show development status"
        echo "  clean   - Clean development environment"
        echo "  test    - Run tests"
        echo "  update  - Update dependencies"
        ;;
esac
EOF
    chmod +x "dev-helper.sh"
    TOOLS_INSTALLED+=("dev-helper")

    # Update setup report with tools
    if [ ${#TOOLS_INSTALLED[@]} -gt 0 ]; then
        echo "✅ Development tools installed: ${TOOLS_INSTALLED[*]}"

        sed -i '/## Development Tools/,/## Next Steps/c\
## Development Tools\
✅ Development tools installed: '"${TOOLS_INSTALLED[*]}"'\
\
- Pre-commit hook configured\
- Development helper script: ./dev-helper.sh\
- Environment file created (if applicable)' REPO_SETUP_REPORT.md
    fi
fi
```

### 7. Git Configuration
```bash
echo "⚙️  Configuring Git settings..."

# Set up branch configuration
git config pull.rebase false
git config push.autoSetupRemote true

# Set up default branch tracking
MAIN_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -n "$MAIN_BRANCH" ]; then
    git config init.defaultBranch "$MAIN_BRANCH"
    echo "  Default branch: $MAIN_BRANCH"
fi

# Set up Git aliases for common operations
git config alias.st status
git config alias.co checkout
git config alias.br branch
git config alias.ci commit
git config alias.unstage 'reset HEAD --'
git config alias.last 'log -1 HEAD'
git config alias.visual '!gitk'
git config alias.graph 'log --oneline --graph --decorate --all'
git config alias.amend 'commit --amend --no-edit'
git config alias.undo 'reset --soft HEAD~1'

echo "✅ Git configuration updated"

# Create useful Git scripts
cat > "git-quick.sh" << 'EOF'
#!/bin/bash

# Quick Git Commands

BRANCH=$(git branch --show-current)
MODIFIED=$(git status --porcelain | wc -l)

quick_commit() {
    if [ -z "$1" ]; then
        echo "Usage: ./git-quick.sh commit 'message'"
        exit 1
    fi

    git add .
    git commit -m "$1"
    git push
}

quick_sync() {
    git fetch origin
    git pull origin "$BRANCH"
}

quick_status() {
    echo "📍 Branch: $BRANCH"
    echo "📝 Modified files: $MODIFIED"
    echo "📊 Status:"
    git status --short
}

quick_clean() {
    echo "🧹 Cleaning..."
    git clean -fd
    git reset --hard HEAD
}

case "$1" in
    "commit")
        quick_commit "$2"
        ;;
    "sync")
        quick_sync
        ;;
    "status")
        quick_status
        ;;
    "clean")
        quick_clean
        ;;
    *)
        echo "Git Quick Commands"
        echo "Usage: ./git-quick.sh [command]"
        echo ""
        echo "Commands:"
        echo "  commit [msg] - Add, commit, and push"
        echo "  sync        - Pull latest changes"
        echo "  status      - Quick status overview"
        echo "  clean       - Clean working directory"
        ;;
esac
EOF
chmod +x "git-quick.sh"
```

### 8. Final Setup and Reporting
```bash
echo "📋 Finalizing repository setup..."

# Update next steps based on project type
NEXT_STEPS=""

case "$PROJECT_TYPE" in
    "node")
        NEXT_STEPS="- Install dependencies: npm install
- Start development: npm run dev
- Run tests: npm test
- Build for production: npm run build"
        ;;
    "python")
        NEXT_STEPS="- Activate virtual environment: source .venv/bin/activate
- Install dependencies: pip install -e .
- Run tests: pytest
- Start development: [check README for specific commands]"
        ;;
    "rust")
        NEXT_STEPS="- Build project: cargo build
- Run tests: cargo test
- Start development: cargo run
- Build for release: cargo build --release"
        ;;
    *)
        NEXT_STEPS="- Check README.md for specific setup instructions
- Install project-specific dependencies
- Configure any required environment variables
- Run initial tests to verify setup"
        ;;
esac

# Finalize setup report
sed -i "/## Next Steps/c\
## Next Steps\
$NEXT_STEPS\
\
### Quick Start Commands\
- Development status: ./dev-helper.sh status\
- Quick Git operations: ./git-quick.sh status\
- Run tests: ./dev-helper.sh test\
- Clean environment: ./dev-helper.sh clean" REPO_SETUP_REPORT.md

echo ""
echo "✅ Repository setup completed successfully!"
echo ""
echo "📁 Repository: $LOCAL_DIR"
echo "🔗 URL: $REPO_URL"
echo "📋 Report: REPO_SETUP_REPORT.md"
echo ""
echo "Quick Start:"
echo "  cd $LOCAL_DIR"
echo "  ./dev-helper.sh status"
echo "  ./git-quick.sh status"
echo ""

# Show project-specific next steps
echo "Project-specific next steps:"
echo "$NEXT_STEPS"

if [ -f "README.md" ]; then
    echo ""
    echo "📖 Don't forget to check the project README.md for additional setup instructions"
fi
```

## Validation Commands

Execute these commands to validate repository setup:

```bash
# Check repository status
git status
git remote -v

# Verify dependencies
npm list  # or pip list, cargo tree, etc.

# Test helper scripts
./dev-helper.sh status
./git-quick.sh status

# Check setup report
cat REPO_SETUP_REPORT.md
```

## Usage Examples

```bash
# Full development setup
/git-repo https://github.com/user/project my-project development

# Production setup with shallow clone
/git-repo https://github.com/user/api-service api-service production

# Minimal setup
/git-repo https://github.com/user/utility-tool tool minimal

# Custom setup with interactive choices
/git-repo https://github.com/user/web-app web-app custom

# Use default local directory name
/git-repo https://github.com/andrefortin/awesome-project
```

## Report

After successful repository setup, provide this report:

```
✅ Repository Setup Completed

Repository: [REPO_URL]
Local Directory: [LOCAL_DIR]
Project Type: [PROJECT_TYPE]
Setup Type: [SETUP_TYPE]

Setup Summary:
- Repository cloned and configured
- Dependencies installed
- Development tools configured
- Git settings optimized
- Helper scripts created

Files Created:
- REPO_SETUP_REPORT.md - Complete setup documentation
- dev-helper.sh - Development environment helper
- git-quick.sh - Quick Git operations
- .git/hooks/pre-commit - Pre-commit validation

Next Steps:
- Review REPO_SETUP_REPORT.md
- Configure environment variables (.env)
- Run initial tests to verify setup
- Start development with project-specific commands

Quick Commands:
- ./dev-helper.sh status - Check development status
- ./git-quick.sh status - Quick Git overview
- ./dev-helper.sh test - Run test suite
- ./git-quick.sh commit "message" - Quick commit and push
```