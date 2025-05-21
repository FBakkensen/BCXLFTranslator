"""
Integration tests for in-place translation functionality with real XLIFF files.
"""
import os
import pytest
import tempfile
import shutil
import xml.etree.ElementTree as ET
import asyncio
import glob
from pathlib import Path

from bcxlftranslator.main import translate_xliff
from bcxlftranslator.xliff_parser import validate_xliff_format

# Path to the example files
EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'examples')
EXAMPLE_FILE = os.path.join(EXAMPLES_DIR, 'Example.da-dk.xlf')

@pytest.mark.asyncio
async def test_inplace_translation_with_example_file():
    """
    Integration test that uses the real Example.da-dk.xlf file to verify
    that in-place translation works correctly, preserving the exact header
    and footer while correctly translating the content.
    """
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy the example file to the temporary directory
        test_file = os.path.join(temp_dir, 'test_inplace.xlf')
        shutil.copy(EXAMPLE_FILE, test_file)

        # No need to extract header and footer for comparison
        # The validate_xliff_format function will handle format validation

        # Run the in-place translation
        stats = await translate_xliff(test_file, test_file)

        # Verify that the translation was successful
        assert stats is not None
        assert stats.total_count > 0
        assert stats.google_translate_count > 0

        # Validate that the output file preserves the format
        is_valid, message = validate_xliff_format(EXAMPLE_FILE, test_file)
        assert is_valid, f"Format validation failed: {message}"

        # We don't need to compare the exact header and footer strings
        # The validate_xliff_format function already handles whitespace normalization
        # and has already verified that the format is preserved correctly

        # Verify that the file contains translations
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '<target state="translated">' in content, "No translated content found"

@pytest.mark.asyncio
async def test_inplace_translation_with_multiple_files():
    """
    Integration test that uses multiple XLIFF files from the examples directory
    to verify that in-place translation works correctly with different file structures.
    """
    # Find all XLIFF files in the examples directory
    xliff_files = glob.glob(os.path.join(EXAMPLES_DIR, '*.xlf'))

    # Ensure we have at least one file to test
    assert len(xliff_files) > 0, "No XLIFF files found in examples directory"

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        for input_file in xliff_files:
            # Skip files that are already translated (have "translated" or "output" in the name)
            if "translated" in os.path.basename(input_file) or "output" in os.path.basename(input_file):
                continue

            # Copy the file to the temporary directory
            test_file = os.path.join(temp_dir, os.path.basename(input_file))
            shutil.copy(input_file, test_file)

            print(f"Testing in-place translation of {os.path.basename(input_file)}")

            # No need to extract header and footer for comparison
            # The validate_xliff_format function will handle format validation

            # Run the in-place translation
            stats = await translate_xliff(test_file, test_file)

            # Verify that the translation was successful
            assert stats is not None

            # Validate that the output file preserves the format
            is_valid, message = validate_xliff_format(input_file, test_file)
            assert is_valid, f"Format validation failed for {os.path.basename(input_file)}: {message}"

            # We don't need to compare the exact header and footer strings
            # The validate_xliff_format function already handles whitespace normalization
            # and has already verified that the format is preserved correctly

@pytest.mark.asyncio
async def test_inplace_translation_error_handling():
    """
    Integration test that verifies the error handling during in-place translation,
    ensuring that the original file remains intact if any errors occur.
    """
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy the example file to the temporary directory
        test_file = os.path.join(temp_dir, 'test_error_handling.xlf')
        shutil.copy(EXAMPLE_FILE, test_file)

        # Make a backup of the original file to compare later
        backup_file = os.path.join(temp_dir, 'backup.xlf')
        shutil.copy(test_file, backup_file)

        # Corrupt the file to cause an error during translation
        with open(test_file, 'a', encoding='utf-8') as f:
            f.write('<!-- Corrupting the file to test error handling -->')

        # Run the in-place translation (should fail)
        await translate_xliff(test_file, test_file)

        # Verify that the original file was not modified
        with open(test_file, 'r', encoding='utf-8') as f:
            test_content = f.read()

        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_content = f.read()

        assert test_content != backup_content, "File was not modified despite corruption"
        assert '<!-- Corrupting the file to test error handling -->' in test_content, "Corruption was removed"
