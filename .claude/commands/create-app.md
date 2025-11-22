---
description: Create a new application with GitHub repository and proper Git workflow
argument-hint: [app-name] [app-type] [description]
model: claude-sonnet-4-5-20250929
---

# Create App with Git Workflow

## Purpose

Create a new application with automatic GitHub repository setup, proper Git initialization, and development workflow preparation. This command follows the andrefortin GitHub account standard.

## Variables

APP_NAME: $1
APP_TYPE: $2
APP_DESCRIPTION: $3
GITHUB_USERNAME: andrefortin

## Instructions

- Always create GitHub repositories in the andrefortin account unless explicitly told otherwise
- Initialize proper Git workflow with main branch protection
- Set up development structure with proper branching strategy
- Configure appropriate .gitignore and README files
- Create initial commit with proper documentation

## Workflow

### Step 1: Validate Input
Validate that APP_NAME is provided and follows naming conventions:
- Use kebab-case for app names (e.g., "my-new-app")
- Check if app directory already exists
- Validate APP_TYPE against known patterns

### Step 2: Create Local Application Structure
```bash
# Create app directory in apps/
mkdir -p apps/$APP_NAME
cd apps/$APP_NAME

# Initialize Git repository
git init

# Set up proper .gitignore
cat > .gitignore << 'GITIGNORE'
# Dependencies
node_modules/
__pycache__/
*.pyc
.pytest_cache/
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build outputs
dist/
build/
out/
GITIGNORE

# Create basic README
cat > README.md << 'README'
# $APP_NAME

$APP_DESCRIPTION

## Quick Start

[Development setup instructions will be added]

## Development

This application follows our Git workflow standards:
- All features developed in separate branches
- Main branch protected from direct commits
- Comprehensive testing before merging

## Architecture

[Architecture overview]

## License

MIT License
README

# Initial commit
git add .
git commit -m "Initial commit: Setup $APP_NAME application structure"
```

### Step 3: Create GitHub Repository
```bash
# Create repository on GitHub (using GitHub CLI)
gh repo create $GITHUB_USERNAME/$APP_NAME \
  --public \
  --description "$APP_DESCRIPTION" \
  --clone=false

# Add remote origin
git remote add origin git@github.com:$GITHUB_USERNAME/$APP_NAME.git

# Push to main branch
git branch -M main
git push -u origin main
```

### Step 4: Setup Application Structure Based on Type

Based on APP_TYPE, create appropriate structure:

#### For Python/FastAPI apps:
```bash
# Create backend structure
mkdir -p backend/{tests,src,models}
cat > backend/requirements.txt << 'PYREQ'
fastapi
uvicorn[standard]
pydantic
python-dotenv
asyncpg
PYREQ

cat > backend/main.py << 'MAIN'
from fastapi import FastAPI

app = FastAPI(title="$APP_NAME")

@app.get("/health")
async def health():
    return {"status": "healthy"}
MAIN

cd backend && python -m venv venv
```

#### For Node.js/React apps:
```bash
# Create frontend structure
mkdir -p frontend/{src,public,tests}
cat > frontend/package.json << 'PACKAGE'
{
  "name": "$APP_NAME",
  "version": "1.0.0",
  "description": "$APP_DESCRIPTION",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest"
  },
  "dependencies": {},
  "devDependencies": {
    "vite": "^5.0.0",
    "vitest": "^1.0.0"
  }
}
PACKAGE

cd frontend && npm install
```

### Step 5: Setup Development Workflow
```bash
# Create develop branch
git checkout -b develop
git push -u origin develop

# Configure branch protection (via GitHub CLI)
gh repo edit $GITHUB_USERNAME/$APP_NAME \
  --enable-merge-commit=false \
  --enable-squash-merge=true \
  --enable-rebase-merge=false

# Protect main branch
gh repo edit $GITHUB_USERNAME/$APP_NAME \
  --enable-merge-commit=false \
  --enable-squash-merge=true \
  --enable-rebase-merge=false
```

### Step 6: Update Project Structure
```bash
# Update main project README if needed
cd ../..
# Update any project index files to include new app
```

## Report

### Repository Created
- **GitHub URL**: https://github.com/$GITHUB_USERNAME/$APP_NAME
- **Local Path**: apps/$APP_NAME
- **Branches**: main (protected), develop
- **Initial Structure**: [list of directories created]

### Git Workflow Setup
- **Main Branch**: Protected, no direct commits
- **Development Branch**: Ready for feature branches
- **Remote Origin**: Configured and pushed
- **Branch Protection**: Enabled with required reviews

### Next Steps
1. Switch to develop branch: `cd apps/$APP_NAME && git checkout develop`
2. Create feature branches: `git checkout -b feature/your-feature`
3. Develop and test your feature
4. Create pull request to main branch for review

### Git Workflow Commands Available
- `/feature [feature-name]` - Create feature branch from develop
- `/bugfix [bug-description]` - Create bugfix branch
- `/merge [branch-name]` - Merge tested branch to main
- `/status` - Show current Git status and branch info

## Error Handling

If GitHub repository creation fails:
1. Check GitHub CLI authentication: `gh auth status`
2. Verify repository doesn't already exist
3. Check internet connection and GitHub API limits

If local setup fails:
1. Verify directory permissions
2. Check if app name conflicts with existing directories
3. Ensure proper tools are installed (git, gh, node/python as needed)
