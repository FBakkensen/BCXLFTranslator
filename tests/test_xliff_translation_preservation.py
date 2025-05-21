import os
import pytest
import tempfile
import xml.etree.ElementTree as ET
import asyncio
from unittest.mock import Mock, patch
import re

from bcxlftranslator.main import translate_xliff
from bcxlftranslator.xliff_parser import extract_header_footer

# Path to the example file
EXAMPLE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'examples', 'Example.da-dk.xlf')

@pytest.mark.asyncio
async def test_translate_xliff_preserves_header_footer():
    """
    Test that the translate_xliff function preserves the exact header and footer
    from the input file while only updating the trans-units.
    """
    # Create a temporary output file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlf') as temp_file:
        output_file = temp_file.name

    try:
        # Extract the original header and footer for comparison
        original_header, original_footer = extract_header_footer(EXAMPLE_FILE)

        # Mock the translation function to return a consistent result
        with patch('bcxlftranslator.main.translate_with_retry') as mock_translate:
            mock_translate.return_value = Mock(text="Translated Text")

            # Run the translation
            await translate_xliff(EXAMPLE_FILE, output_file)

            # Extract the header and footer from the output file
            translated_header, translated_footer = extract_header_footer(output_file)

            # Verify the header and footer contain the same essential content
            # Normalize whitespace for comparison
            def normalize_whitespace(text):
                return re.sub(r'\s+', ' ', text).strip()

            assert normalize_whitespace(original_header) == normalize_whitespace(translated_header)
            assert normalize_whitespace(original_footer) == normalize_whitespace(translated_footer)

            # Verify that the trans-units were processed
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check that some translations were applied (target elements have content)
            assert 'state="translated"' in content
            assert '<target state="translated">' in content

            # Check that the BCXLFTranslator note was added
            assert '<note from="BCXLFTranslator">Source: Google Translate' in content
    finally:
        # Clean up the temporary file
        if os.path.exists(output_file):
            os.unlink(output_file)

@pytest.mark.asyncio
async def test_translate_xliff_preserves_attributes():
    """
    Test that the translate_xliff function preserves all attributes
    in the XLIFF file, including source-language, target-language, and original.
    """
    # Create a temporary output file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlf') as temp_file:
        output_file = temp_file.name

    try:
        # Mock the translation function to return a consistent result
        with patch('bcxlftranslator.main.translate_with_retry') as mock_translate:
            mock_translate.return_value = Mock(text="Translated Text")

            # Run the translation
            await translate_xliff(EXAMPLE_FILE, output_file)

            # Parse the input and output files
            input_tree = ET.parse(EXAMPLE_FILE)
            output_tree = ET.parse(output_file)

            input_root = input_tree.getroot()
            output_root = output_tree.getroot()

            # Check that the root attributes are preserved
            for attr, value in input_root.attrib.items():
                assert attr in output_root.attrib
                assert output_root.attrib[attr] == value

            # Check that the file element attributes are preserved
            input_file = input_root.find('.//{*}file')
            output_file_elem = output_root.find('.//{*}file')

            assert input_file is not None
            assert output_file_elem is not None

            for attr, value in input_file.attrib.items():
                assert attr in output_file_elem.attrib
                assert output_file_elem.attrib[attr] == value

            # Specifically check important attributes
            assert output_file_elem.get('source-language') == input_file.get('source-language')
            assert output_file_elem.get('target-language') == input_file.get('target-language')
            assert output_file_elem.get('original') == input_file.get('original')
    finally:
        # Clean up the temporary file
        if os.path.exists(output_file):
            os.unlink(output_file)

@pytest.mark.asyncio
async def test_translate_xliff_with_special_characters():
    """
    Test that the translate_xliff function correctly handles special characters
    in the XLIFF content.
    """
    # Create a temporary input file with special characters in content
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.xlf') as temp_input:
        temp_input.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="da-dk" original="Test &amp; Demo">
    <body>
      <group id="body">
        <trans-unit id="1">
          <source>Test with special chars: &amp; &lt; &gt; &quot; &apos;</source>
          <target state="needs-translation"></target>
        </trans-unit>
      </group>
    </body>
  </file>
</xliff>''')
        input_file = temp_input.name

    # Create a temporary output file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlf') as temp_output:
        output_file = temp_output.name

    try:
        # Extract the original header and footer for comparison
        original_header, original_footer = extract_header_footer(input_file)

        # Mock the translation function to return a consistent result
        with patch('bcxlftranslator.main.translate_with_retry') as mock_translate:
            mock_translate.return_value = Mock(text="Translated Text with special chars: & < > \" '")

            # Run the translation
            await translate_xliff(input_file, output_file)

            # Extract the header and footer from the output file
            translated_header, translated_footer = extract_header_footer(output_file)

            # Verify the header and footer contain the same essential content
            # Normalize whitespace for comparison
            def normalize_whitespace(text):
                return re.sub(r'\s+', ' ', text).strip()

            assert normalize_whitespace(original_header) == normalize_whitespace(translated_header)
            assert normalize_whitespace(original_footer) == normalize_whitespace(translated_footer)

            # Verify that special characters were properly escaped in the output
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check that the original attribute was preserved with escaped ampersand
            assert 'original="Test &amp; Demo"' in content

            # Check that special characters in the translated text were properly escaped
            assert '&amp;' in content  # Escaped ampersand
            assert '&lt;' in content   # Escaped less than
            assert '&gt;' in content   # Escaped greater than
            assert '&quot;' in content # Escaped quote
            assert '&apos;' in content # Escaped apostrophe
    finally:
        # Clean up the temporary files
        if os.path.exists(input_file):
            os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)
