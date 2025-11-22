---
description: Create a new application with GitHub repository initialization and proper project structure
argument-hint: [app-name] [app-type] [description]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, MultiEdit
---

# Git New App

Create a new application with proper GitHub repository initialization, project structure, and development setup. This command automates the creation of new apps with best practices for Git workflow and project organization.

## Variables

APP_NAME: $1
APP_TYPE: $2
APP_DESCRIPTION: $3
GITHUB_USERNAME: `andrefortin`

## Instructions

- IMPORTANT: If no `APP_NAME` is provided, stop and ask the user to provide it.
- IMPORTANT: If no `APP_TYPE` is provided, ask the user to specify (web, api, mobile, desktop, library, cli).
- IMPORTANT: If no `APP_DESCRIPTION` is provided, ask for a brief description of the app.
- Validate APP_NAME follows naming conventions (lowercase, hyphens, no special chars)
- Create GitHub repository using gh CLI
- Initialize project with proper structure based on APP_TYPE
- Set up development environment and configuration files
- Create initial commit with proper structure
- Set up branch protection rules and default branch

## Workflow

1. Validate Inputs - Check all required variables and validate naming conventions
2. Create GitHub Repo - Use gh CLI to create remote repository
3. Initialize Local Project - Create directory structure and basic files
4. Setup Configuration - Add .gitignore, README, and config files
5. Install Dependencies - Set up package management and basic dependencies
6. Create Initial Commit - Set up proper Git history
7. Configure Repository - Set up branch protection and team settings
8. Setup Development - Configure local development environment

## Error Handling

- If GitHub CLI is not installed, provide installation instructions
- If repository already exists, suggest alternative names
- If app name is invalid, provide naming guidelines
- If gh login is required, provide authentication instructions
- Always clean up partially created directories on failure

## Project Templates

### Web App (web)
```
app-name/
├── frontend/          # Vue/React frontend
├── backend/           # API backend
├── docker-compose.yml # Development containers
├── .env.sample        # Environment template
└── README.md          # Project documentation
```

### API Service (api)
```
app-name/
├── src/               # Source code
├── tests/             # Test files
├── Dockerfile         # Container configuration
├── requirements.txt   # Python dependencies
└── README.md          # API documentation
```

### Library (library)
```
app-name/
├── src/               # Library source
├── tests/             # Test suite
├── examples/          # Usage examples
├── docs/              # Documentation
├── pyproject.toml     # Package configuration
└── README.md          # Library documentation
```

### CLI Tool (cli)
```
app-name/
├── src/               # CLI source
├── tests/             # Tests
├── README.md          # Usage documentation
├── pyproject.toml     # Package config with entry points
└── .github/           # CI/CD workflows
```

## Implementation Steps

Execute these steps in order for proper app creation:

### 1. Validate and Prepare
```bash
# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) is required. Install from https://cli.github.com/"
    exit 1
fi

# Check GitHub authentication
if ! gh auth status &> /dev/null; then
    echo "Please authenticate with GitHub first: gh auth login"
    exit 1
fi

# Validate app name
if [[ ! "$APP_NAME" =~ ^[a-z][a-z0-9-]*[a-z0-9]$ ]]; then
    echo "App name must be lowercase, start with letter, use hyphens only"
    exit 1
fi

# Check if directory already exists
if [ -d "$APP_NAME" ]; then
    echo "Directory $APP_NAME already exists"
    exit 1
fi
```

### 2. Create GitHub Repository
```bash
# Create remote repository
gh repo create "$GITHUB_USERNAME/$APP_NAME" \
    --description "$APP_DESCRIPTION" \
    --public \
    --clone=false \
    --confirm

echo "✅ GitHub repository created: https://github.com/$GITHUB_USERNAME/$APP_NAME"
```

### 3. Initialize Local Project
```bash
# Create project directory
mkdir "$APP_NAME"
cd "$APP_NAME"

# Initialize Git repository
git init
git branch -m main
git remote add origin "https://github.com/$GITHUB_USERNAME/$APP_NAME.git"

# Create basic structure based on APP_TYPE
case "$APP_TYPE" in
    "web")
        mkdir -p frontend backend
        ;;
    "api")
        mkdir -p src tests
        ;;
    "library")
        mkdir -p src tests examples docs
        ;;
    "cli")
        mkdir -p src tests
        ;;
    *)
        mkdir -p src tests
        ;;
esac
```

### 4. Create Configuration Files

#### .gitignore
```bash
cat > .gitignore << 'EOF'
# Dependencies
node_modules/
__pycache__/
*.pyc
.pytest_cache/

# Environment
.env
.env.local
.env.production

# Build outputs
dist/
build/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log
EOF
```

#### README.md
```bash
cat > README.md << EOF
# $APP_NAME

$APP_DESCRIPTION

## Getting Started

### Prerequisites
- Node.js 18+ (for web apps)
- Python 3.9+ (for Python apps)
- Docker (optional)

### Installation

\`\`\`bash
# Clone the repository
git clone https://github.com/$GITHUB_USERNAME/$APP_NAME.git
cd $APP_NAME

# Install dependencies
# [Installation instructions based on app type]
\`\`\`

### Development

\`\`\`bash
# Start development server
# [Development instructions]
\`\`\`

## Contributing

1. Fork the repository
2. Create a feature branch: \`git checkout -b feature/amazing-feature\`
3. Commit your changes: \`git commit -m 'Add amazing feature'\`
4. Push to the branch: \`git push origin feature/amazing-feature\`
5. Open a Pull Request

## License

This project is licensed under the MIT License.
EOF
```

### 5. App-Specific Setup

#### For Web Apps
```bash
if [ "$APP_TYPE" = "web" ]; then
    # Frontend setup
    cat > frontend/package.json << EOF
{
  "name": "$APP_NAME-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.5.0",
    "vite": "^5.0.0"
  }
}
EOF

    # Backend setup (Python/FastAPI)
    cat > backend/requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
EOF

    cat > backend/main.py << EOF
from fastapi import FastAPI

app = FastAPI(title="$APP_NAME API")

@app.get("/")
async def root():
    return {"message": "Welcome to $APP_NAME API"}
EOF

    # Docker Compose
    cat > docker-compose.yml << EOF
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/$APP_NAME
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=$APP_NAME
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF
fi
```

#### For API Services
```bash
if [ "$APP_TYPE" = "api" ]; then
    cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
EOF

    cat > src/main.py << EOF
from fastapi import FastAPI

app = FastAPI(
    title="$APP_NAME",
    description="$APP_DESCRIPTION",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "Welcome to $APP_NAME API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
EOF

    cat > Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
fi
```

#### For Libraries
```bash
if [ "$APP_TYPE" = "library" ]; then
    cat > pyproject.toml << EOF
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "$APP_NAME"
version = "0.1.0"
description = "$APP_DESCRIPTION"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

[project.urls]
Homepage = "https://github.com/$GITHUB_USERNAME/$APP_NAME"
Repository = "https://github.com/$GITHUB_USERNAME/$APP_NAME"
Issues = "https://github.com/$GITHUB_USERNAME/$APP_NAME/issues"
EOF

    cat > src/__init__.py << EOF
"""
$APP_NAME - $APP_DESCRIPTION
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
EOF
fi
```

#### For CLI Tools
```bash
if [ "$APP_TYPE" = "cli" ]; then
    cat > pyproject.toml << EOF
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "$APP_NAME"
version = "0.1.0"
description = "$APP_DESCRIPTION"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
]

[project.scripts]
$APP_NAME = "$APP_NAME.main:main"
EOF

    cat > src/main.py << EOF
#!/usr/bin/env python3
"""
$APP_NAME - $APP_DESCRIPTION
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        prog="$APP_NAME",
        description="$APP_DESCRIPTION"
    )
    parser.add_argument("--version", action="version", version="0.1.0")

    args = parser.parse_args()
    print("$APP_NAME - CLI tool initialized")

if __name__ == "__main__":
    main()
EOF
fi
```

### 6. Create Initial Commit
```bash
# Add all files
git add .

# Create initial commit
git commit -m "🎉 Initial commit: Set up $APP_NAME project structure

- Created project structure for $APP_TYPE application
- Added configuration files (.gitignore, README.md)
- Set up development environment
- Initialized package management

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to main branch
git push -u origin main
```

### 7. Configure Repository Settings
```bash
# Set up branch protection
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":[]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null || echo "Branch protection requires admin privileges"

# Set default branch to main
gh repo edit "$GITHUB_USERNAME/$APP_NAME" --default-branch main
```

### 8. Setup Local Development
```bash
# Create .env.sample file
cat > .env.sample << EOF
# Environment Variables for $APP_NAME
# Copy this file to .env and fill in your values

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/$APP_NAME

# API Keys
API_KEY=your_api_key_here

# Other Settings
DEBUG=true
PORT=8000
EOF

# Install dependencies if possible
if [ "$APP_TYPE" = "api" ] || [ "$APP_TYPE" = "library" ] || [ "$APP_TYPE" = "cli" ]; then
    if command -v uv &> /dev/null; then
        echo "Installing Python dependencies with uv..."
        uv venv
        source .venv/bin/activate
        uv pip install -e .
    else
        echo "Consider installing uv for Python dependency management: pip install uv"
    fi
fi

echo ""
echo "✅ $APP_NAME app created successfully!"
echo "📍 Repository: https://github.com/$GITHUB_USERNAME/$APP_NAME"
echo "📁 Local directory: $(pwd)"
echo ""
echo "Next steps:"
echo "1. cd $APP_NAME"
echo "2. Copy .env.sample to .env and configure"
echo "3. Start development with the appropriate commands"
echo "4. Create your first feature branch: git checkout -b feature/initial-feature"
```

## Validation Commands

Execute these commands to validate the app creation:

```bash
# Check repository was created
gh repo view "$GITHUB_USERNAME/$APP_NAME" --json name,description,visibility

# Check local Git setup
cd "$APP_NAME" && git status && git remote -v

# Check structure exists
ls -la "$APP_NAME"

# Test basic functionality (if applicable)
cd "$APP_NAME" && [ -f "src/main.py" ] && python src/main.py || echo "Basic setup complete"
```

## Report

After successful app creation, provide this report:

```
✅ New App Created Successfully

Repository: https://github.com/andrefortin/[APP_NAME]
Type: [APP_TYPE]
Location: ./[APP_NAME]/

Key Components:
- GitHub repository initialized with proper settings
- Project structure created for [APP_TYPE]
- Development environment configured
- Initial commit with comprehensive README
- Branch protection and best practices applied

Next Steps:
- Configure environment variables (.env from .env.sample)
- Create your first feature branch
- Start development with your preferred tools
```