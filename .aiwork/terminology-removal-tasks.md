# Terminology Removal Tasks

This document outlines the step-by-step process for completely removing terminology functionality from the BCXLFTranslator codebase. Each task is designed to be atomic and self-contained, with clear verification criteria.

## Test Modifications

### Task 1: Update test_config.py to Remove Terminology Tests

- **Status**: [x]
- **Description**: Modify `tests/test_config.py` to remove or update tests that specifically check for terminology functionality. This includes tests for CLI arguments, config file loading, environment variables, and validation related to terminology.
- **Prompt**: "Update the test_config.py file to remove all terminology-related tests. Either remove the tests completely or modify them to test only the translation functionality that remains in the codebase."
- **Verification**:
  - The file no longer contains assertions checking for terminology-related configuration options
  - Running `python -m pytest tests/test_config.py -v` passes all tests

### Task 2: Update test_cli.py to Remove Terminology Expectations

- **Status**: [x]
- **Description**: Modify `tests/test_cli.py` to remove expectations for terminology-related options in the CLI help text and argument handling.
- **Prompt**: "Update the test_cli.py file to remove any expectations for terminology-related options in the CLI help text and argument handling. Make sure the tests only check for translation-related functionality."
- **Verification**:
  - The file no longer contains assertions checking for terminology-related CLI options
  - Running `python -m pytest tests/test_cli.py -v` passes all tests

### Task 3: Check and Update Any Other Test Files for Terminology References

- **Status**: [ ]
- **Description**: Search through all other test files for any references to terminology functionality and update them accordingly.
- **Prompt**: "Search through all test files (except test_config.py and test_cli.py which we've already handled) for any references to terminology functionality. Update or remove these tests as needed to focus only on translation functionality."
- **Verification**:
  - No test files contain assertions or expectations related to terminology functionality
  - Running `python -m pytest` passes all tests

## Implementation Changes

### Task 4: Clean Up config.py

- **Status**: [ ]
- **Description**: Remove all terminology-related code from `src/bcxlftranslator/config.py`, including command-line arguments, environment variable handling, and configuration validation.
- **Prompt**: "Clean up the config.py file to remove all terminology-related code. This includes removing command-line arguments, environment variable handling, and configuration validation related to terminology. Keep only the translation-related functionality."
- **Verification**:
  - The file no longer contains any terminology-related code
  - Running `python -m pytest tests/test_config.py -v` still passes all tests

### Task 5: Clean Up main.py

- **Status**: [ ]
- **Description**: Remove any terminology-related code from `src/bcxlftranslator/main.py`, including imports, functions, and CLI argument handling.
- **Prompt**: "Clean up the main.py file to remove any terminology-related code. This includes imports, functions, and CLI argument handling related to terminology. Keep only the translation-related functionality."
- **Verification**:
  - The file no longer contains any terminology-related code
  - Running `python -m pytest tests/test_cli.py -v` still passes all tests

### Task 6: Search for and Remove Terminology References in Other Files

- **Status**: [ ]
- **Description**: Search through all other Python files in the src directory for any references to terminology functionality and remove them.
- **Prompt**: "Search through all Python files in the src directory (except config.py and main.py which we've already handled) for any references to terminology functionality. Remove these references while maintaining the integrity of the translation functionality."
- **Verification**:
  - No Python files in the src directory contain terminology-related code
  - Running `python -m pytest` passes all tests

## Documentation Updates

### Task 7: Update README.md

- **Status**: [ ]
- **Description**: Update the project's README.md file to remove any references to terminology functionality and clarify that the project now focuses solely on translation.
- **Prompt**: "Update the README.md file to remove any references to terminology functionality. Make it clear that the project now focuses solely on translation using Google Translate. Update any examples, usage instructions, or feature lists accordingly."
- **Verification**:
  - README.md no longer mentions terminology functionality
  - README.md accurately describes the current functionality of the project

### Task 8: Update Other Documentation Files

- **Status**: [ ]
- **Description**: Search for and update any other documentation files in the project to remove terminology references.
- **Prompt**: "Search for and update any documentation files in the project (besides README.md) to remove terminology references. This includes any .md files, docstrings, or comments in the code."
- **Verification**:
  - No documentation files contain references to terminology functionality
  - All documentation accurately reflects the current functionality

## Final Verification

### Task 9: Run All Tests and Fix Any Remaining Issues

- **Status**: [ ]
- **Description**: Run the full test suite to ensure all tests pass after the terminology functionality has been removed.
- **Prompt**: "Run the full test suite to verify that all tests pass after removing the terminology functionality. If any tests fail, identify and fix the issues while maintaining the focus on translation-only functionality."
- **Verification**:
  - Running `python -m pytest -v` passes all tests
  - No terminology-related code remains in the codebase

### Task 10: Version Bump for Breaking Change

- **Status**: [ ]
- **Description**: Update the version number in the project metadata to reflect the breaking change of removing terminology functionality.
- **Prompt**: "Update the version number in the project metadata (setup.py or similar) to reflect the breaking change of removing terminology functionality. This should be a major version bump according to semantic versioning."
- **Verification**:
  - Version number has been incremented appropriately in all relevant files
  - Any version references in documentation are consistent

## Additional Tasks

### Task 11: Create Migration Guide for Users

- **Status**: [ ]
- **Description**: Create a migration guide for users who were using the terminology functionality to help them transition to the new version.
- **Prompt**: "Create a migration guide document that explains the removal of terminology functionality and provides guidance for users who were using this feature. Include alternative approaches they might consider and explain the rationale for the change."
- **Verification**:
  - A clear migration guide exists in the project documentation
  - The guide provides helpful information for users affected by the change

### Task 12: Clean Up Unused Dependencies

- **Status**: [ ]
- **Description**: Remove any dependencies that were only needed for the terminology functionality.
- **Prompt**: "Review the project dependencies in requirements.txt and setup.py to identify and remove any that were only needed for the terminology functionality. Update the dependency list to include only what's needed for the translation functionality."
- **Verification**:
  - requirements.txt and setup.py only include necessary dependencies
  - The project still builds and runs correctly with the updated dependencies

### Task 13: Final Code Review and Cleanup

- **Status**: [ ]
- **Description**: Perform a final review of the codebase to ensure it's clean, well-organized, and focused solely on translation functionality.
- **Prompt**: "Perform a final review of the codebase to ensure it's clean, well-organized, and focused solely on translation functionality. Look for any remaining terminology references, unused code, or opportunities for simplification now that the terminology functionality has been removed."
- **Verification**:
  - Code is clean and well-organized
  - No unused code or terminology references remain
  - Project structure makes sense for the focused functionality