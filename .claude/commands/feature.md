---
description: Create a feature branch for development with proper Git workflow
argument-hint: [feature-name] [app-name]
model: claude-sonnet-4-5-20250929
---

# Feature Branch Development

## Purpose

Create a new feature branch following proper Git workflow standards. All feature development must happen in separate branches and only merge to main after successful testing.

## Variables

FEATURE_NAME: $1
APP_NAME: $2 (optional, defaults to current directory)
GITHUB_USERNAME: andrefortin

## Instructions

- Always create feature branches from develop branch
- Use descriptive feature names in kebab-case
- Push branches to GitHub for collaboration and backup
- Ensure main branch protection rules are followed

## Workflow

### Step 1: Validate Environment
```bash
# Check if we're in a Git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a Git repository"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Determine app directory
if [ -n "$APP_NAME" ]; then
    if [ -d "apps/$APP_NAME" ]; then
        cd "apps/$APP_NAME"
        echo "Switched to app directory: apps/$APP_NAME"
    else
        echo "Error: App directory 'apps/$APP_NAME' not found"
        exit 1
    fi
fi
```

### Step 2: Create Feature Branch
```bash
# Switch to develop branch first
git checkout develop

# Pull latest changes
git pull origin develop

# Create and switch to feature branch
FEATURE_BRANCH="feature/$FEATURE_NAME"
git checkout -b $FEATURE_BRANCH

echo "Created feature branch: $FEATURE_BRANCH"
```

### Step 3: Push to GitHub
```bash
# Push new branch to GitHub
git push -u origin $FEATURE_BRANCH

echo "Pushed branch to GitHub: origin/$FEATURE_BRANCH"
```

### Step 4: Setup Development Environment
```bash
# Check if this is a Python app
if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    echo "Python app detected"
    if [ ! -d "venv" ]; then
        python -m venv venv
        echo "Created virtual environment"
    fi
    source venv/bin/activate
    pip install -r requirements.txt 2>/dev/null || pip install -r pyproject.toml 2>/dev/null
fi

# Check if this is a Node.js app
if [ -f "package.json" ]; then
    echo "Node.js app detected"
    if [ ! -d "node_modules" ]; then
        npm install
        echo "Installed Node.js dependencies"
    fi
fi

# Check if this is a multi-agent app and initialize if needed
if [ -f ".claude/orchestrator.md" ] || [ -d ".claude/agents" ]; then
    echo "Multi-agent app detected"
    echo "AI agents will be available for development assistance"
fi
```

### Step 5: Create Feature Documentation
```bash
# Create feature documentation file
FEATURE_DOC="docs/feature-$FEATURE_NAME.md"
mkdir -p docs

cat > $FEATURE_DOC << 'FEATUREDOC'
# Feature: $FEATURE_NAME

## Description
[Feature description will be added by developer]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

## Implementation Plan
1. [ ] Step 1
2. [ ] Step 2
3. [ ] Step 3

## Testing Plan
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Dependencies
- [ ] None identified yet

## Notes
[Additional notes and considerations]
FEATUREDOC

echo "Created feature documentation: $FEATURE_DOC"
```

### Step 6: Initial Commit
```bash
# Add feature documentation
git add $FEATURE_DOC
git commit -m "feat: Add feature documentation for $FEATURE_NAME"
git push

echo "Created initial commit with feature documentation"
```

## Report

### Branch Created Successfully
- **Feature Branch**: $FEATURE_BRANCH
- **Base Branch**: develop
- **GitHub URL**: https://github.com/$GITHUB_USERNAME/[repo-name]/tree/$FEATURE_BRANCH
- **Local Path**: $(pwd)
- **Documentation**: $FEATURE_DOC

### Development Environment
- **Git Status**: Ready for development
- **Dependencies**: Installed/Verified
- **Branch Tracking**: Configured with origin

### Next Development Steps
1. **Implement Feature**: Start coding your feature
2. **Commit Regularly**: Use descriptive commit messages
3. **Test Thoroughly**: Run all tests before considering merge
4. **Update Documentation**: Keep feature doc updated
5. **Create Pull Request**: When ready for review

### Available Commands During Development
- `/status` - Check current Git status and branch info
- `/commit [message]` - Commit changes with proper message
- `/test` - Run application tests
- `/merge` - Create pull request for feature merge
- `/bugfix [description]` - If you discover a bug during development

### Git Workflow Reminders
- **Main Branch**: Protected - no direct commits allowed
- **Feature Branches**: All development happens here
- **Testing Required**: Before any merge to main
- **Code Review**: Pull requests required for main merges
- **Documentation**: Keep docs updated with changes

## Error Handling

### Branch Already Exists
```bash
# If feature branch already exists locally
git checkout $FEATURE_BRANCH
git pull origin $FEATURE_BRANCH
```

### Push Failures
- Check GitHub authentication: `gh auth status`
- Verify repository exists and you have push access
- Check network connectivity

### Dependency Issues
- Verify Python/Node.js versions
- Check internet connectivity for package downloads
- Clear package caches if needed: `npm cache clean --force` or `pip cache purge`

## Best Practices

### Commit Messages
- Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, etc.
- Keep messages descriptive but concise
- Reference feature name in commits when relevant

### Branch Management
- Keep feature branches focused on single features
- Regularly merge develop into feature branches to stay updated
- Delete feature branches after successful merge

### Testing
- Write tests before or alongside code
- Run full test suite before requesting merge
- Test on multiple environments if applicable

### Documentation
- Update README files for user-facing changes
- Document APIs and new features
- Update architectural diagrams if structure changes
