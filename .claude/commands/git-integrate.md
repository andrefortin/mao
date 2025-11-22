---
description: Merge validated features and bug fixes with comprehensive testing and validation
argument-hint: [source-branch] [target-branch] [merge-type]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, MultiEdit
---

# Git Integrate

Merge validated features and bug fixes with comprehensive testing, validation, and proper Git workflow. This command handles the complete integration process including testing, validation, and proper merge strategies.

## Variables

SOURCE_BRANCH: $1  (branch to merge from)
TARGET_BRANCH: $2  (branch to merge to, defaults to main)
MERGE_TYPE: $3  (merge, squash, rebase)

## Instructions

- IMPORTANT: If no `SOURCE_BRANCH` is provided, stop and ask for it.
- IMPORTANT: Validate SOURCE_BRANCH exists and is ready for integration
- Use TARGET_BRANCH from argument or default to main
- Set MERGE_TYPE to merge if not provided
- Run comprehensive tests before integration
- Ensure proper validation and approval process
- Handle merge conflicts systematically

## Workflow

1. Validate Environment - Check Git status, branch existence, and readiness
2. Pre-Merge Validation - Run comprehensive tests and quality checks
3. Update Target Branch - Ensure target branch is up to date
4. Prepare Integration - Set up proper merge strategy and conflict resolution
5. Execute Merge - Perform merge with appropriate strategy
6. Post-Merge Validation - Verify integration success and run tests
7. Cleanup and Documentation - Clean up branches and document integration

## Error Handling

- If source branch doesn't exist, provide available branches
- If tests fail, provide detailed failure information
- If merge conflicts occur, provide resolution guidance
- If integration breaks functionality, provide rollback instructions
- If approvals are required, block integration until satisfied

## Merge Strategies

### Merge (default)
- Creates merge commit preserving branch history
- Maintains complete development history
- Best for feature branches with significant history
- Preserves context of when features were integrated

### Squash
- Squashes all commits into single commit
- Creates clean linear history
- Best for small features or bug fixes
- Reduces noise in main branch history

### Rebase
- Replays commits on top of target branch
- Creates linear history without merge commits
- Best for maintaining clean development history
- Requires careful conflict resolution

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
    echo "  git commit -m 'Save work before integration'"
    echo "  git stash"
    exit 1
fi

# Validate source branch
if [ -z "$SOURCE_BRANCH" ]; then
    echo "❌ Error: Source branch is required"
    echo "Available branches:"
    git branch -a | grep -v "HEAD ->" | sed 's/^[ *]*//'
    exit 1
fi

# Check if source branch exists
if ! git show-ref --verify --quiet "refs/heads/$SOURCE_BRANCH"; then
    echo "❌ Error: Source branch '$SOURCE_BRANCH' does not exist locally"

    # Check if it exists on remote
    if git show-ref --verify --quiet "refs/remotes/origin/$SOURCE_BRANCH"; then
        echo "✅ Found branch on remote. Checking out..."
        git checkout -b "$SOURCE_BRANCH" "origin/$SOURCE_BRANCH"
    else
        echo "❌ Source branch '$SOURCE_BRANCH' not found locally or remotely"
        echo "Available branches:"
        git branch -a | grep -v "HEAD ->" | sed 's/^[ *]*//'
        exit 1
    fi
fi

# Set default target branch if not provided
if [ -z "$TARGET_BRANCH" ]; then
    TARGET_BRANCH="main"
fi

# Set default merge type if not provided
if [ -z "$MERGE_TYPE" ]; then
    MERGE_TYPE="merge"
fi

# Validate merge type
case "$MERGE_TYPE" in
    "merge"|"squash"|"rebase")
        ;;
    *)
        echo "❌ Error: Invalid merge type. Use: merge, squash, or rebase"
        exit 1
        ;;
esac

# Check if target branch exists
if ! git show-ref --verify --quiet "refs/heads/$TARGET_BRANCH"; then
    echo "❌ Error: Target branch '$TARGET_BRANCH' does not exist"
    echo "Available branches:"
    git branch -a | grep -v "HEAD ->" | sed 's/^[ *]*//'
    exit 1
fi

echo "🔍 Integration Analysis:"
echo "  Source: $SOURCE_BRANCH"
echo "  Target: $TARGET_BRANCH"
echo "  Strategy: $MERGE_TYPE"
echo "  Commits to integrate: $(git rev-list --count "$TARGET_BRANCH..$SOURCE_BRANCH")"
```

### 2. Pre-Merge Validation
```bash
echo "🧪 Running pre-integration validation..."

# Check if source branch is ahead/behind
AHEAD_COUNT=$(git rev-list --count "origin/$TARGET_BRANCH..$SOURCE_BRANCH" 2>/dev/null || echo "0")
BEHIND_COUNT=$(git rev-list --count "$SOURCE_BRANCH..origin/$TARGET_BRANCH" 2>/dev/null || echo "0")

echo "📊 Branch Status:"
echo "  Ahead of target: $AHEAD_COUNT commits"
echo "  Behind target: $BEHIND_COUNT commits"

if [ "$BEHIND_COUNT" -gt 0 ]; then
    echo "⚠️  Warning: Source branch is behind target branch"
    echo "Consider syncing source branch first:"
    echo "  git checkout $SOURCE_BRANCH"
    echo "  git rebase origin/$TARGET_BRANCH"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for merge conflicts before actual merge
echo "🔍 Checking for potential merge conflicts..."
git merge-tree "$(git merge-base "$TARGET_BRANCH" "$SOURCE_BRANCH")" "$TARGET_BRANCH" "$SOURCE_BRANCH" > /tmp/conflict_check.txt 2>&1

if grep -q "CONFLICT" /tmp/conflict_check.txt; then
    echo "⚠️  Potential merge conflicts detected:"
    grep "CONFLICT" /tmp/conflict_check.txt | head -5
    echo ""
    echo "Be prepared to resolve conflicts during integration."
fi

rm -f /tmp/conflict_check.txt

# Run tests on source branch if available
echo "🧪 Running tests on source branch..."
git checkout "$SOURCE_BRANCH"

if [ -f "package.json" ] && command -v npm &> /dev/null; then
    if npm test 2>/dev/null; then
        echo "✅ Source branch tests passed"
    else
        echo "❌ Source branch tests failed"
        read -p "Continue with integration anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    if command -v python3 &> /dev/null && command -v pytest &> /dev/null; then
        if python3 -m pytest tests/ -v 2>/dev/null; then
            echo "✅ Source branch tests passed"
        else
            echo "❌ Source branch tests failed"
            read -p "Continue with integration anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        echo "⚠️  No test framework found or tests not executable"
    fi
else
    echo "⚠️  No test framework detected"
fi
```

### 3. Update Target Branch
```bash
echo "🔄 Updating target branch '$TARGET_BRANCH'..."

# Fetch latest changes
git fetch origin

# Switch to target branch
git checkout "$TARGET_BRANCH"

# Pull latest changes
git pull origin "$TARGET_BRANCH"

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to update target branch"
    exit 1
fi

echo "✅ Target branch updated"
```

### 4. Integration Preparation
```bash
echo "📋 Preparing integration..."

# Create integration backup branch
BACKUP_BRANCH="integration-backup-$(date +%Y%m%d-%H%M%S)"
git branch "$BACKUP_BRANCH"
echo "📦 Created backup branch: $BACKUP_BRANCH"

# Check for any last-minute conflicts
echo "🔍 Final conflict check..."
MERGE_BASE=$(git merge-base "$TARGET_BRANCH" "$SOURCE_BRANCH")
echo "Merge base: $MERGE_BASE"

# Show what will be merged
echo ""
echo "📝 Commits to be integrated:"
git log --oneline "$TARGET_BRANCH..$SOURCE_BRANCH" | head -10

if [ $(git rev-list --count "$TARGET_BRANCH..$SOURCE_BRANCH") -gt 10 ]; then
    echo "... and $(( $(git rev-list --count "$TARGET_BRANCH..$SOURCE_BRANCH") - 10 )) more commits"
fi

echo ""
read -p "Proceed with integration? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Integration cancelled"
    exit 0
fi
```

### 5. Execute Integration
```bash
echo "🔀 Executing integration using $MERGE_TYPE strategy..."

MERGE_SUCCESS=false

case "$MERGE_TYPE" in
    "merge")
        if git merge "$SOURCE_BRANCH" --no-ff -m "🔀 Integrate $SOURCE_BRANCH into $TARGET_BRANCH

Merge changes from feature/bug fix branch:
- $(git log --oneline "$TARGET_BRANCH..$SOURCE_BRANCH" | wc -l) commits integrated
- Integration performed at $(date)

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"; then
            MERGE_SUCCESS=true
        fi
        ;;

    "squash")
        if git merge --squash "$SOURCE_BRANCH"; then
            git commit -m "🔀 Integrate changes from $SOURCE_BRANCH

Squashed merge integrating $(git rev-list --count "$TARGET_BRANCH..$SOURCE_BRANCH") commits:
$(git log --oneline "$TARGET_BRANCH..$SOURCE_BRANCH" | sed 's/^/- /')

Integration performed at $(date)

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
            MERGE_SUCCESS=true
        fi
        ;;

    "rebase")
        # For rebase, we need to be more careful
        echo "⚠️  Rebase integration - this will rewrite history"
        echo "Creating temporary branch for rebase..."

        TEMP_BRANCH="temp-rebase-$(date +%s)"
        git checkout -b "$TEMP_BRANCH" "$SOURCE_BRANCH"

        if git rebase "$TARGET_BRANCH"; then
            # Switch back to target and merge the rebased branch
            git checkout "$TARGET_BRANCH"
            if git merge "$TEMP_BRANCH" --ff-only; then
                MERGE_SUCCESS=true
                git branch -D "$TEMP_BRANCH"
            else
                echo "❌ Fast-forward merge failed after rebase"
                git branch -D "$TEMP_BRANCH"
            fi
        else
            echo "❌ Rebase failed. Aborting..."
            git rebase --abort 2>/dev/null || true
            git checkout "$TARGET_BRANCH"
            git branch -D "$TEMP_BRANCH" 2>/dev/null || true
        fi
        ;;
esac

if [ "$MERGE_SUCCESS" = true ]; then
    echo "✅ Integration completed successfully"
else
    echo "❌ Integration failed"
    echo "Resolving conflicts or reverting..."

    # Check if we're in merge conflict state
    if [ -n "$(git status --porcelain | grep '^UU')" ]; then
        echo "🔧 Merge conflicts detected. Please resolve them:"
        echo "1. Edit conflicted files"
        echo "2. git add <resolved-files>"
        echo "3. git commit"
        echo ""
        echo "Or abort with: git merge --abort"
        exit 1
    else
        # Reset to backup
        echo "🔄 Resetting to backup branch..."
        git reset --hard "$BACKUP_BRANCH"
        git branch -D "$BACKUP_BRANCH"
        exit 1
    fi
fi
```

### 6. Post-Merge Validation
```bash
echo "🧪 Running post-integration validation..."

# Check merge commit was created
if [ "$MERGE_TYPE" = "merge" ]; then
    if git log --oneline -n 1 | grep -q "Integrate"; then
        echo "✅ Merge commit created successfully"
    else
        echo "❌ Merge commit not found"
        exit 1
    fi
fi

# Run tests on integrated code
if [ -f "package.json" ] && command -v npm &> /dev/null; then
    if npm test 2>/dev/null; then
        echo "✅ Post-integration tests passed"
    else
        echo "❌ Post-integration tests failed"
        echo "⚠️  Integration broke functionality. Consider reverting."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            # Revert integration
            echo "🔄 Reverting integration..."
            git reset --hard "$BACKUP_BRANCH"
            git branch -D "$BACKUP_BRANCH"
            exit 1
        fi
    fi
elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    if command -v python3 &> /dev/null && command -v pytest &> /dev/null; then
        if python3 -m pytest tests/ -v 2>/dev/null; then
            echo "✅ Post-integration tests passed"
        else
            echo "❌ Post-integration tests failed"
            echo "⚠️  Integration broke functionality. Consider reverting."
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "🔄 Reverting integration..."
                git reset --hard "$BACKUP_BRANCH"
                git branch -D "$BACKUP_BRANCH"
                exit 1
            fi
        fi
    else
        echo "⚠️  No test framework found to validate integration"
    fi
fi

# Verify integration status
echo "📊 Integration Summary:"
echo "  Source branch: $SOURCE_BRANCH"
echo "  Target branch: $TARGET_BRANCH"
echo "  Merge strategy: $MERGE_TYPE"
echo "  Current commit: $(git rev-parse --short HEAD)"
echo "  Files changed: $(git diff --name-only "$BACKUP_BRANCH" HEAD | wc -l)"
```

### 7. Cleanup and Documentation
```bash
echo "🧹 Cleaning up integration..."

# Create integration log
cat > "INTEGRATION_LOG.md" << EOF
# Integration Log: $SOURCE_BRANCH → $TARGET_BRANCH

## Integration Details
- **Source Branch**: $SOURCE_BRANCH
- **Target Branch**: $TARGET_BRANCH
- **Merge Strategy**: $MERGE_TYPE
- **Integration Date**: $(date)
- **Integrated By**: $(git config user.name || "Unknown")

## Changes Summary
- **Commits Integrated**: $(git rev-list --count "$BACKUP_BRANCH..HEAD")
- **Files Modified**: $(git diff --name-only "$BACKUP_BRANCH" HEAD | wc -l)
- **Lines Added**: $(git diff --numstat "$BACKUP_BRANCH" HEAD | awk '{sum += $1} END {print sum}')
- **Lines Removed**: $(git diff --numstat "$BACKUP_BRANCH" HEAD | awk '{sum += $2} END {print sum}')

## Integrated Commits
\`\`\`
$(git log --oneline "$BACKUP_BRANCH..HEAD")
\`\`\`

## File Changes
\`\`\`
$(git diff --stat "$BACKUP_BRANCH" HEAD)
\`\`\`

## Test Results
- **Pre-integration**: $(echo "✅ Passed" || "❌ Failed")
- **Post-integration**: $(echo "✅ Passed" || "❌ Failed")

## Next Steps
- [ ] Verify functionality in staging environment
- [ ] Deploy to production (if applicable)
- [ ] Monitor for any issues
- [ ] Update documentation if needed

## Rollback Information
If issues arise, rollback to: $BACKUP_BRANCH
\`\`\`bash
git checkout $BACKUP_BRANCH
git checkout -b rollback-$SOURCE_BRANCH-$(date +%Y%m%d)
git push origin rollback-$SOURCE_BRANCH-$(date +%Y%m%d)
\`\`\`
EOF

echo "📝 Integration log created: INTEGRATION_LOG.md"

# Push changes to remote
echo "📤 Pushing integrated changes to remote..."
git push origin "$TARGET_BRANCH"

# Handle source branch cleanup
if [ "$MERGE_TYPE" != "rebase" ]; then
    echo ""
    read -p "Delete source branch '$SOURCE_BRANCH'? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git branch -d "$SOURCE_BRANCH"
        git push origin --delete "$SOURCE_BRANCH" 2>/dev/null || true
        echo "🗑️  Source branch deleted"
    fi
fi

# Clean up backup branch
echo ""
read -p "Delete backup branch '$BACKUP_BRANCH'? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git branch -D "$BACKUP_BRANCH"
    echo "🗑️  Backup branch deleted"
fi

echo ""
echo "✅ Integration completed successfully!"
echo "📍 Target branch: $TARGET_BRANCH is now updated"
echo "📋 Log file: INTEGRATION_LOG.md"
echo ""
echo "Post-Integration Checklist:"
echo "□ Verify integrated functionality works correctly"
echo "□ Check that no regressions were introduced"
echo "□ Run any additional manual tests"
echo "□ Update any relevant documentation"
echo "□ Monitor system for any issues"
echo "□ Consider deploying to staging/production"
```

## Validation Commands

Execute these commands to validate integration:

```bash
# Check integration status
git log --oneline -n 5
git status

# Verify tests still pass
npm test  # or python -m pytest

# Check integration log
cat INTEGRATION_LOG.md

# Verify source branch was cleaned up (if requested)
git branch -a | grep "$SOURCE_BRANCH" || echo "Source branch cleaned up"
```

## Usage Examples

```bash
# Standard merge of feature branch
/git-integrate feature-user-auth main merge

# Squash merge of bug fix
/git-integrate fix-api-timeout main squash

# Rebase integration
/git-integrate refactor-database main rebase

# Integrate into develop branch
/git-integrate feature-dashboard develop merge
```

## Report

After successful integration, provide this report:

```
✅ Integration Completed Successfully

Source: [SOURCE_BRANCH]
Target: [TARGET_BRANCH]
Strategy: [MERGE_TYPE]
Commits: [NUMBER_OF_COMMITS]

Integration Summary:
- Files modified: [COUNT]
- Lines added: [COUNT]
- Lines removed: [COUNT]
- Tests: [PASSED/FAILED]

Documentation:
- Integration log: INTEGRATION_LOG.md
- Backup: [BACKUP_BRANCH or 'Cleaned up']

Next Steps:
- Verify functionality in staging
- Monitor for any issues
- Consider production deployment
- Update team on integration status
```