---
description: Create bug fix branches with testing workflow and proper validation
argument-hint: [bug-description] [issue-number] [severity]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, MultiEdit
---

# Git Fix

Create bug fix branches with comprehensive testing, validation, and proper Git workflow. This command handles bug reproduction, testing setup, and systematic bug fixing process.

## Variables

BUG_DESCRIPTION: $1
ISSUE_NUMBER: $2  (optional, GitHub issue number)
SEVERITY: $3  (critical, high, medium, low)
BRANCH_PREFIX: `fix/`

## Instructions

- IMPORTANT: If no `BUG_DESCRIPTION` is provided, stop and ask the user to provide it.
- IMPORTANT: Validate BUG_DESCRIPTION is meaningful and descriptive
- Set SEVERITY to medium if not provided
- Ensure working directory is clean before creating new branch
- Pull latest changes from main branch before branching
- Set up bug reproduction test cases
- Create systematic testing approach

## Workflow

1. Validate Environment - Check Git status, bug description validity
2. Analyze Bug - Understand the bug scope and impact assessment
3. Create Bug Branch - Create properly named branch from main
4. Setup Bug Reproduction - Create test cases that reproduce the bug
5. Implement Fix Strategy - Plan systematic approach to fixing
6. Testing Framework - Set up comprehensive testing for the fix
7. Bug Fixing Process - Guide through systematic bug resolution

## Error Handling

- If working directory is not clean, provide options to stash or commit
- If bug description is too vague, ask for more details
- If test environment setup fails, provide alternative approaches
- If bug cannot be reproduced, suggest investigation steps
- If fixing requires breaking changes, flag for additional review

## Bug Severity Classification

### Critical
- Production outage or data loss
- Security vulnerability
- Complete feature failure
- **Workflow**: Immediate attention, emergency fix process

### High
- Major feature broken
- Significant user impact
- Performance degradation
- **Workflow**: Priority fix, comprehensive testing

### Medium
- Minor feature issues
- UI/UX problems
- Edge case failures
- **Workflow**: Standard fix process, targeted testing

### Low
- Cosmetic issues
- Documentation errors
- Minor improvements
- **Workflow**: Normal fix process, basic testing

## Implementation Steps

### 1. Environment Validation and Bug Analysis
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
    echo "  git commit -m 'Save work before creating bug fix branch'"
    echo "  git stash"
    exit 1
fi

# Validate bug description
if [ -z "$BUG_DESCRIPTION" ]; then
    echo "❌ Error: Bug description is required"
    echo "Usage: /git-fix 'Bug description' [issue-number] [severity]"
    exit 1
fi

# Clean and validate bug description for branch naming
BUG_NAME=$(echo "$BUG_DESCRIPTION" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')

if [ ${#BUG_NAME} -lt 3 ]; then
    echo "❌ Error: Bug description too short or invalid"
    exit 1
fi

# Set default severity if not provided
if [ -z "$SEVERITY" ]; then
    SEVERITY="medium"
fi

# Validate severity
case "$SEVERITY" in
    "critical"|"high"|"medium"|"low")
        ;;
    *)
        echo "❌ Error: Invalid severity. Use: critical, high, medium, or low"
        exit 1
        ;;
esac

# Extract issue number if provided
ISSUE_REF=""
if [ -n "$ISSUE_NUMBER" ]; then
    ISSUE_REF="#$ISSUE_NUMBER-"
fi

BRANCH_NAME="$BRANCH_PREFIX$ISSUE_REF$BUG_NAME"

echo "🐛 Bug Analysis:"
echo "  Description: $BUG_DESCRIPTION"
echo "  Branch Name: $BRANCH_NAME"
echo "  Severity: $SEVERITY"
echo "  Issue: ${ISSUE_NUMBER:-'No issue number'}"
```

### 2. Base Branch Preparation
```bash
# Fetch latest changes
echo "📥 Fetching latest changes from remote..."
git fetch origin

# Update main branch
echo "🔄 Updating main branch..."
git checkout main
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to update main branch"
    exit 1
fi

# Check if bug fix branch already exists
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    echo "⚠️  Warning: Branch '$BRANCH_NAME' already exists"
    echo "Checkout existing branch or use different description:"
    echo "  git checkout $BRANCH_NAME"
    read -p "Continue with existing branch? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    git checkout "$BRANCH_NAME"
else
    # Create new bug fix branch
    echo "🌿 Creating bug fix branch '$BRANCH_NAME'..."
    git checkout -b "$BRANCH_NAME"

    # Set up tracking branch
    git push -u origin "$BRANCH_NAME"
fi

echo "✅ Bug fix branch ready: $BRANCH_NAME"
```

### 3. Bug Fix Documentation and Planning
```bash
# Create bug fix documentation
cat > "BUG_FIX_PLAN.md" << EOF
# Bug Fix Plan: $BUG_DESCRIPTION

## Bug Information
- **Description**: $BUG_DESCRIPTION
- **Branch**: $BRANCH_NAME
- **Severity**: $SEVERITY
- **Issue**: ${ISSUE_NUMBER:-'Not linked to issue'}
- **Created**: $(date)
- **Status**: Investigation

## Bug Analysis

### Problem Description
[Describe the bug in detail]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Error Messages
[Include any error messages, stack traces, etc.]

### Impact Assessment
- **Affected Features**: [List affected features]
- **User Impact**: [Describe impact on users]
- **System Impact**: [Describe impact on system]

## Investigation

### Root Cause Analysis
[Investigate and document the root cause]

### Affected Files
[List files that likely need changes]

### Dependencies
[List any dependencies that might be involved]

## Fix Strategy

### Approach
[Describe the approach to fix the bug]

### Changes Required
- [ ] [Change 1]
- [ ] [Change 2]
- [ ] [Change 3]

### Risk Assessment
- **Breaking Changes**: [Yes/No and details]
- **Side Effects**: [Potential side effects]
- **Rollback Plan**: [How to rollback if fix causes issues]

## Testing Plan

### Reproduction Test
- [ ] Create test case that reproduces the bug
- [ ] Verify test fails before fix
- [ ] Verify test passes after fix

### Regression Tests
- [ ] Run existing test suite
- [ ] Add specific regression tests
- [ ] Test related functionality

### Manual Testing
- [ ] Test fix in development environment
- [ ] Test fix in staging environment
- [ ] User acceptance testing

## Implementation Log

$(date): Started bug fix investigation
EOF

echo "📋 Created bug fix plan: BUG_FIX_PLAN.md"
```

### 4. Bug Reproduction Test Setup
```bash
# Create test directory structure
mkdir -p "tests/bug_fixes"

# Create bug reproduction test
TEST_FILE="tests/bug_fixes/test_${BUG_NAME}.py"

if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    # Python project test structure
    cat > "$TEST_FILE" << EOF
"""
Bug Reproduction Test: $BUG_DESCRIPTION

This test reproduces the bug before implementing the fix.
Run this test to verify the bug exists, then implement the fix
and verify the test passes.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# TODO: Import relevant modules for testing
# from your_module import function_that_has_bug

class Test${BUG_NAME^}:
    """
    Test cases for bug: $BUG_DESCRIPTION
    Issue: ${ISSUE_NUMBER:-'Not linked'}
    Severity: $SEVERITY
    """

    def test_bug_reproduction(self):
        """
        Test that reproduces the bug.
        This test should FAIL before the fix is implemented.
        """
        # TODO: Implement test that reproduces the bug
        # Example:
        # result = function_that_has_bug(input_data)
        # assert result == expected_result, "Bug reproduced - function returned wrong result"

        # Placeholder until actual test is implemented
        pytest.skip("Bug reproduction test not yet implemented - add your test here")

    def test_bug_fix(self):
        """
        Test that verifies the bug is fixed.
        This test should PASS after the fix is implemented.
        """
        # TODO: Implement test that verifies the fix
        # Example:
        # result = function_with_fix(input_data)
        # assert result == expected_result, "Bug not fixed - function still returns wrong result"

        # Placeholder until actual test is implemented
        pytest.skip("Bug fix test not yet implemented - add your test here")

    def test_no_regression(self):
        """
        Test to ensure no regression in related functionality.
        """
        # TODO: Add regression tests for related functionality
        pass

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
EOF

    echo "🧪 Created Python reproduction test: $TEST_FILE"
else
    # Generic test template
    cat > "$TEST_FILE" << EOF
# Bug Reproduction Test: $BUG_DESCRIPTION

# Issue: ${ISSUE_NUMBER:-'Not linked'}
# Severity: $SEVERITY

## TODO: Implement bug reproduction test

### Steps to Reproduce
1. [Describe steps to reproduce the bug]
2. [Expected behavior]
3. [Actual behavior]

### Test Commands
\`\`\`bash
# Add commands to reproduce the bug
# Example:
# npm test -- --testNamePattern="Bug Name"
# python -m pytest tests/bug_fixes/test_${BUG_NAME}.py
\`\`\`

### Expected Results
- [What should happen before the fix]
- [What should happen after the fix]

### Actual Results
- [Document what actually happens]
EOF

    echo "🧪 Created bug test template: $TEST_FILE"
fi
```

### 5. Bug Fix Helper Script
```bash
# Create bug fix helper script
cat > "bug-fix-helper.sh" << 'EOF'
#!/bin/bash

# Bug Fix Helper Script

BRANCH_NAME=$(git branch --show-current)
BUG_INFO=$(echo "$BRANCH_NAME" | sed 's/^fix\/\(#.*-\)\?\(.*\)$/\2/')
SEVERITY="medium"  # Default, could be extracted from branch name or config

bug_status() {
    echo "Bug Fix Status: $BUG_INFO"
    echo "Branch: $BRANCH_NAME"
    echo "Modified files: $(git status --porcelain | wc -l)"
    echo "Commits: $(git rev-list --count main..HEAD 2>/dev/null || echo 'N/A')"
    echo "Plan file: $(ls BUG_FIX_PLAN.md 2>/dev/null && echo '✅ Exists' || echo '❌ Missing')"
}

bug_reproduce() {
    echo "🐛 Running bug reproduction tests..."

    if [ -f "tests/bug_fixes/test_${BUG_INFO}.py" ]; then
        if command -v python3 &> /dev/null; then
            python3 -m pytest "tests/bug_fixes/test_${BUG_INFO}.py::Test${BUG_INFO^}::test_bug_reproduction" -v
        else
            echo "❌ Python3 not found. Run tests manually:"
            echo "  python -m pytest tests/bug_fixes/test_${BUG_INFO}.py"
        fi
    else
        echo "❌ Bug reproduction test not found"
        echo "Create the test first in: tests/bug_fixes/test_${BUG_INFO}.py"
    fi
}

bug_fix_test() {
    echo "✅ Running bug fix tests..."

    if [ -f "tests/bug_fixes/test_${BUG_INFO}.py" ]; then
        if command -v python3 &> /dev/null; then
            python3 -m pytest "tests/bug_fixes/test_${BUG_INFO}.py::Test${BUG_INFO^}::test_bug_fix" -v
        else
            echo "❌ Python3 not found. Run tests manually:"
            echo "  python -m pytest tests/bug_fixes/test_${BUG_INFO}.py"
        fi
    else
        echo "❌ Bug fix test not found"
    fi
}

bug_all_tests() {
    echo "🧪 Running all tests..."

    if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
        if command -v python3 &> /dev/null; then
            python3 -m pytest tests/ -v
        elif command -v pytest &> /dev/null; then
            pytest tests/ -v
        else
            echo "❌ pytest not found. Install with: pip install pytest"
        fi
    elif [ -f "package.json" ]; then
        if command -v npm &> /dev/null; then
            npm test
        elif command -v yarn &> /dev/null; then
            yarn test
        else
            echo "❌ Node.js package manager not found"
        fi
    else
        echo "⚠️  No test framework detected. Run tests manually."
    fi
}

bug_commit() {
    if [ -z "$1" ]; then
        echo "Usage: ./bug-fix-helper.sh commit 'Fix description'"
        exit 1
    fi

    echo "📝 Committing bug fix: $1"
    git add .
    git commit -m "fix: $1

Fixes: $BUG_INFO
Severity: $SEVERITY

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

    git push origin "$BRANCH_NAME"
}

bug_sync() {
    echo "🔄 Syncing bug fix with main branch..."
    git fetch origin
    git checkout main
    git pull origin main
    git checkout "$BRANCH_NAME"
    git rebase main

    if [ $? -eq 0 ]; then
        echo "✅ Bug fix synced successfully"
        echo "📤 Pushing updated branch..."
        git push origin "$BRANCH_NAME" --force-with-lease
    else
        echo "❌ Rebase failed. Resolve conflicts and continue:"
        echo "  git rebase --continue"
        echo "  git rebase --abort"
    fi
}

bug_pr() {
    echo "🔗 Creating pull request for bug fix..."

    ISSUE_NUM=$(echo "$BRANCH_NAME" | grep -o '#[0-9]*' | sed 's/#//')
    BODY="## Bug Fix

### Bug Description
$BUG_INFO

### Changes Made
- [Describe the changes made to fix the bug]

### Testing
- [x] Bug reproduction test created and verified to fail
- [x] Fix implemented and verified to pass tests
- [x] Regression tests performed
- [x] Manual testing completed

### Impact Assessment
- **Breaking Changes**: No
- **Performance Impact**: None
- **User Impact**: Resolves reported issue

### Verification Steps
1. [Steps to verify the fix]

## Checklist
- [ ] Bug is properly reproduced in tests
- [ ] Fix addresses the root cause
- [ ] No new bugs introduced
- [ ] Code follows project style guidelines
- [ ] Documentation updated if needed"

    if [ -n "$ISSUE_NUM" ]; then
        BODY="$BODY

Closes #$ISSUE_NUM"
    fi

    gh pr create \
        --title "fix: $BUG_INFO" \
        --body "$BODY" \
        --base main \
        --head "$BRANCH_NAME"

    echo "✅ Pull request created"
}

case "$1" in
    "status")
        bug_status
        ;;
    "reproduce")
        bug_reproduce
        ;;
    "test")
        bug_fix_test
        ;;
    "all")
        bug_all_tests
        ;;
    "commit")
        bug_commit "$2"
        ;;
    "sync")
        bug_sync
        ;;
    "pr")
        bug_pr
        ;;
    *)
        echo "Bug Fix Helper"
        echo "Usage: ./bug-fix-helper.sh [command]"
        echo ""
        echo "Commands:"
        echo "  status    - Show bug fix status"
        echo "  reproduce - Run bug reproduction test (should fail before fix)"
        echo "  test      - Run bug fix test (should pass after fix)"
        echo "  all       - Run all tests"
        echo "  commit    - Commit bug fix with proper message"
        echo "  sync      - Sync with main branch (rebase)"
        echo "  pr        - Create pull request"
        echo ""
        echo "Current bug: $BUG_INFO"
        echo "Severity: $SEVERITY"
        ;;
esac
EOF

chmod +x bug-fix-helper.sh
echo "🛠️  Created bug fix helper script: ./bug-fix-helper.sh"
```

### 6. Initial Commit and Setup
```bash
# Add all created files
git add BUG_FIX_PLAN.md bug-fix-helper.sh
if [ -f "tests/bug_fixes/test_${BUG_NAME}.py" ]; then
    git add "tests/bug_fixes/test_${BUG_NAME}.py"
fi

# Create initial commit
git commit -m "🐛 Initialize bug fix: $BUG_DESCRIPTION

- Set up bug fix branch and documentation
- Create bug reproduction test template
- Add bug fix helper script
- Prepare systematic fix approach

Bug: $BUG_DESCRIPTION
Severity: $SEVERITY
Issue: ${ISSUE_NUMBER:-'Not linked'}

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin "$BRANCH_NAME"

echo ""
echo "✅ Bug fix environment initialized successfully!"
echo "🐛 Bug: $BUG_DESCRIPTION"
echo "🌿 Branch: $BRANCH_NAME"
echo "📋 Plan: BUG_FIX_PLAN.md"
echo "🛠️  Helper: ./bug-fix-helper.sh"
echo ""
echo "Bug Fix Workflow:"
echo "1. 📋 Edit BUG_FIX_PLAN.md with detailed analysis"
echo "2. 🧪 Implement bug reproduction test in tests/bug_fixes/"
echo "3. 🔍 Run ./bug-fix-helper.sh reproduce (should fail)"
echo "4. 🔧 Implement the actual fix"
echo "5. ✅ Run ./bug-fix-helper.sh test (should pass)"
echo "6. 🧪 Run ./bug-fix-helper.sh all (full test suite)"
echo "7. 📝 Commit changes: ./bug-fix-helper.sh commit 'Fixed specific issue'"
echo "8. 🔗 Create PR: ./bug-fix-helper.sh pr"

# Show next steps based on severity
if [ "$SEVERITY" = "critical" ]; then
    echo ""
    echo "🚨 CRITICAL BUG - Immediate Action Required:"
    echo "- Focus on rapid fix implementation"
    echo "- Prepare rollback plan"
    echo "- Consider hotfix deployment strategy"
fi
```

## Validation Commands

Execute these commands to validate bug fix setup:

```bash
# Check branch and files
git status
ls -la BUG_FIX_PLAN.md bug-fix-helper.sh

# Test helper script
./bug-fix-helper.sh status

# Verify test structure
ls -la tests/bug_fixes/

# Check if issue is linked (if issue number provided)
if [ -n "$ISSUE_NUMBER" ]; then
    echo "📋 Remember to update GitHub issue #$ISSUE_NUMBER with progress"
fi
```

## Usage Examples

```bash
# Critical bug with issue number
/git-fix "user authentication fails on password reset" 123 critical

# High severity bug without issue
/git-fix "api timeout on large file uploads" high

# Medium severity bug
/git-fix "ui layout breaks on mobile devices" medium

# Low severity cosmetic issue
/git-fix "typo in error message" low
```

## Report

After successful bug fix environment setup, provide this report:

```
✅ Bug Fix Environment Initialized

Bug: [BUG_DESCRIPTION]
Branch: [BRANCH_NAME]
Severity: [SEVERITY]
Issue: [ISSUE_NUMBER or 'Not linked']

Documentation:
- Bug fix plan: BUG_FIX_PLAN.md
- Helper script: ./bug-fix-helper.sh
- Reproduction test: tests/bug_fixes/test_[BUG_NAME].py

Next Steps:
1. Complete bug analysis in BUG_FIX_PLAN.md
2. Implement reproduction test to confirm bug exists
3. Fix the bug systematically
4. Verify fix with comprehensive testing
5. Create pull request for review

Workflow Commands:
- ./bug-fix-helper.sh reproduce - Test bug reproduction
- ./bug-fix-helper.sh test - Test bug fix
- ./bug-fix-helper.sh commit - Commit with proper message
- ./bug-fix-helper.sh pr - Create pull request
```