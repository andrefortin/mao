# Spec File Organization Guidelines

## Overview
This document outlines the proper organization for specification (spec) files across the multi-agent orchestration project. Each app should maintain its own specs directory containing relevant plans and documentation.

## Directory Structure

### App-Specific Specs
Each application should have its own `specs/` directory:
```
apps/
├── orchestrator_3_stream/
│   └── specs/                 # Plans for orchestrator_3_stream features
├── sec-detective/
│   └── specs/                 # Plans for sec-detective features
├── proxyhub-rotor-pro/
│   └── specs/                 # Plans for proxyhub features
└── [other-apps]/
    └── specs/                 # Plans for respective app features
```

### File Naming Convention
Spec files should follow the pattern: `{feature-name}-plan.md` or `{app-name}-{description}.md`

Examples:
- `orchestrator-chat-width-toggle.md`
- `sec-detective-postgresql-migration.md`
- `proxyhub-claude-code-optimized-readme.md`

## Placement Rules

### ✅ Correct Placement
- App-specific plans go in the app's own `specs/` directory
- Cross-app architectural plans go in the most relevant app's `specs/` directory
- Shared infrastructure plans go in the orchestrator's `specs/` directory

### ❌ Incorrect Placement
- Never place app-specific plans in unrelated app directories
- Avoid centralized specs that mix multiple app plans
- Don't create specs in root-level `specs/` directories for app-specific features

## Creating New Spec Files

When creating a new spec file:

1. **Determine the primary app**: Identify which app the feature belongs to
2. **Use the correct directory**: Place the file in `apps/{app-name}/specs/`
3. **Follow naming convention**: Use descriptive, kebab-case names
4. **Use the template**: Follow the established plan format with sections:
   - Task Description
   - Objective
   - Problem Statement (if applicable)
   - Solution Approach (if applicable)
   - Relevant Files
   - Implementation Phases (if applicable)
   - Step by Step Tasks
   - Testing Strategy (if applicable)
   - Acceptance Criteria
   - Validation Commands
   - Notes

## Examples

### Sec-Detective Example
```bash
# Correct: Sec-detective database migration plan
touch apps/sec-detective/specs/sec-detective-database-migration-plan.md

# Incorrect: Placing sec-detective plan in orchestrator directory
touch apps/orchestrator_3_stream/specs/sec-detective-something.md  # ❌
```

### ProxyHub Example
```bash
# Correct: ProxyHub feature plan
touch apps/proxyhub-rotor-pro/specs/proxyhub-load-balancing-plan.md

# Incorrect: Placing proxyhub plan in sec-detective directory
touch apps/sec-detective/specs/proxyhub-something.md  # ❌
```

### Orchestrator Example
```bash
# Correct: Orchestrator feature plan
touch apps/orchestrator_3_stream/specs/orchestrator-agent-management-plan.md

# Correct: Cross-app infrastructure affecting orchestrator
touch apps/orchestrator_3_stream/specs/shared-authentication-plan.md
```

## Validation Commands

### Check for Misplaced Files
```bash
# Find misplaced sec-detective files
find /home/andre/batcave/mao -name "*sec-detective*" -name "*.md" -not -path "*/apps/sec-detective/*"

# Find misplaced proxyhub files
find /home/andre/batcave/mao -name "*proxyhub*" -name "*.md" -not -path "*/apps/proxyhub-rotor-pro/*"

# Find misplaced orchestrator files
find /home/andre/batcave/mao -name "*orchestrator*" -name "*.md" -not -path "*/apps/orchestrator_3_stream/*"
```

### Verify Directory Structure
```bash
# Check all apps have specs directories
find /home/andre/batcave/mao/apps -maxdepth 2 -name "specs" -type d

# List contents of each specs directory
for dir in /home/andre/batcave/mao/apps/*/specs; do
    echo "=== $dir ==="
    ls -la "$dir" | grep "\.md$" || echo "  No spec files"
    echo
done
```

## Migration Process

When moving misplaced spec files:

1. **Identify target app**: Determine which app the spec belongs to
2. **Verify target directory**: Ensure the target app has a `specs/` directory
3. **Move the file**: Use `mv` to preserve permissions and timestamps
4. **Validate integrity**: Check the file after moving
5. **Update references**: Update any internal file references
6. **Clean up**: Remove any empty directories left behind

## Best Practices

1. **Be specific**: Use descriptive names that clearly indicate the app and feature
2. **Stay organized**: Keep related specs together in the appropriate app directory
3. **Document dependencies**: If a spec affects multiple apps, note it in the spec
4. **Regular cleanup**: Periodically review and clean up misplaced files
5. **Consistent formatting**: Use the established template and formatting

## Tools and Automation

### Validation Script
Create a script to validate spec file organization:

```bash
#!/bin/bash
# validate-spec-organization.sh

echo "🔍 Checking spec file organization..."

# Check for common misplaced patterns
misplaced_files=$(find /home/andre/batcave/mao -name "*sec-detective*" -name "*.md" -not -path "*/apps/sec-detective/*")

if [ -n "$misplaced_files" ]; then
    echo "❌ Found misplaced sec-detective files:"
    echo "$misplaced_files"
    exit 1
fi

misplaced_files=$(find /home/andre/batcave/mao -name "*proxyhub*" -name "*.md" -not -path "*/apps/proxyhub-rotor-pro/*")

if [ -n "$misplaced_files" ]; then
    echo "❌ Found misplaced proxyhub files:"
    echo "$misplaced_files"
    exit 1
fi

echo "✅ All spec files are properly organized!"
```

### Pre-commit Hook
Add a pre-commit hook to validate spec file organization:

```bash
#!/bin/sh
# .git/hooks/pre-commit

# Check for misplaced spec files
if git diff --cached --name-only | grep -E "\.md$" | grep -v "/specs/"; then
    echo "⚠️  Consider if this markdown file should be in a specs/ directory"
fi

# Validate spec file organization in staged files
./scripts/validate-spec-organization.sh
```

## Troubleshooting

### Common Issues

1. **Files in wrong directory**: Use the validation commands to identify and fix
2. **Missing specs directory**: Create `mkdir apps/{app-name}/specs/`
3. **Naming inconsistencies**: Rename files to follow the established pattern
4. **Broken references**: Update internal links after moving files

### Getting Help

- Check existing examples in correctly organized directories
- Follow the naming convention strictly
- Use validation scripts to catch issues early
- Ask for clarification if unsure about placement

## Maintenance

This document should be:
- Reviewed periodically for accuracy
- Updated when new apps are added
- Shared with team members to ensure consistent practices
- Used as reference for code reviews and pull requests
