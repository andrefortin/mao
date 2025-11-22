---
description: Check current Git status, branch information, and workflow compliance
argument-hint: [app-name] [verbose]
model: claude-sonnet-4-5-20250929
---

# Git Status and Workflow Check

## Purpose

Check current Git status, branch information, and verify compliance with established Git workflow standards. This command provides a comprehensive view of your current Git state and workflow adherence.

## Variables

APP_NAME: $1 (optional, check specific app directory)
VERBOSE: $2 (optional, show detailed information)

## Instructions

- Always verify Git workflow compliance
- Check branch protection status
- Verify repository connection to GitHub
- Identify any workflow violations

## Workflow

### Step 1: Determine Working Directory
```bash
# Check if specific app directory requested
if [ -n "$APP_NAME" ]; then
    if [ -d "apps/$APP_NAME" ]; then
        cd "apps/$APP_NAME"
        echo "Checking status for app: $APP_NAME"
        WORKING_DIR="apps/$APP_NAME"
    else
        echo "Error: App directory 'apps/$APP_NAME' not found"
        exit 1
    fi
else
    WORKING_DIR="current directory"
    echo "Checking status for current directory"
fi
```

### Step 2: Check Git Repository Status
```bash
# Verify we are in a Git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a Git repository"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Get repository information
REPO_NAME=$(basename $(git rev-parse --show-toplevel))
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "No remote configured")
CURRENT_BRANCH=$(git branch --show-current)
COMMIT_HASH=$(git rev-parse --short HEAD)
LAST_COMMIT_DATE=$(git log -1 --pretty=format:'%ci' 2>/dev/null)
LAST_COMMIT_MESSAGE=$(git log -1 --pretty=format:'%s' 2>/dev/null)
```

### Step 3: Check Working Directory Status
```bash
# Check for uncommitted changes
UNCOMMITTED_STATUS=$(git status --porcelain)
UNCOMMITTED_COUNT=$(echo "$UNCOMMITTED_STATUS" | wc -l)

# Check for untracked files
UNTRACKED_COUNT=$(git ls-files --others --exclude-standard | wc -l)

# Check for staged changes
STAGED_COUNT=$(git diff --cached --name-only | wc -l)

# Check for modified files
MODIFIED_COUNT=$(git diff --name-only | wc -l)
```

### Step 4: Check Branch Information
```bash
# Get all local branches
LOCAL_BRANCHES=$(git branch --format='%(refname:short)')

# Get all remote branches
REMOTE_BRANCHES=$(git branch -r --format='%(refname:short)')

# Check if we are on main/develop branch
IS_MAIN_BRANCH=false
IS_DEVELOP_BRANCH=false
IS_FEATURE_BRANCH=false
IS_BUGFIX_BRANCH=false

case $CURRENT_BRANCH in
    main|master)
        IS_MAIN_BRANCH=true
        ;;
    develop)
        IS_DEVELOP_BRANCH=true
        ;;
    feature/*)
        IS_FEATURE_BRANCH=true
        ;;
    bugfix/*)
        IS_BUGFIX_BRANCH=true
        ;;
esac
```

### Step 5: Check GitHub Integration
```bash
# Check GitHub CLI authentication
GITHUB_AUTH_STATUS="Not authenticated"
if gh auth status > /dev/null 2>&1; then
    GITHUB_AUTH_STATUS="Authenticated"
    GITHUB_USER=$(gh api user --jq '.login' 2>/dev/null || echo "Unknown")
fi

# Check if remote is GitHub
GITHUB_REMOTE=false
if [[ $REMOTE_URL == *"github.com"* ]]; then
    GITHUB_REMOTE=true
    # Extract owner and repo name
    GITHUB_OWNER=$(echo $REMOTE_URL | sed -n 's/.*github\.com[:\/]\([^\/]*\)\/\(.*\)\.git/\1/p')
    GITHUB_REPO=$(echo $REMOTE_URL | sed -n 's/.*github\.com[:\/]\([^\/]*\)\/\(.*\)\.git/\2/p')
fi
```

### Step 6: Workflow Compliance Check
```bash
# Check for workflow violations
VIOLATIONS=""

# Check if working on main branch with changes
if [ "$IS_MAIN_BRANCH" = true ] && [ "$UNCOMMITTED_COUNT" -gt 0 ]; then
    VIOLATIONS="$VIOLATIONS
❌ Working directly on main branch with uncommitted changes"
fi

# Check if feature/bugfix branches have documentation
if [ "$IS_FEATURE_BRANCH" = true ]; then
    FEATURE_DOC="docs/feature-$(echo $CURRENT_BRANCH | sed 's/feature\///').md"
    if [ ! -f "$FEATURE_DOC" ]; then
        VIOLATIONS="$VIOLATIONS
⚠️ Feature branch missing documentation: $FEATURE_DOC"
    fi
fi

if [ "$IS_BUGFIX_BRANCH" = true ]; then
    BUGFIX_DOC="bugs/bugfix-$(echo $CURRENT_BRANCH | sed 's/bugfix\///').md"
    if [ ! -f "$BUGFIX_DOC" ]; then
        VIOLATIONS="$VIOLATIONS
⚠️ Bugfix branch missing documentation: $BUGFIX_DOC"
    fi
fi

# Check if remote is configured
if [ -z "$REMOTE_URL" ] || [ "$REMOTE_URL" = "No remote configured" ]; then
    VIOLATIONS="$VIOLATIONS
⚠️ No Git remote configured"
fi

# Check if not pushed to remote
if [ -n "$REMOTE_URL" ]; then
    LOCAL_COMMIT=$(git rev-parse HEAD)
    if git rev-parse --verify origin/$CURRENT_BRANCH > /dev/null 2>&1; then
        REMOTE_COMMIT=$(git rev-parse origin/$CURRENT_BRANCH)
        if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
            VIOLATIONS="$VIOLATIONS
⚠️ Local branch not pushed to remote"
        fi
    else
        VIOLATIONS="$VIOLATIONS
⚠️ Branch not pushed to remote"
    fi
fi
```

### Step 7: Detailed Information (if verbose)
```bash
if [ -n "$VERBOSE" ]; then
    echo ""
    echo "=== Detailed Git Information ==="
    echo ""
    echo "Repository: $REPO_NAME"
    echo "Working Directory: $(pwd)"
    echo "Remote URL: $REMOTE_URL"
    echo ""
    echo "=== Branch Information ==="
    echo "Current Branch: $CURRENT_BRANCH"
    echo "Commit Hash: $COMMIT_HASH"
    echo "Last Commit: $LAST_COMMIT_DATE"
    echo "Last Message: $LAST_COMMIT_MESSAGE"
    echo ""
    echo "=== Local Branches ==="
    echo "$LOCAL_BRANCHES"
    echo ""
    echo "=== Remote Tracking ==="
    git branch -vv
    echo ""
    echo "=== Recent Commits ==="
    git log --oneline -5
fi
```

## Report

### Repository Status
- **Repository**: $REPO_NAME
- **Working Directory**: $WORKING_DIR
- **Remote URL**: $REMOTE_URL
- **Current Branch**: $CURRENT_BRANCH
- **Last Commit**: $COMMIT_HASH ($LAST_COMMIT_DATE)

### Working Directory Status
- **Uncommitted Changes**: $UNCOMMITTED_COUNT files
- **Staged Changes**: $STAGED_COUNT files
- **Modified Files**: $MODIFIED_COUNT files
- **Untracked Files**: $UNTRACKED_COUNT files

### Branch Analysis
- **Branch Type**: $([ "$IS_MAIN_BRANCH" = true ] && echo "Main Branch" || [ "$IS_DEVELOP_BRANCH" = true ] && echo "Develop Branch" || [ "$IS_FEATURE_BRANCH" = true ] && echo "Feature Branch" || [ "$IS_BUGFIX_BRANCH" = true ] && echo "Bugfix Branch" || echo "Other Branch")
- **Local Branches**: $(echo "$LOCAL_BRANCHES" | wc -l) branches
- **Remote Branches**: $(echo "$REMOTE_BRANCHES" | wc -l) branches

### GitHub Integration
- **Authentication Status**: $GITHUB_AUTH_STATUS
- **GitHub User**: ${GITHUB_USER:-"Not available"}
- **GitHub Remote**: $([ "$GITHUB_REMOTE" = true ] && echo "Yes ($GITHUB_OWNER/$GITHUB_REPO)" || echo "No")

### Workflow Compliance

#### ✅ Compliant Standards
- [ ] Git repository initialized
- [ ] Current branch identified
- [ ] Working directory status checked
- [ ] Remote configuration verified

#### ⚠️ Potential Issues
$([ -n "$VIOLATIONS" ] && echo "$VIOLATIONS" || echo "No violations detected")

### Recommended Actions

#### If Working on Main Branch
```bash
# Create feature branch instead
/feature "new-feature-name"

# Or switch to develop branch
git checkout develop
```

#### If Uncommitted Changes
```bash
# Check what changes exist
git status

# Commit changes
git add .
git commit -m "Descriptive commit message"

# Or stash changes
git stash
```

#### If Missing Documentation
```bash
# For feature branches
echo "Feature documentation" > docs/feature-$(echo $CURRENT_BRANCH | sed 's/feature\///').md

# For bugfix branches
echo "Bug fix documentation" > bugs/bugfix-$(echo $CURRENT_BRANCH | sed 's/bugfix\///').md
```

#### If Not Pushed to Remote
```bash
# Push current branch
git push -u origin $CURRENT_BRANCH
```

### Quick Commands

- **Create Feature**: `/feature [feature-name]`
- **Create Bugfix**: `/bugfix [description]`
- **Create Merge**: `/merge [branch-name]`
- **Create New App**: `/create-app [app-name] [type] [description]`

### Git Workflow Reminders

1. **Never work directly on main branch** with uncommitted changes
2. **Always create feature/bugfix branches** for development work
3. **Document your work** with appropriate markdown files
4. **Push branches to GitHub** for backup and collaboration
5. **Use pull requests** for merging to main branch
6. **Follow testing requirements** before merging

---

**Last Checked**: $(date)
**Workflow Version**: 1.0
**Git Standards**: Enforced for andrefortin account
