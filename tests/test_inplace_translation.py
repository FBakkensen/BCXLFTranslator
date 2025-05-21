"""
Tests for in-place translation functionality.
"""
import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, Mock
import xml.etree.ElementTree as ET
import asyncio

# Import the function to test
from bcxlftranslator.main import translate_xliff

# Sample XLIFF content for testing
SAMPLE_XLIFF = """<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="urn:oasis:names:tc:xliff:document:1.2 xliff-core-1.2-transitional.xsd">
  <file datatype="xml" source-language="en-US" target-language="da-dk" original="Test File">
    <body>
      <group id="body">
        <trans-unit id="test1" size-unit="char" translate="yes" xml:space="preserve">
          <source>Hello World</source>
          <target state="needs-translation"/>
          <note from="Developer" annotates="general" priority="2"/>
        </trans-unit>
        <trans-unit id="test2" size-unit="char" translate="yes" xml:space="preserve">
          <source>Test Translation</source>
          <target state="needs-translation"/>
          <note from="Developer" annotates="general" priority="2"/>
        </trans-unit>
      </group>
    </body>
  </file>
</xliff>"""

@pytest.mark.asyncio
async def test_inplace_translation():
    """
    Test that in-place translation works correctly by creating a temporary file,
    translating it in-place, and verifying the result.
    """
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_file = os.path.join(temp_dir, 'test_inplace.xlf')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(SAMPLE_XLIFF)

        # Mock the translation function to return a consistent result
        with patch('bcxlftranslator.main.translate_with_retry') as mock_translate:
            mock_translate.return_value = Mock(text="Hej Verden")

            # Run in-place translation (input_file == output_file)
            stats = await translate_xliff(test_file, test_file)

            # Verify that the translation was successful
            assert stats is not None
            assert stats.total_count > 0

            # Verify that the file was modified
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Hej Verden" in content
                assert "<target state=\"translated\">Hej Verden</target>" in content

            # For in-place translation, we can't use validate_xliff_format with the same file
            # as both input and output, so we'll check the content directly
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check that the file contains the expected elements
                assert '<?xml version="1.0" encoding="UTF-8"?>' in content
                assert '<xliff version="1.2"' in content
                assert 'source-language="en-US"' in content
                assert 'target-language="da-dk"' in content
                assert '<target state="translated">Hej Verden</target>' in content

@pytest.mark.asyncio
async def test_inplace_translation_error_handling():
    """
    Test that in-place translation properly handles errors and preserves the original file.
    """
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_file = os.path.join(temp_dir, 'test_inplace_error.xlf')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(SAMPLE_XLIFF)

        # Make a backup of the original file to compare later
        backup_file = os.path.join(temp_dir, 'backup.xlf')
        shutil.copy(test_file, backup_file)

        # Mock the translation function to raise an exception
        with patch('bcxlftranslator.main.translate_with_retry') as mock_translate:
            mock_translate.side_effect = Exception("Simulated translation error")

            # Run in-place translation (input_file == output_file)
            stats = await translate_xliff(test_file, test_file)

            # Verify that the original file was not modified
            with open(test_file, 'r', encoding='utf-8') as f:
                test_content = f.read()

            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_content = f.read()

            assert test_content == backup_content, "Original file was modified despite error"

@pytest.mark.asyncio
async def test_inplace_translation_preserves_header_footer():
    """
    Test that in-place translation preserves the exact header and footer from the input file.
    """
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_file = os.path.join(temp_dir, 'test_inplace_header_footer.xlf')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(SAMPLE_XLIFF)

        # Make a backup of the original file to compare later
        backup_file = os.path.join(temp_dir, 'backup.xlf')
        shutil.copy(test_file, backup_file)

        # Mock the translation function to return a consistent result
        with patch('bcxlftranslator.main.translate_with_retry') as mock_translate:
            mock_translate.return_value = Mock(text="Hej Verden")

            # Run in-place translation (input_file == output_file)
            await translate_xliff(test_file, test_file)

            # Verify that the file was modified (contains translations)
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "<target state=\"translated\">Hej Verden</target>" in content

            # Verify that the XML structure is preserved
            with open(test_file, 'r', encoding='utf-8') as f:
                translated_content = f.read()

            with open(backup_file, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Check that the XML declaration and root element are preserved
            assert original_content.split('<trans-unit')[0] in translated_content
            # Check that the closing tags are preserved (allowing for different whitespace)
            assert '</body>' in translated_content
            assert '</file>' in translated_content
            assert '</xliff>' in translated_content
