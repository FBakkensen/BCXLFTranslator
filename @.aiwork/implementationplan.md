# Implementation Plan: In-Place File Translation for BCXLFTranslator

This plan outlines the steps needed to implement in-place file translation for BCXLFTranslator, allowing the tool to accept a single file parameter that serves as both input and output.

## Tasks

1. [ ] **Modify the translate_xliff function to support in-place translation**
   - Prompt: "Modify the translate_xliff function in src/bcxlftranslator/main.py to support in-place file translation by creating a temporary file for output and replacing the original file only after successful translation."
   - Verification: The function should create a temporary file, write the translated content to it, and then replace the original file only if translation is successful. If any errors occur, the original file should remain intact.

2. [ ] **Update the command-line interface to support single-file mode**
   - Prompt: "Update the command-line interface in src/bcxlftranslator/main.py to support both the existing two-file mode and a new single-file mode where only an input file is provided."
   - Verification: Running the tool with a single file parameter should perform in-place translation, while running with two file parameters should maintain the existing behavior of writing to a separate output file.

3. [ ] **Add error handling for in-place translation**
   - Prompt: "Enhance error handling in the translate_xliff function to ensure the original file remains intact if any errors occur during in-place translation."
   - Verification: If an error occurs during translation, the original file should not be modified, and an appropriate error message should be displayed.

4. [ ] **Create unit tests for in-place translation**
   - Prompt: "Create unit tests in tests/test_inplace_translation.py to verify that in-place translation works correctly, including error handling and file preservation."
   - Verification: All tests should pass, confirming that in-place translation works as expected, preserves the original file on errors, and correctly replaces the file on success.

5. [ ] **Update documentation to reflect the new in-place translation feature**
   - Prompt: "Update the README.md file to document the new in-place translation feature, including examples of how to use it."
   - Verification: The README should clearly explain both the two-file mode and the new single-file mode, with examples of how to use each.

6. [ ] **Implement temporary file cleanup**
   - Prompt: "Ensure that temporary files created during in-place translation are properly cleaned up, even if errors occur."
   - Verification: No temporary files should be left behind after translation, regardless of whether it succeeds or fails.

7. [ ] **Add integration tests for in-place translation**
   - Prompt: "Add integration tests to verify that in-place translation works correctly with real XLIFF files from the examples directory."
   - Verification: The integration tests should confirm that in-place translation preserves the exact header and footer from the input file while correctly translating the content.

8. [ ] **Update help text and usage examples**
   - Prompt: "Update the help text and usage examples in the command-line interface to include information about in-place translation."
   - Verification: The help text should clearly explain how to use both the two-file mode and the new single-file mode.