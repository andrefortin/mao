---
description: Create pull request to merge tested branch to main following proper Git workflow
argument-hint: [branch-name] [merge-type]
model: claude-sonnet-4-5-20250929
---

# Merge Branch to Main

## Purpose

Create a pull request to merge a tested branch (feature, bugfix, etc.) to main branch following proper Git workflow and quality gates.

## Variables

BRANCH_NAME: $1 (required, branch to merge)
MERGE_TYPE: $2 (squash|merge|rebase, defaults to squash)
GITHUB_USERNAME: andrefortin

## Instructions

- Never merge branches directly to main without pull request
- Ensure proper testing has been completed before merge
- Follow your organization's code review standards
- All branches must be tested before merging to main

## Workflow

### Step 1: Validate Environment
```bash
# Check if we are in a Git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a Git repository"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Verify target branch exists
if ! git show-ref --quiet refs/heads/$BRANCH_NAME; then
    echo "Error: Branch '$BRANCH_NAME' does not exist"
    echo "Available branches:"
    git branch -a
    exit 1
fi

# Check if GitHub CLI is configured
if ! gh auth status > /dev/null 2>&1; then
    echo "Error: GitHub CLI not authenticated"
    echo "Run: gh auth login"
    exit 1
fi
```

### Step 2: Branch Status and Quality Checks
```bash
# Switch to branch to be merged
git checkout $BRANCH_NAME

# Pull latest changes
git pull origin $BRANCH_NAME

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Uncommitted changes found"
    echo "Commit or stash changes before creating pull request"
    git status
    exit 1
fi

# Get branch information
BRANCH_AUTHOR=$(git log -1 --pretty=format:'%an' $BRANCH_NAME)
BRANCH_CREATED=$(git log -1 --pretty=format:'%ci' $BRANCH_NAME)
BRANCH_UPDATED=$(git log -1 --pretty=format:'%cr' $BRANCH_NAME)

echo "Branch Information:"
echo "  Branch: $BRANCH_NAME"
echo "  Author: $BRANCH_AUTHOR"
echo "  Created: $BRANCH_CREATED"
echo "  Updated: $BRANCH_UPDATED"
```

### Step 3: Set Merge Type
```bash
# Set default merge type
if [ -z "$MERGE_TYPE" ]; then
    MERGE_TYPE="squash"
fi

echo "Selected merge type: $MERGE_TYPE"

# Validate merge type
case $MERGE_TYPE in
    "squash"|"merge"|"rebase")
        echo "✓ Merge type '$MERGE_TYPE' is valid"
        ;;
    *)
        echo "Error: Invalid merge type '$MERGE_TYPE'"
        echo "Valid options: squash, merge, rebase"
        exit 1
        ;;
esac
```

### Step 4: Check Testing Status
```bash
# Look for testing evidence
TEST_EVIDENCE=""

# Check for test commands in repository
if [ -f "package.json" ]; then
    if jq -e '.scripts.test' package.json > /dev/null 2>&1; then
        TEST_EVIDENCE="Node.js test script found in package.json"
        echo "✓ Test command found: npm test"
    fi
fi

if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
    if [ -d "tests" ] || [ -d "test" ]; then
        TEST_EVIDENCE="Python test directory found"
        echo "✓ Test directory found: tests/"
    fi
fi

# Check for GitHub Actions test workflows
if [ -d ".github/workflows" ]; then
    TEST_WORKFLOWS=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | grep -i test)
    if [ -n "$TEST_WORKFLOWS" ]; then
        TEST_EVIDENCE="$TEST_EVIDENCE - GitHub Actions test workflows found"
    fi
fi

echo "Testing Evidence: $TEST_EVIDENCE"
if [ -z "$TEST_EVIDENCE" ]; then
    echo "⚠️ Warning: No test evidence found"
    echo "Consider running tests before creating pull request"
fi
```

### Step 5: Generate Pull Request Content
```bash
# Generate branch description
BRANCH_DESCRIPTION=$(git log --format=%s origin/develop..$BRANCH_NAME | head -1)
COMMIT_COUNT=$(git rev-list --count origin/develop..$BRANCH_NAME)
CHANGED_FILES=$(git diff --name-only origin/develop..$BRANCH_NAME | wc -l)

# Generate pull request title
PR_TITLE="Merge $BRANCH_NAME to main"

# Generate pull request body
PR_BODY=$(cat << ENDMSG
## Pull Request: Merge $BRANCH_NAME

### Summary
$BRANCH_DESCRIPTION

### Changes Overview
- **Commits**: $COMMIT_COUNT commits included
- **Files Changed**: $CHANGED_FILES files modified
- **Merge Type**: $MERGE_TYPE
- **Testing**: $([ -n "$TEST_EVIDENCE" ] && echo "Testing evidence found" || echo "Testing status unknown")

### Checklist
- [ ] Code follows project standards
- [ ] Tests pass locally
- [ ] Documentation updated (if needed)
- [ ] No breaking changes
- [ ] Performance impact considered

### Type of Change
- [ ] Bugfix (fixes an issue without breaking changes)
- [ ] Feature (adds new functionality)
- [ ] Breaking Change (changes existing functionality)
- [ ] Documentation (updates documentation only)
- [ ] Refactor (code restructuring without behavior change)
- [ ] Tests (adds/modifies tests)
- [ ] Build/CI (build system or CI changes)

### Additional Context
Add any other context about the pull request here.
ENDMSG
)

echo "Generated pull request with:"
echo "  - Commit count: $COMMIT_COUNT"
echo "  - Files changed: $CHANGED_FILES"
echo "  - Merge type: $MERGE_TYPE"
```

### Step 6: Create Pull Request
```bash
# Determine target branch
TARGET_BRANCH="main"
if ! git show-ref --quiet refs/heads/main; then
    TARGET_BRANCH="develop"
fi

echo "Target branch: $TARGET_BRANCH"

# Create draft pull request
echo "Creating draft pull request for review..."
PR_URL=$(gh pr create --title "$PR_TITLE" \
  --body "$PR_BODY" \
  --base $TARGET_BRANCH \
  --head $BRANCH_NAME \
  --draft)

echo "✓ Draft pull request created: $PR_URL"

# Open pull request in browser
echo "Opening pull request in browser for final review..."
gh pr view --web $PR_URL

echo "Please review the pull request and remove draft status when ready."
echo "Ensure all tests pass and code review requirements are met."
```

### Step 7: Post-Creation Information
```bash
echo "=== Post-Creation Actions ==="
echo ""
echo "✅ Pull request created: $PR_URL"
echo ""
echo "To remove draft status when ready:"
echo "  gh pr edit \$PR_URL --draft=false"
echo ""
echo "To merge when ready:"
echo "  gh pr merge \$PR_URL --$MERGE_TYPE --delete-branch"
```

## Report

### Pull Request Created Successfully
- **PR URL**: $PR_URL
- **Source Branch**: $BRANCH_NAME
- **Target Branch**: $TARGET_BRANCH
- **Merge Type**: $MERGE_TYPE
- **Status**: Draft (ready for review)

### Branch Analysis
- **Commits to Merge**: $COMMIT_COUNT
- **Files Changed**: $CHANGED_FILES
- **Testing Evidence**: $([ -n "$TEST_EVIDENCE" ] && echo "Found" || echo "None found")

### Required Actions
1. **Review Pull Request**: Visit $PR_URL and review changes
2. **Complete Testing**: Ensure all tests pass and manual testing is done
3. **Get Code Review**: Request at least one code review
4. **Update Documentation**: Update any affected documentation
5. **Remove Draft Status**: Remove draft status when ready for merge

## Error Handling

### Authentication Issues
```bash
# Check GitHub CLI status
gh auth status

# Re-authenticate if needed
gh auth login
```

### Branch Issues
- **Branch Not Found**: Verify branch name and spelling
- **Merge Conflicts**: Resolve conflicts before creating PR
- **Permission Denied**: Check repository permissions

## Best Practices

### Before Creating PR
- **Testing**: Always run full test suite
- **Documentation**: Update relevant documentation
- **Code Quality**: Ensure code follows project standards
- **Branch Cleanliness**: Keep branch history clean

### Before Merge
- **All Tests Pass**: Never merge with failing tests
- **Code Review**: At least one approval
- **Documentation**: All documentation updated
- **No Breaking Changes**: Or breaking changes documented

Remember: Quality is more important than speed.
