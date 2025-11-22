# Plan: Fix Spec File Organization by App Context

## Task Description
Reorganize spec files to be located in the correct app-specific directories instead of being centralized in unrelated app folders. Currently, spec files for different apps (sec-detective, proxyhub-rotor-pro) are being created in the orchestrator_3_stream specs directory, which creates confusion and makes it difficult to find app-specific plans.

## Objective
Implement a proper spec file organization system where each app has its own specs directory containing only its relevant plan files. Move misplaced spec files to their correct app directories and establish a pattern for future spec file creation.

## Problem Statement
The current spec file organization has several issues:

1. **Wrong Location**: Spec files are being created in the orchestrator_3_stream specs directory regardless of which app they're for
2. **Confusion**: Developers can't easily find spec files for specific apps
3. **Poor Organization**: Mixed app plans in a single directory breaks the principle of separation of concerns
4. **Scalability Issues**: As more apps are added, the centralized approach becomes unmanageable
5. **Maintenance Difficulties**: Hard to track which plans belong to which apps

## Solution Approach
Implement an app-centric spec organization system where:

1. **App-Specific Directories**: Each app has its own `specs/` directory
2. **Correct File Placement**: Move existing misplaced files to proper app directories
3. **Creation Pattern**: Establish clear guidelines for where to create new spec files
4. **Validation**: Implement checks to prevent future misplacement
5. **Documentation**: Update documentation to reflect the new organization

## Relevant Files

### Files to Move
- `/home/andre/batcave/mao/apps/orchestrator_3_stream/specs/sec-detective-postgresql-migration.md` → `/home/andre/batcave/mao/apps/sec-detective/specs/`
- `/home/andre/batcave/mao/apps/orchestrator_3_stream/specs/sec-detective-bolt-to-docker-supabase-migration.md` → `/home/andre/batcave/mao/apps/sec-detective/specs/`
- `/home/andre/batcave/mao/apps/orchestrator_3_stream/specs/proxyhub-claude-code-optimized-readme.md` → `/home/andre/batcave/mao/apps/proxyhub-rotor-pro/specs/`

### Files to Keep
- `/home/andre/batcave/mao/apps/orchestrator_3_stream/specs/agent-file-tracking-visualization.md` - Correctly placed for orchestrator_3_stream
- `/home/andre/batcave/mao/apps/orchestrator_3_stream/specs/eventstream-icon-update-plan.md` - Correctly placed for orchestrator_3_stream
- `/home/andre/batcave/mao/apps/orchestrator_3_stream/specs/global-command-input-bar.md` - Correctly placed for orchestrator_3_stream
- `/home/andre/batcave/mao/apps/orchestrator_3_stream/specs/orchestrator-chat-width-toggle.md` - Correctly placed for orchestrator_3_stream
- `/home/andre/batcave/mao/apps/orchestrator_3_stream/specs/responsive-ui-plan.md` - Correctly placed for orchestrator_3_stream

### Files to Create
- Documentation templates for spec organization
- Guidelines for spec file creation
- Validation scripts for proper file placement

## Implementation Phases

### Phase 1: Assessment and Planning
- Identify all misplaced spec files across the project
- Document correct target directories for each file
- Create mapping of files to their proper locations
- Plan the migration strategy

### Phase 2: Directory Preparation
- Ensure all target app directories have specs folders
- Create specs directories where missing
- Set up proper permissions and structure
- Prepare for file migration

### Phase 3: File Migration
- Move misplaced files to correct directories
- Update any internal references or links
- Verify file integrity after migration
- Clean up any empty directories

### Phase 4: Validation and Testing
- Verify all files are in correct locations
- Test that file references still work
- Check that no files were lost or corrupted
- Validate the new organization structure

### Phase 5: Documentation and Guidelines
- Create guidelines for future spec file creation
- Update project documentation
- Establish patterns for spec organization
- Create validation procedures

## Step by Step Tasks

### 1. Inventory Misplaced Spec Files
- Scan all specs directories for misplaced files
- Create a comprehensive list of files that need to be moved
- Identify the target app for each misplaced file
- Document the current and target locations

### 2. Verify Target Directory Structure
- Check that each app has a specs directory
- Create specs directories where they're missing
- Ensure proper permissions are set
- Verify directory structure is consistent

### 3. Move Sec-Detective Spec Files
- Move `sec-detective-postgresql-migration.md` to `/home/andre/batcave/mao/apps/sec-detective/specs/`
- Move `sec-detective-bolt-to-docker-supabase-migration.md` to `/home/andre/batcave/mao/apps/sec-detective/specs/`
- Verify file integrity after move
- Update any internal file references

### 4. Move ProxyHub Spec Files
- Move `proxyhub-claude-code-optimized-readme.md` to `/home/andre/batcave/mao/apps/proxyhub-rotor-pro/specs/`
- Verify file integrity after move
- Update any internal file references
- Check for related files that might also need moving

### 5. Validate File Integrity
- Check that all moved files are intact
- Verify no data corruption occurred during migration
- Test that file permissions are correct
- Confirm file accessibility

### 6. Update File References
- Check for any hardcoded paths in moved files
- Update internal references to new locations
- Verify that relative links still work
- Test any documentation links

### 7. Clean Up Empty Directories
- Remove any now-empty specs directories
- Clean up temporary files created during migration
- Verify directory structure is clean
- Update directory listings

### 8. Create Organization Guidelines
- Document the proper spec file organization pattern
- Create guidelines for where to place new spec files
- Establish naming conventions for spec files
- Write procedures for spec file creation

### 9. Update Project Documentation
- Update any README files that reference old locations
- Modify project setup documentation
- Update development workflows
- Document the new organization structure

### 10. Create Validation Procedures
- Write scripts to validate spec file placement
- Create checks for future spec file creation
- Implement automated validation where possible
- Set up monitoring for proper file organization

### 11. Test New Organization
- Verify that developers can find spec files easily
- Test that the new structure works with existing tools
- Check that file search and discovery works correctly
- Validate that the organization is intuitive

### 12. Communicate Changes
- Inform team members about the new organization
- Update any shared documentation or wikis
- Provide guidance on how to use the new structure
- Answer questions about the changes

## Testing Strategy

### File Migration Testing
- Test file move operations on sample files
- Verify file integrity before and after migration
- Test that file permissions are preserved
- Check that no files are lost during migration

### Reference Testing
- Test that internal file references still work
- Verify that relative links are not broken
- Check that documentation links are updated
- Test any automated tools that use spec files

### Organization Testing
- Test that developers can easily find files
- Verify that the new structure is intuitive
- Check that file naming is consistent
- Test search and discovery functionality

## Acceptance Criteria

1. **All Files Correctly Placed**: Every spec file is in its appropriate app directory
2. **No File Loss**: All original files are preserved and accessible
3. **Integrity Maintained**: No file corruption during migration
4. **References Updated**: All internal file references point to correct locations
5. **Clean Structure**: No misplaced files remain
6. **Documentation Updated**: All documentation reflects new organization
7. **Guidelines Created**: Clear guidelines exist for future spec file creation
8. **Validation Procedures**: Methods exist to validate proper file placement

## Validation Commands

```bash
# Check for misplaced sec-detective files
find /home/andre/batcave/mao -name "*sec-detective*" -name "*.md" -not -path "*/apps/sec-detective/*"

# Check for misplaced proxyhub files  
find /home/andre/batcave/mao -name "*proxyhub*" -name "*.md" -not -path "*/apps/proxyhub-rotor-pro/*"

# Verify correct placement
ls -la /home/andre/batcave/mao/apps/sec-detective/specs/
ls -la /home/andre/batcave/mao/apps/proxyhub-rotor-pro/specs/

# Check orchestrator specs only contains orchestrator files
ls -la /home/andre/batcave/mao/apps/orchestrator_3_stream/specs/ | grep -v "orchestrator"

# Validate file integrity
md5sum /home/andre/batcave/mao/apps/*/specs/*.md
```

## Notes

### Migration Considerations
- Use `mv` command to preserve file permissions and timestamps
- Test file moves on a copy first if possible
- Keep backups of important files
- Document the before/after state for verification

### Future Prevention
- Update the `/plan` command to detect current working directory
- Modify spec creation logic to use app-specific directories
- Add validation to prevent future misplacement
- Create templates that include proper path resolution

### Developer Experience
- Ensure the new organization is intuitive
- Provide clear documentation on where to find files
- Create search patterns that work with the new structure
- Consider developer workflows and tooling integration

### Maintenance
- Set up periodic checks for proper file organization
- Create scripts to validate spec file placement
- Document the organization pattern for new team members
- Review and adjust the organization as needed
