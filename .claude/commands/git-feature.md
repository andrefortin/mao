---
description: Create and manage feature development branches with proper Git workflow
argument-hint: [feature-name] [base-branch] [type]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, MultiEdit
---

# Git Feature

Create and manage feature development branches following Git best practices. This command handles branch creation, synchronization, and proper preparation for pull requests.

## Variables

FEATURE_NAME: $1
BASE_BRANCH: $2  (defaults to main)
FEATURE_TYPE: $3  (feature, enhancement, refactor, experiment)
BRANCH_PREFIX: `feature/`

## Instructions

- IMPORTANT: If no `FEATURE_NAME` is provided, stop and ask the user to provide it.
- IMPORTANT: Validate FEATURE_NAME follows naming conventions (kebab-case)
- Use BASE_BRANCH from argument or default to main
- Ensure working directory is clean before creating new branch
- Pull latest changes from base branch before branching
- Set up tracking branch and proper configuration
- Create feature development checklist if needed

## Workflow

1. Validate Environment - Check Git status, authentication, and branch naming
2. Update Base Branch - Pull latest changes from specified base branch
3. Create Feature Branch - Branch from updated base with proper naming
4. Setup Development Environment - Configure tracking and local settings
5. Create Feature Documentation - Set up tracking and planning files
6. Initialize Development - Create initial commit structure and setup

## Error Handling

- If working directory is not clean, provide options to stash or commit
- If base branch doesn't exist, offer available branches
- If feature branch already exists, suggest alternative names
- If no GitHub remote is configured, help set it up
- If GitHub CLI is not available, provide alternative commands

## Implementation Steps

### 1. Environment Validation
```bash
# Check if we're in a Git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a Git repository"
    exit 1
fi

# Check working directory status
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Working directory is not clean"
    echo "Please commit, stash, or discard your changes first:"
    echo "  git commit -m 'Save work before creating feature branch'"
    echo "  git stash"
    exit 1
fi

# Validate feature name
if [[ ! "$FEATURE_NAME" =~ ^[a-z][a-z0-9-]*[a-z0-9]$ ]]; then
    echo "❌ Error: Feature name must be kebab-case (lowercase, hyphens, no special chars)"
    echo "Example: user-authentication, api-integration, ui-redesign"
    exit 1
fi

# Set default base branch if not provided
if [ -z "$BASE_BRANCH" ]; then
    BASE_BRANCH="main"
fi

# Set default feature type if not provided
if [ -z "$FEATURE_TYPE" ]; then
    FEATURE_TYPE="feature"
fi

# Validate feature type
case "$FEATURE_TYPE" in
    "feature"|"enhancement"|"refactor"|"experiment")
        BRANCH_PREFIX="$FEATURE_TYPE/"
        ;;
    *)
        echo "❌ Error: Invalid feature type. Use: feature, enhancement, refactor, or experiment"
        exit 1
        ;;
esac
```

### 2. Base Branch Preparation
```bash
# Check if base branch exists
if ! git show-ref --verify --quiet "refs/heads/$BASE_BRANCH"; then
    echo "❌ Error: Base branch '$BASE_BRANCH' does not exist locally"
    echo "Available branches:"
    git branch -a
    exit 1
fi

# Fetch latest changes from remote
echo "📥 Fetching latest changes from remote..."
git fetch origin

# Update base branch
echo "🔄 Updating base branch '$BASE_BRANCH'..."
git checkout "$BASE_BRANCH"
git pull origin "$BASE_BRANCH"

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to update base branch"
    exit 1
fi

echo "✅ Base branch '$BASE_BRANCH' is up to date"
```

### 3. Create Feature Branch
```bash
BRANCH_NAME="$BRANCH_PREFIX$FEATURE_NAME"

# Check if feature branch already exists
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    echo "❌ Error: Branch '$BRANCH_NAME' already exists"
    echo "Choose a different name or checkout the existing branch:"
    echo "  git checkout $BRANCH_NAME"
    exit 1
fi

# Check if branch exists on remote
if git show-ref --verify --quiet "refs/remotes/origin/$BRANCH_NAME"; then
    echo "⚠️  Warning: Branch '$BRANCH_NAME' exists on remote"
    echo "Checking out and updating from remote..."
    git checkout -b "$BRANCH_NAME" "origin/$BRANCH_NAME"
    git pull origin "$BRANCH_NAME"
else
    echo "🌿 Creating new feature branch '$BRANCH_NAME'..."
    git checkout -b "$BRANCH_NAME"

    # Set up tracking branch
    git push -u origin "$BRANCH_NAME"
fi

echo "✅ Feature branch '$BRANCH_NAME' created and ready"
```

### 4. Development Environment Setup
```bash
# Configure Git user for this branch if needed
if [ -z "$(git config user.name)" ] || [ -z "$(git config user.email)" ]; then
    echo "⚙️  Git user configuration not found. Please configure:"
    echo "  git config --global user.name 'Your Name'"
    echo "  git config --global user.email 'your.email@example.com'"
fi

# Set up branch-specific configuration
git config branch."$BRANCH_NAME".rebase true

# Create development checklist
cat > "FEATURE_CHECKLIST.md" << EOF
# Feature Development Checklist: $FEATURE_NAME

## Overview
- **Branch**: $BRANCH_NAME
- **Base**: $BASE_BRANCH
- **Type**: $FEATURE_TYPE
- **Created**: $(date)
- **Status**: In Progress

## Development Tasks

### ✅ Initial Setup
- [x] Branch created from $BASE_BRANCH
- [x] Tracking branch configured
- [x] Development environment ready

### 📋 Implementation Tasks
- [ ] Design and plan implementation
- [ ] Write code for the feature
- [ ] Add tests for new functionality
- [ ] Update documentation
- [ ] Test the implementation thoroughly

### 🔍 Review Tasks
- [ ] Self-review the code changes
- [ ] Run all tests and ensure they pass
- [ ] Check code quality and style
- [ ] Verify edge cases are handled
- [ ] Test integration with existing features

### 📝 Documentation Tasks
- [ ] Update README if needed
- [ ] Add/update inline comments
- [ ] Create/update API documentation
- [ ] Document breaking changes if any

### 🚀 Release Tasks
- [ ] Rebase onto latest $BASE_BRANCH
- [ ] Resolve any merge conflicts
- [ ] Run full test suite
- [ ] Create pull request
- [ ] Address review feedback
- [ ] Merge to $BASE_BRANCH

## Notes

Add any important notes, decisions, or requirements specific to this feature here.

## Links

- Issue/Ticket: [Link to issue if applicable]
- Design Doc: [Link to design document if applicable]
- Mockups: [Link to mockups if applicable]
EOF

echo "📋 Created development checklist: FEATURE_CHECKLIST.md"
```

### 5. Feature Initialization
```bash
# Create feature-specific structure if this is a complex feature
if [ "$FEATURE_TYPE" = "feature" ]; then
    # Create feature documentation directory if it doesn't exist
    mkdir -p "docs/features"

    # Create feature documentation
    cat > "docs/features/$FEATURE_NAME.md" << EOF
# Feature: $FEATURE_NAME

## Description
[Describe the feature being implemented]

## Requirements
[List specific requirements for this feature]

## Implementation Details
[Technical implementation notes]

## Testing
[Testing approach and test cases]

## Dependencies
[List any dependencies on other features or systems]

## Impact
[Describe the impact on existing functionality]

## Rollback Plan
[How to roll back this change if needed]
EOF

    echo "📚 Created feature documentation: docs/features/$FEATURE_NAME.md"
fi

# Create initial commit structure
git add FEATURE_CHECKLIST.md
if [ -f "docs/features/$FEATURE_NAME.md" ]; then
    git add "docs/features/$FEATURE_NAME.md"
fi

git commit -m "🚀 Start feature: $FEATURE_NAME

- Initialize feature development
- Add development checklist
- Set up feature documentation
- Configure branch for development

Feature: $FEATURE_NAME
Type: $FEATURE_TYPE
Base: $BASE_BRANCH

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin "$BRANCH_NAME"

echo ""
echo "✅ Feature development initialized successfully!"
echo "🌿 Branch: $BRANCH_NAME"
echo "📋 Checklist: FEATURE_CHECKLIST.md"
echo ""
echo "Development workflow:"
echo "1. Work on your feature implementation"
echo "2. Commit changes with descriptive messages"
echo "3. Push regularly: git push origin $BRANCH_NAME"
echo "4. When ready: git checkout main && git pull && git checkout $BRANCH_NAME && git rebase main"
echo "5. Create pull request for review"
```

### 6. Integration Helper Functions
```bash
# Create helper script for common feature operations
cat > "feature-helper.sh" << 'EOF'
#!/bin/bash

# Feature Development Helper Script

BRANCH_NAME=$(git branch --show-current)
FEATURE_TYPE=$(echo "$BRANCH_NAME" | cut -d'/' -f1)
FEATURE_NAME=$(echo "$BRANCH_NAME" | cut -d'/' -f2-)

feature_status() {
    echo "Feature: $FEATURE_NAME"
    echo "Branch: $BRANCH_NAME"
    echo "Type: $FEATURE_TYPE"
    echo "Status: $(git status --porcelain | wc -l) modified files"
    echo "Commits ahead: $(git rev-list --count origin/main..HEAD 2>/dev/null || echo 'N/A')"
}

feature_sync() {
    echo "🔄 Syncing feature with main branch..."
    git fetch origin
    git checkout main
    git pull origin main
    git checkout "$BRANCH_NAME"
    git rebase main

    if [ $? -eq 0 ]; then
        echo "✅ Feature synced successfully"
        echo "📤 Pushing updated branch..."
        git push origin "$BRANCH_NAME" --force-with-lease
    else
        echo "❌ Rebase failed. Resolve conflicts and continue:"
        echo "  git rebase --continue"
        echo "  git rebase --abort"
    fi
}

feature_commit() {
    if [ -z "$1" ]; then
        echo "Usage: ./feature-helper.sh commit 'Commit message'"
        exit 1
    fi

    git add .
    git commit -m "feat: $1

Feature: $FEATURE_NAME

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

    git push origin "$BRANCH_NAME"
}

feature_pr() {
    echo "🔗 Creating pull request..."
    gh pr create \
        --title "feat: $FEATURE_NAME" \
        --body "## Summary

[Describe what this feature does]

## Changes Made
- [List the main changes]

## Testing
- [Describe how this was tested]

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added and passing
- [ ] Documentation updated

Closes #[issue-number]" \
        --base main \
        --head "$BRANCH_NAME"

    echo "✅ Pull request created"
}

case "$1" in
    "status")
        feature_status
        ;;
    "sync")
        feature_sync
        ;;
    "commit")
        feature_commit "$2"
        ;;
    "pr")
        feature_pr
        ;;
    *)
        echo "Feature Development Helper"
        echo "Usage: ./feature-helper.sh [command]"
        echo ""
        echo "Commands:"
        echo "  status  - Show feature development status"
        echo "  sync    - Sync feature with main branch (rebase)"
        echo "  commit  - Commit changes with feature prefix"
        echo "  pr      - Create pull request"
        echo ""
        echo "Current feature: $FEATURE_NAME"
        ;;
esac
EOF

chmod +x feature-helper.sh
echo "🛠️  Created feature helper script: ./feature-helper.sh"
```

## Validation Commands

Execute these commands to validate feature setup:

```bash
# Check branch status
git status
git branch -vv

# Verify tracking branch
git remote show origin

# Test helper script
./feature-helper.sh status

# Check if documentation was created
ls -la FEATURE_CHECKLIST.md docs/features/
```

## Usage Examples

```bash
# Create new feature
/git-feature user-authentication main feature

# Create enhancement
/git-feature dashboard-widgets main enhancement

# Create experimental feature
/git-feature ai-integration main experiment

# Create refactor
/git-feature database-optimization main refactor
```

## Report

After successful feature branch creation, provide this report:

```
✅ Feature Development Branch Created

Branch: [BRANCH_NAME]
Type: [FEATURE_TYPE]
Base: [BASE_BRANCH]
Tracker: FEATURE_CHECKLIST.md

Development Tools:
- Feature helper script: ./feature-helper.sh
- Documentation: docs/features/[FEATURE_NAME].md
- Ready for development

Next Steps:
1. Follow the checklist in FEATURE_CHECKLIST.md
2. Use ./feature-helper.sh for common operations
3. Implement your feature with regular commits
4. Sync regularly: ./feature-helper.sh sync
5. Create PR when ready: ./feature-helper.sh pr
```