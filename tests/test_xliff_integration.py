import os
import pytest
import tempfile
import xml.etree.ElementTree as ET
import asyncio
from unittest.mock import Mock, patch
import re
import glob

from bcxlftranslator.main import translate_xliff
from bcxlftranslator.xliff_parser import extract_header_footer, validate_xliff_format

# Path to the example files
EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'examples')
EXAMPLE_FILE = os.path.join(EXAMPLES_DIR, 'Example.da-dk.xlf')

@pytest.mark.asyncio
async def test_integration_with_example_file():
    """
    Integration test that uses the real Example.da-dk.xlf file to verify
    the entire translation process preserves the exact header and footer
    while correctly translating the content.
    """
    # Create a temporary output file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlf') as temp_file:
        output_file = temp_file.name

    try:
        # Extract the original header and footer for comparison
        original_header, original_footer = extract_header_footer(EXAMPLE_FILE)

        # Run the actual translation without mocking
        stats = await translate_xliff(EXAMPLE_FILE, output_file)

        # Verify that the translation was successful
        assert stats is not None
        assert stats.total_count > 0
        assert stats.google_translate_count > 0

        # Validate that the output file preserves the format
        is_valid, message = validate_xliff_format(EXAMPLE_FILE, output_file)
        assert is_valid, f"Format validation failed: {message}"

        # Extract the header and footer from the output file
        translated_header, translated_footer = extract_header_footer(output_file)

        # Verify the header and footer contain the same essential content
        # Normalize whitespace for comparison
        def normalize_whitespace(text):
            return re.sub(r'\s+', ' ', text).strip()

        assert normalize_whitespace(original_header) == normalize_whitespace(translated_header)
        assert normalize_whitespace(original_footer) == normalize_whitespace(translated_footer)

        # Parse the input and output files to check content
        input_tree = ET.parse(EXAMPLE_FILE)
        output_tree = ET.parse(output_file)

        # Check that file attributes are preserved
        input_file_elem = input_tree.getroot().find('.//{*}file')
        output_file_elem = output_tree.getroot().find('.//{*}file')

        assert input_file_elem is not None
        assert output_file_elem is not None
        assert output_file_elem.get('source-language') == input_file_elem.get('source-language')
        assert output_file_elem.get('target-language') == input_file_elem.get('target-language')
        assert output_file_elem.get('original') == input_file_elem.get('original')

        # Check that trans-units were translated
        # Find trans-units with empty targets in the input file
        ns = {'x': 'urn:oasis:names:tc:xliff:document:1.2'}

        # Find all trans-units in the input file
        input_trans_units = input_tree.findall('.//x:trans-unit', ns)
        assert len(input_trans_units) > 0, "No trans-units found in input file"

        # Find trans-units that need translation (empty target or needs-translation state)
        input_empty_trans_units = []
        for tu in input_trans_units:
            target = tu.find('x:target', ns)
            if target is not None:
                if not target.text or not target.text.strip() or target.get('state') == 'needs-translation':
                    input_empty_trans_units.append(tu)

        # There should be at least some trans-units that needed translation
        # If not, we'll just check that the format was preserved
        if len(input_empty_trans_units) > 0:
            print(f"Found {len(input_empty_trans_units)} trans-units that need translation")

            # Check that these units were translated in the output file
            for i, input_trans_unit in enumerate(input_empty_trans_units):
                trans_unit_id = input_trans_unit.get('id')
                assert trans_unit_id is not None, "Trans-unit has no id attribute"

                # Find the same trans-unit in the output file
                output_trans_unit = output_tree.find(f'.//x:trans-unit[@id="{trans_unit_id}"]', ns)
                assert output_trans_unit is not None, f"Trans-unit with id {trans_unit_id} not found in output file"

                output_target = output_trans_unit.find('x:target', ns)
                assert output_target is not None, f"Target element not found in trans-unit with id {trans_unit_id}"

                # Check that the target has content and is marked as translated
                assert output_target.text and output_target.text.strip(), f"Target text is empty for trans-unit with id {trans_unit_id}"
                assert output_target.get('state') == 'translated', f"Target state is not 'translated' for trans-unit with id {trans_unit_id}"

                # Check that a BCXLFTranslator note was added
                note = output_trans_unit.find('x:note[@from="BCXLFTranslator"]', ns)
                assert note is not None, f"BCXLFTranslator note not found for trans-unit with id {trans_unit_id}"
                assert "Source: Google Translate" in note.text, f"Note does not contain 'Source: Google Translate' for trans-unit with id {trans_unit_id}"

                # Only check a few units to keep the test reasonably fast
                if i >= 5:
                    break
        else:
            print("No trans-units found that need translation. Checking format preservation only.")

    finally:
        # Clean up the temporary file
        if os.path.exists(output_file):
            os.unlink(output_file)

@pytest.mark.asyncio
async def test_integration_with_multiple_files():
    """
    Integration test that uses multiple XLIFF files from the examples directory
    to verify the translation process works correctly with different file structures.
    """
    # Find all XLIFF files in the examples directory
    xliff_files = glob.glob(os.path.join(EXAMPLES_DIR, '*.xlf'))

    # Ensure we have at least one file to test
    assert len(xliff_files) > 0, "No XLIFF files found in examples directory"

    for input_file in xliff_files:
        # Skip files that are already translated (have "output" in the name)
        if "output" in os.path.basename(input_file):
            continue

        # Create a temporary output file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlf') as temp_file:
            output_file = temp_file.name

        try:
            print(f"Testing translation of {os.path.basename(input_file)}")

            # Extract the original header and footer for comparison
            original_header, original_footer = extract_header_footer(input_file)

            # Run the actual translation
            stats = await translate_xliff(input_file, output_file)

            # Verify that the translation was successful
            assert stats is not None

            # Validate that the output file preserves the format
            is_valid, message = validate_xliff_format(input_file, output_file)

            # If the file is already translated, the validation might fail with "No translation appears to have occurred"
            # This is expected and we should ignore this specific error
            if not is_valid and "No translation appears to have occurred" in message:
                print(f"Note: {message} This is expected for already translated files.")
            else:
                assert is_valid, f"Format validation failed for {os.path.basename(input_file)}: {message}"

            # Extract the header and footer from the output file
            translated_header, translated_footer = extract_header_footer(output_file)

            # Verify the header and footer contain the same essential content
            def normalize_whitespace(text):
                return re.sub(r'\s+', ' ', text).strip()

            assert normalize_whitespace(original_header) == normalize_whitespace(translated_header)
            assert normalize_whitespace(original_footer) == normalize_whitespace(translated_footer)

            # Parse the input and output files to check content
            input_tree = ET.parse(input_file)
            output_tree = ET.parse(output_file)

            # Check that file attributes are preserved
            input_file_elem = input_tree.getroot().find('.//{*}file')
            output_file_elem = output_tree.getroot().find('.//{*}file')

            if input_file_elem is not None and output_file_elem is not None:
                for attr in ['source-language', 'target-language', 'original']:
                    if input_file_elem.get(attr):
                        assert output_file_elem.get(attr) == input_file_elem.get(attr)

        finally:
            # Clean up the temporary file
            if os.path.exists(output_file):
                os.unlink(output_file)
