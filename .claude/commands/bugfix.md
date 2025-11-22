---
description: Create a bugfix branch following proper Git workflow with testing requirements
argument-hint: [bug-description] [app-name] [severity]
model: claude-sonnet-4-5-20250929
---

# Bugfix Branch Development

## Purpose

Create a bugfix branch with proper testing requirements and workflow. Bug fixes must be developed in separate branches, thoroughly tested, and only merged after validation.

## Variables

BUG_DESCRIPTION: $1
APP_NAME: $2 (optional, defaults to current directory)
SEVERITY: $3 (critical, high, medium, low - defaults to medium)
GITHUB_USERNAME: andrefortin

## Instructions

- Bug fixes must be developed in separate branches
- Higher severity bugs require more thorough testing
- All bug fixes need regression testing before merge
- Document bug details and fix verification

## Workflow

### Step 1: Validate Environment and Bug Details
```bash
# Check if we're in a Git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a Git repository"
    exit 1
fi

# Set default severity if not provided
if [ -z "$SEVERITY" ]; then
    SEVERITY="medium"
fi

# Create safe branch name from bug description
BUG_SAFE_NAME=$(echo "$BUG_DESCRIPTION" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')
BUG_BRANCH="bugfix/$BUG_SAFE_NAME"

echo "Creating bugfix branch for: $BUG_DESCRIPTION"
echo "Severity: $SEVERITY"
echo "Branch name: $BUG_BRANCH"
```

### Step 2: Determine App Directory
```bash
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

### Step 3: Create Bugfix Branch
```bash
# Switch to develop branch first
git checkout develop

# Pull latest changes
git pull origin develop

# Create and switch to bugfix branch
git checkout -b $BUG_BRANCH

echo "Created bugfix branch: $BUG_BRANCH"
```

### Step 4: Setup Bug Fix Environment
```bash
# Create bug documentation
BUG_DOC="bugs/bugfix-$BUG_SAFE_NAME.md"
mkdir -p bugs

cat > $BUG_DOC << 'BUGDOC'
# Bug Fix: $BUG_SAFE_NAME

## Bug Description
$BUG_DESCRIPTION

## Severity
$SEVERITY

## Environment
- **App**: $(basename $(pwd))
- **Branch**: $BUG_BRANCH
- **Date**: $(date)

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Expected Behavior
[Describe what should happen]

## Actual Behavior
[Describe what actually happens]

## Root Cause Analysis
[Analysis of the bug's cause]

## Fix Implementation
### Code Changes
- [ ] File 1: [description of change]
- [ ] File 2: [description of change]

### Testing Plan
- [ ] Reproduce bug before fix
- [ ] Implement fix
- [ ] Verify fix resolves issue
- [ ] Regression testing
- [ ] Edge case testing

## Verification Steps
1. [ ] Step to verify fix
2. [ ] Additional verification
3. [ ] Performance impact check

## Test Results
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Regression tests pass

## Merge Readiness
- [ ] Code reviewed
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Ready for merge to main

## Related Issues
[Link to any related issues or pull requests]
BUGDOC

echo "Created bug documentation: $BUG_DOC"
```

### Step 5: Severity-Based Requirements
```bash
# Set testing requirements based on severity
case $SEVERITY in
    "critical")
        TESTING_REQUIREMENTS="Critical bugs require:
- Full regression test suite
- Performance impact analysis
- Security review
- Multiple environment testing
- Code review from senior developer"
        ;;
    "high")
        TESTING_REQUIREMENTS="High severity bugs require:
- Regression testing for affected modules
- Integration testing
- Performance check
- Code review"
        ;;
    "medium")
        TESTING_REQUIREMENTS="Medium severity bugs require:
- Unit tests for fixed code
- Integration testing
- Manual verification"
        ;;
    "low")
        TESTING_REQUIREMENTS="Low severity bugs require:
- Basic unit tests
- Manual verification
- Documentation update if needed"
        ;;
esac

echo "Testing requirements for $SEVERITY severity:"
echo "$TESTING_REQUIREMENTS"
```

### Step 6: Development Environment Setup
```bash
# Setup development environment based on app type
if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
    echo "Python app detected - setting up environment"
    if [ ! -d "venv" ]; then
        python -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt 2>/dev/null || pip install -r pyproject.toml 2>/dev/null
    
    # Run existing tests to establish baseline
    if [ -d "tests" ]; then
        echo "Running baseline tests..."
        pytest tests/ --tb=short || echo "Some tests failed - this may be related to the bug"
    fi
fi

if [ -f "package.json" ]; then
    echo "Node.js app detected - setting up environment"
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    # Run existing tests to establish baseline
    if npm run test --silent 2>/dev/null; then
        echo "Baseline tests passed"
    else
        echo "Some tests failed - this may be related to the bug"
    fi
fi
```

### Step 7: Push Branch to GitHub
```bash
# Add bug documentation
git add $BUG_DOC
git commit -m "docs: Add bug documentation for $BUG_SAFE_NAME"

# Push to GitHub
git push -u origin $BUG_BRANCH

echo "Pushed bugfix branch to GitHub: origin/$BUG_BRANCH"
```

## Report

### Bugfix Branch Created
- **Bug Description**: $BUG_DESCRIPTION
- **Severity**: $SEVERITY
- **Branch**: $BUG_BRANCH
- **GitHub URL**: https://github.com/$GITHUB_USERNAME/[repo-name]/tree/$BUG_BRANCH
- **Bug Documentation**: $BUG_DOC

### Testing Requirements
$TESTING_REQUIREMENTS

### Development Environment
- **Git Status**: Ready for bug fix development
- **Baseline Tests**: [Results of initial test run]
- **Dependencies**: Installed and verified

### Bug Fix Process
1. **Analyze Bug**: Use $BUG_DOC to document findings
2. **Reproduce Bug**: Follow steps in documentation
3. **Implement Fix**: Make necessary code changes
4. **Test Fix**: Follow testing requirements for severity
5. **Document Changes**: Update bug documentation
6. **Request Review**: Create pull request when ready

### Quality Gates Before Merge
- **Bug Reproduced**: ✓ Verified before fix
- **Fix Verified**: ✓ Bug no longer occurs
- **Tests Pass**: ✓ All test requirements met
- **No Regressions**: ✓ Existing functionality intact
- **Documentation**: ✓ Updated as needed

## Error Handling

### Branch Creation Issues
- If branch exists: `git checkout $BUG_BRANCH && git pull origin $BUG_BRANCH`
- If develop branch issues: Ensure develop branch exists and is up to date

### Testing Failures
- Investigate test failures - they may be related to the bug
- Document test failures in bug report
- Fix test failures as part of bug fix if needed

### Merge Conflicts
- Resolve conflicts carefully
- Test resolution thoroughly
- Document conflict resolution in bug report

## Bug Fix Best Practices

### Code Quality
- Make minimal, focused changes
- Follow existing code patterns and conventions
- Add comments for complex bug fixes
- Consider edge cases in fix implementation

### Testing Strategy
- Write tests that would have caught the bug
- Test fix with various input scenarios
- Consider performance implications of fix
- Test in multiple environments if applicable

### Documentation
- Clearly explain root cause in bug report
- Document fix approach and reasoning
- Update any related documentation
- Note any breaking changes or migration needs

## Commands for Bug Fix Development

- `/status` - Check current Git status and branch info
- `/test` - Run application tests
- `/commit [message]` - Commit bug fix changes
- `/merge` - Create pull request when bug fix is ready
- `/hotfix [description]` - For critical production bugs (creates hotfix from main)

## Severity Guidelines

- **Critical**: Production downtime, data loss, security vulnerabilities
- **High**: Major functionality broken, significant user impact
- **Medium**: Minor functionality issues, some user impact
- **Low**: Cosmetic issues, minor inconveniences

Remember: All bug fixes must pass their severity-specific testing requirements before merging to main branch.
