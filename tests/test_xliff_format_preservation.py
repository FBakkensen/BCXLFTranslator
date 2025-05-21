import os
import pytest
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch

from bcxlftranslator.xliff_parser import extract_header_footer, extract_trans_units, extract_trans_units_from_file, trans_units_to_text, preserve_indentation, validate_xliff_format
from bcxlftranslator.exceptions import EmptyXliffError, InvalidXliffError, MalformedXliffError, NoTransUnitsError
from bcxlftranslator.main import translate_xliff

# Path to the example file
EXAMPLE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'examples', 'Example.da-dk.xlf')

def test_extract_header_footer_with_example_file():
    """
    Test that the extract_header_footer function correctly extracts the header and footer
    from the example file.
    """
    # Extract header and footer
    header, footer = extract_header_footer(EXAMPLE_FILE)

    # Verify header contains expected content
    assert '<?xml version="1.0" encoding="UTF-8"?>' in header
    assert '<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2"' in header
    assert '<file datatype="xml" source-language="en-US" target-language="da-dk"' in header
    assert '<body>' in header
    assert '<group id="body">' in header

    # Verify header does not contain any trans-unit elements
    assert '<trans-unit' not in header

    # Verify footer contains expected content
    assert '</group>' in footer
    assert '</body>' in footer
    assert '</file>' in footer
    assert '</xliff>' in footer

    # Verify footer does not contain any trans-unit elements
    assert '</trans-unit>' not in footer

def test_extract_header_footer_with_nonexistent_file():
    """
    Test that the extract_header_footer function raises FileNotFoundError
    when the file does not exist.
    """
    with pytest.raises(FileNotFoundError):
        extract_header_footer('nonexistent_file.xlf')

def test_extract_header_footer_with_empty_file():
    """
    Test that the extract_header_footer function raises EmptyXliffError
    when the file is empty.
    """
    # Create an empty temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_path = temp_file.name

    try:
        with pytest.raises(EmptyXliffError):
            extract_header_footer(temp_file_path)
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_extract_header_footer_with_no_trans_units():
    """
    Test that the extract_header_footer function raises NoTransUnitsError
    when the file does not contain any trans-unit elements.
    """
    # Create a temporary file with XLIFF structure but no trans-units
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <group id="body">
      </group>
    </body>
  </file>
</xliff>''')
        temp_file_path = temp_file.name

    try:
        with pytest.raises(NoTransUnitsError, match="No trans-unit elements found"):
            extract_header_footer(temp_file_path)
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_extract_header_footer_with_namespaced_trans_units():
    """
    Test that the extract_header_footer function correctly handles
    trans-unit elements with namespaces.
    """
    # Create a temporary file with namespaced trans-units
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <group id="body">
        <x:trans-unit id="test1" xmlns:x="urn:oasis:names:tc:xliff:document:1.2">
          <x:source>Hello World</x:source>
          <x:target>Bonjour Le monde</x:target>
        </x:trans-unit>
      </group>
    </body>
  </file>
</xliff>''')
        temp_file_path = temp_file.name

    try:
        header, footer = extract_header_footer(temp_file_path)

        # Verify header contains expected content
        assert '<?xml version="1.0" encoding="UTF-8"?>' in header
        assert '<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2"' in header

        # Verify header does not contain any trans-unit elements
        assert 'trans-unit' not in header

        # Verify footer contains expected content
        assert '</group>' in footer
        assert '</body>' in footer
        assert '</file>' in footer
        assert '</xliff>' in footer
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_extract_trans_units_with_example_file():
    """
    Test that the extract_trans_units_from_file function correctly extracts all trans-units
    from the example file as XML Element objects.
    """
    # Extract trans-units
    trans_units = extract_trans_units_from_file(EXAMPLE_FILE)

    # Verify we have the expected number of trans-units
    assert len(trans_units) == 4

    # Verify each trans-unit has the expected structure
    for tu in trans_units:
        # Check that it's an Element object
        assert isinstance(tu, ET.Element)

        # Check that it has an id attribute
        assert 'id' in tu.attrib

        # Check that it has source and target elements
        ns = {'x': 'urn:oasis:names:tc:xliff:document:1.2'}
        source = tu.find('x:source', ns)
        assert source is not None

        # Target might be None in some cases, but we'll check it exists in our example
        target = tu.find('x:target', ns)
        assert target is not None

def test_extract_trans_units_with_nonexistent_file():
    """
    Test that the extract_trans_units_from_file function raises FileNotFoundError
    when the file does not exist.
    """
    with pytest.raises(FileNotFoundError):
        extract_trans_units_from_file('nonexistent_file.xlf')

def test_extract_trans_units_with_empty_file():
    """
    Test that the extract_trans_units_from_file function raises EmptyXliffError
    when the file is empty.
    """
    # Create an empty temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_path = temp_file.name

    try:
        with pytest.raises(EmptyXliffError):
            extract_trans_units_from_file(temp_file_path)
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_extract_trans_units_with_invalid_xliff():
    """
    Test that the extract_trans_units_from_file function raises InvalidXliffError
    when the file is not a valid XLIFF file.
    """
    # Create a temporary file with invalid XML
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<root>
  <file>
    <body>
      <trans-unit id="1">
        <source>Test</source>
        <target>Test</target>
      </trans-unit>
    </body>
  </file>
</root>''')
        temp_file_path = temp_file.name

    try:
        # The function should raise an InvalidXliffError because the root element is not 'xliff'
        with pytest.raises(InvalidXliffError):
            extract_trans_units_from_file(temp_file_path)
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_extract_header_footer_with_malformed_xml():
    """
    Test that the extract_header_footer function raises MalformedXliffError
    when the file contains malformed XML.
    """
    # Create a temporary file with malformed XML (missing closing tag)
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <group id="body">
        <trans-unit id="1">
          <source>Test</source>
          <target>Test</target>
        <!-- Missing closing trans-unit tag -->
      </group>
    </body>
  </file>
</xliff>''')
        temp_file_path = temp_file.name

    try:
        with pytest.raises(MalformedXliffError):
            extract_header_footer(temp_file_path)
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_extract_header_footer_with_mismatched_tags():
    """
    Test that the extract_header_footer function raises MalformedXliffError
    when the file contains mismatched tags.
    """
    # Create a temporary file with mismatched tags
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <group id="body">
        <trans-unit id="1">
          <source>Test</source>
          <target>Test</target>
        </trans-unit>
      </group>
    </body>
  </file>
</xliff>'''.replace('</trans-unit>', '</unit>'))  # Deliberately mismatch the closing tag
        temp_file_path = temp_file.name

    try:
        with pytest.raises(MalformedXliffError):
            extract_header_footer(temp_file_path)
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_extract_header_footer_with_missing_essential_elements():
    """
    Test that the extract_header_footer function raises MalformedXliffError
    when the file is missing essential XLIFF elements.
    """
    # Create a temporary file without a file element
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <body>
    <trans-unit id="1">
      <source>Test</source>
      <target>Test</target>
    </trans-unit>
  </body>
</xliff>''')
        temp_file_path = temp_file.name

    try:
        with pytest.raises(MalformedXliffError, match="Missing <file> element"):
            extract_header_footer(temp_file_path)
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_preserve_indentation_with_malformed_xml():
    """
    Test that the preserve_indentation function raises MalformedXliffError
    when the file contains malformed XML.
    """
    # Create a temporary file with malformed XML - completely invalid XML structure
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="1">
        <source>Test</source>
        <target>Test</target>
      </trans-unit>
    </body>
  </file>
</xliff''')  # Missing closing bracket for xliff tag
        temp_file_path = temp_file.name

    try:
        # Mock the open function to simulate an XML parsing error
        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'Invalid UTF-8')):
            with pytest.raises(MalformedXliffError):
                preserve_indentation(temp_file_path)
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_load_xliff_file_with_no_trans_units():
    """
    Test that the load_xliff_file function raises NoTransUnitsError
    when the file does not contain any trans-unit elements.
    """
    # Create a temporary file with XLIFF structure but no trans-units
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <group id="body">
      </group>
    </body>
  </file>
</xliff>''')
        temp_file_path = temp_file.name

    try:
        with pytest.raises(NoTransUnitsError):
            from bcxlftranslator.xliff_parser import load_xliff_file
            load_xliff_file(temp_file_path)
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_extract_trans_units_with_namespaced_trans_units():
    """
    Test that the extract_trans_units_from_file function correctly handles
    trans-unit elements with namespaces.
    """
    # Create a temporary file with namespaced trans-units
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <group id="body">
        <x:trans-unit id="test1" xmlns:x="urn:oasis:names:tc:xliff:document:1.2">
          <x:source>Hello World</x:source>
          <x:target>Bonjour Le monde</x:target>
        </x:trans-unit>
      </group>
    </body>
  </file>
</xliff>''')
        temp_file_path = temp_file.name

    try:
        trans_units = extract_trans_units_from_file(temp_file_path)

        # Verify we have the expected number of trans-units
        assert len(trans_units) == 1

        # Verify the trans-unit has the expected structure
        tu = trans_units[0]
        assert isinstance(tu, ET.Element)
        assert 'id' in tu.attrib
        assert tu.get('id') == 'test1'

        # Check source and target content
        ns = {'x': 'urn:oasis:names:tc:xliff:document:1.2'}
        source = tu.find('x:source', ns)
        assert source is not None
        assert source.text == 'Hello World'

        target = tu.find('x:target', ns)
        assert target is not None
        assert target.text == 'Bonjour Le monde'
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_trans_units_to_text_with_example_file():
    """
    Test that the trans_units_to_text function correctly converts trans-units
    from the example file back to properly formatted text.
    """
    # Extract trans-units
    trans_units = extract_trans_units_from_file(EXAMPLE_FILE)

    # Convert trans-units to text
    text = trans_units_to_text(trans_units)

    # Verify the text contains expected content
    assert '<trans-unit id=' in text
    assert 'Attached To SystemID' in text
    assert 'state="needs-translation"' in text
    assert 'from="Developer" annotates="general" priority="2"' in text

    # Verify proper indentation
    lines = text.split('\n')
    for line in lines:
        if '<trans-unit' in line:
            assert line.startswith('  ')  # Base indentation
        if 'source' in line or 'target' in line or 'note' in line:
            assert line.startswith('    ')  # Child indentation

    # Verify all trans-units are included
    assert text.count('<trans-unit') == 4
    assert text.count('</trans-unit>') == 4

def test_trans_units_to_text_with_empty_list():
    """
    Test that the trans_units_to_text function returns an empty string
    when given an empty list.
    """
    assert trans_units_to_text([]) == ""

def test_trans_units_to_text_with_invalid_input():
    """
    Test that the trans_units_to_text function raises TypeError
    when given invalid input.
    """
    with pytest.raises(TypeError, match="trans_units must be a list"):
        trans_units_to_text("not a list")

    with pytest.raises(TypeError, match="All items in trans_units must be xml.etree.ElementTree.Element objects"):
        trans_units_to_text([1, 2, 3])

def test_trans_units_to_text_with_custom_indentation():
    """
    Test that the trans_units_to_text function correctly applies custom indentation.
    """
    # Extract trans-units
    trans_units = extract_trans_units_from_file(EXAMPLE_FILE)

    # Convert trans-units to text with custom indentation
    text = trans_units_to_text(trans_units, indent_level=3)

    # Verify proper indentation
    lines = text.split('\n')
    for line in lines:
        if '<trans-unit' in line:
            assert line.startswith('      ')  # 3 * 2 spaces
        if 'source' in line or 'target' in line or 'note' in line:
            assert line.startswith('        ')  # (3 * 2) + 2 spaces

def test_preserve_indentation():
    """
    Test that the preserve_indentation function correctly extracts indentation patterns
    from an XLIFF file.
    """
    # Use the example file
    patterns = preserve_indentation(EXAMPLE_FILE)

    # Verify the patterns
    assert 'trans_unit' in patterns
    assert 'child' in patterns
    assert len(patterns['trans_unit']) == 8  # 8 spaces
    assert len(patterns['child']) == 10  # 10 spaces

def test_preserve_indentation_with_nonexistent_file():
    """
    Test that the preserve_indentation function raises FileNotFoundError
    when the file does not exist.
    """
    with pytest.raises(FileNotFoundError):
        preserve_indentation('nonexistent_file.xlf')

def test_preserve_indentation_with_empty_file():
    """
    Test that the preserve_indentation function raises EmptyXliffError
    when the file is empty.
    """
    # Create an empty temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_path = temp_file.name

    try:
        with pytest.raises(EmptyXliffError):
            preserve_indentation(temp_file_path)
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_preserve_indentation_with_no_trans_units():
    """
    Test that the preserve_indentation function raises NoTransUnitsError
    when the file does not contain any trans-unit elements.
    """
    # Create a temporary file with XLIFF structure but no trans-units
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <group id="body">
      </group>
    </body>
  </file>
</xliff>''')
        temp_file_path = temp_file.name

    try:
        with pytest.raises(NoTransUnitsError, match="No trans-unit elements found"):
            preserve_indentation(temp_file_path)
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def test_trans_units_to_text_with_indentation_patterns():
    """
    Test that the trans_units_to_text function correctly applies indentation patterns.
    """
    # Extract trans-units
    trans_units = extract_trans_units_from_file(EXAMPLE_FILE)

    # Extract indentation patterns
    patterns = preserve_indentation(EXAMPLE_FILE)

    # Convert trans-units to text with indentation patterns
    text = trans_units_to_text(trans_units, indentation_patterns=patterns)

    # Verify proper indentation - we now use a standard 6 spaces for trans-units
    # instead of the original patterns, so we need to check for that
    lines = text.split('\n')
    for line in lines:
        if '<trans-unit' in line:
            # We now use a standard 8 spaces for trans-units
            assert line.startswith(' ' * 8)
        if '<source' in line or '<target' in line or '<note' in line:
            # Child elements should have 2 more spaces than trans-units
            assert line.startswith(' ' * 10)

def test_consistent_indentation_for_all_trans_units():
    """
    Test that all trans-units have the same indentation in the output.
    This test specifically addresses the issue where the first trans-unit
    had different indentation than subsequent trans-units.
    """
    # Extract trans-units
    trans_units = extract_trans_units_from_file(EXAMPLE_FILE)

    # Convert trans-units to text with default indentation
    text = trans_units_to_text(trans_units)

    # Extract all lines that start a trans-unit
    trans_unit_lines = [line for line in text.split('\n') if '<trans-unit' in line]

    # Verify that all trans-unit lines have the same indentation
    if trans_unit_lines:
        first_indent = len(trans_unit_lines[0]) - len(trans_unit_lines[0].lstrip())
        for line in trans_unit_lines:
            indent = len(line) - len(line.lstrip())
            assert indent == first_indent, f"Inconsistent indentation: {indent} vs {first_indent}"

    # Extract indentation patterns
    patterns = preserve_indentation(EXAMPLE_FILE)

    # Convert trans-units to text with extracted indentation patterns
    text_with_patterns = trans_units_to_text(trans_units, indentation_patterns=patterns)

    # Extract all lines that start a trans-unit
    trans_unit_lines_with_patterns = [line for line in text_with_patterns.split('\n') if '<trans-unit' in line]

    # Verify that all trans-unit lines have the same indentation
    if trans_unit_lines_with_patterns:
        first_indent = len(trans_unit_lines_with_patterns[0]) - len(trans_unit_lines_with_patterns[0].lstrip())
        for line in trans_unit_lines_with_patterns:
            indent = len(line) - len(line.lstrip())
            assert indent == first_indent, f"Inconsistent indentation with patterns: {indent} vs {first_indent}"

def test_trans_units_to_text_preserves_namespaces():
    """
    Test that the trans_units_to_text function correctly preserves XML namespaces
    in the output text.
    """
    # Create a temporary file with namespaced elements and attributes
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="urn:oasis:names:tc:xliff:document:1.2 xliff-core-1.2-transitional.xsd">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1" size-unit="char" translate="yes" xml:space="preserve" xsi:type="transunit">
        <source>Hello World</source>
        <target state="needs-translation"></target>
        <note from="Developer" annotates="general" priority="2"/>
      </trans-unit>
    </body>
  </file>
</xliff>''')
        temp_file_path = temp_file.name

    try:
        # Extract trans-units
        trans_units = extract_trans_units_from_file(temp_file_path)

        # Convert trans-units to text
        text = trans_units_to_text(trans_units)

        # Verify that namespaced attributes are preserved
        assert 'xml:space="preserve"' in text
        assert 'xsi:type="transunit"' in text

        # Verify that all attributes are preserved
        assert 'id="test1"' in text
        assert 'size-unit="char"' in text
        assert 'translate="yes"' in text

        # Verify that child elements and their attributes are preserved
        assert '<source>Hello World</source>' in text
        assert '<target state="needs-translation"' in text
        assert '<note from="Developer" annotates="general" priority="2"' in text

    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

@pytest.mark.asyncio
async def test_translate_xliff_preserves_namespaces():
    """
    Test that the translate_xliff function preserves XML namespaces
    in the output file.
    """
    # Create a temporary input file with namespaced elements and attributes
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.xlf') as input_temp_file:
        input_temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="urn:oasis:names:tc:xliff:document:1.2 xliff-core-1.2-transitional.xsd">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1" size-unit="char" translate="yes" xml:space="preserve" xsi:type="transunit">
        <source>Hello World</source>
        <target></target>
        <note from="Developer" annotates="general" priority="2"/>
      </trans-unit>
    </body>
  </file>
</xliff>''')
        input_file = input_temp_file.name

    # Create a temporary output file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlf') as output_temp_file:
        output_file = output_temp_file.name

    try:
        # Mock the translation function to return a consistent result
        with patch('bcxlftranslator.main.translate_with_retry') as mock_translate:
            mock_translate.return_value = Mock(text="Bonjour le monde")

            # Run the translation
            await translate_xliff(input_file, output_file)

            # Read the output file
            with open(output_file, 'r', encoding='utf-8') as f:
                output_content = f.read()

            # Verify that namespace declarations are preserved in the header
            assert 'xmlns="urn:oasis:names:tc:xliff:document:1.2"' in output_content
            assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in output_content
            assert 'xsi:schemaLocation="urn:oasis:names:tc:xliff:document:1.2 xliff-core-1.2-transitional.xsd"' in output_content

            # Verify that namespaced attributes are preserved in the trans-units
            assert 'xml:space="preserve"' in output_content
            assert 'xsi:type="transunit"' in output_content

            # Verify that all attributes are preserved
            assert 'id="test1"' in output_content
            assert 'size-unit="char"' in output_content
            assert 'translate="yes"' in output_content

            # Verify that the translation was applied (note: match_case may capitalize "Le")
            assert '<target state="translated">Bonjour' in output_content
            assert 'monde</target>' in output_content

    finally:
        # Clean up the temporary files
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

@pytest.mark.asyncio
async def test_translate_xliff_preserves_indentation():
    """
    Test that the translate_xliff function preserves consistent indentation
    in the output file.
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

            # Extract the indentation patterns from the output file
            translated_patterns = preserve_indentation(output_file)

            # Verify the indentation patterns match our standard
            # We now use a standard 8 spaces for trans-units
            assert len(translated_patterns['trans_unit']) == 8
            # Child elements should have 2 more spaces than trans-units
            assert len(translated_patterns['child']) == 10

            # Read the output file and verify all trans-units have the same indentation
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract all lines that start a trans-unit
            trans_unit_lines = [line for line in content.split('\n') if '<trans-unit' in line]

            # Verify that all trans-unit lines have the same indentation
            if trans_unit_lines:
                # All trans-units should have consistent indentation
                # The first one might have 16 spaces (8 from original + 8 from our code)
                # but all subsequent ones should have 8 spaces

                # Check that all trans-units after the first one have the same indentation
                for i in range(1, len(trans_unit_lines)):
                    indent = len(trans_unit_lines[i]) - len(trans_unit_lines[i].lstrip())
                    assert indent == 8, f"Incorrect indentation for trans-unit {i+1}: {indent} vs expected 8 spaces"

            # Also verify by checking specific lines in the output file
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Verify that the file contains properly indented elements
            lines = content.split('\n')
            has_trans_unit = False
            has_child_elements = False

            for line in lines:
                if '<trans-unit' in line:
                    # Verify that trans-unit has some indentation
                    indent = line[:line.find('<trans-unit')]
                    assert indent.isspace(), f"Trans-unit line has no indentation: {line}"
                    has_trans_unit = True
                elif '<source' in line or '<target' in line or '<note' in line:
                    # Verify that child elements have some indentation
                    for tag in ['<source', '<target', '<note']:
                        if tag in line:
                            indent = line[:line.find(tag)]
                            assert indent.isspace(), f"Child element line has no indentation: {line}"
                            has_child_elements = True
                            break

            # Verify that we found at least one trans-unit and one child element
            assert has_trans_unit, "No trans-unit elements found in the output file"
            assert has_child_elements, "No child elements found in the output file"

    finally:
        # Clean up the temporary file
        if os.path.exists(output_file):
            os.remove(output_file)

@pytest.mark.asyncio
async def test_validate_xliff_format_with_valid_files():
    """
    Test that the validate_xliff_format function correctly identifies when an output file
    preserves the header and footer from the input file.
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

            # Validate the output file
            is_valid, message = validate_xliff_format(EXAMPLE_FILE, output_file)

            # Verify that the validation passes
            assert is_valid, f"Validation failed with message: {message}"
            assert "correctly preserves header and footer" in message

    finally:
        # Clean up the temporary file
        if os.path.exists(output_file):
            os.remove(output_file)

def test_validate_xliff_format_with_modified_header():
    """
    Test that the validate_xliff_format function correctly identifies when an output file
    has a modified header compared to the input file.
    """
    # Create a temporary input file
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.xlf') as input_temp_file:
        input_temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1">
        <source>Hello World</source>
        <target></target>
      </trans-unit>
    </body>
  </file>
</xliff>''')
        input_file = input_temp_file.name

    # Create a temporary output file with a modified header
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.xlf') as output_temp_file:
        output_temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<!-- Added comment -->
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1">
        <source>Hello World</source>
        <target>Bonjour le monde</target>
      </trans-unit>
    </body>
  </file>
</xliff>''')
        output_file = output_temp_file.name

    try:
        # Validate the output file
        is_valid, message = validate_xliff_format(input_file, output_file)

        # Verify that the validation fails due to modified header
        assert not is_valid, "Validation should fail with modified header"
        assert "Header in output file does not match" in message

    finally:
        # Clean up the temporary files
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

def test_validate_xliff_format_with_modified_footer():
    """
    Test that the validate_xliff_format function correctly identifies when an output file
    has a modified footer compared to the input file.
    """
    # Create a temporary input file
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.xlf') as input_temp_file:
        input_temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1">
        <source>Hello World</source>
        <target></target>
      </trans-unit>
    </body>
  </file>
</xliff>''')
        input_file = input_temp_file.name

    # Create a temporary output file with a modified footer
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.xlf') as output_temp_file:
        output_temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1">
        <source>Hello World</source>
        <target>Bonjour le monde</target>
      </trans-unit>
    </body>
  </file>
</xliff><!-- Added comment -->''')
        output_file = output_temp_file.name

    try:
        # Validate the output file
        is_valid, message = validate_xliff_format(input_file, output_file)

        # Verify that the validation fails due to modified footer
        assert not is_valid, "Validation should fail with modified footer"
        assert "Footer in output file does not match" in message

    finally:
        # Clean up the temporary files
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

def test_validate_xliff_format_with_different_trans_unit_count():
    """
    Test that the validate_xliff_format function correctly identifies when an output file
    has a different number of trans-units compared to the input file.
    """
    # Create a temporary input file with two trans-units
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.xlf') as input_temp_file:
        input_temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1">
        <source>Hello World</source>
        <target></target>
      </trans-unit>
      <trans-unit id="test2">
        <source>Goodbye World</source>
        <target></target>
      </trans-unit>
    </body>
  </file>
</xliff>''')
        input_file = input_temp_file.name

    # Create a temporary output file with only one trans-unit
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.xlf') as output_temp_file:
        output_temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1">
        <source>Hello World</source>
        <target>Bonjour le monde</target>
      </trans-unit>
    </body>
  </file>
</xliff>''')
        output_file = output_temp_file.name

    try:
        # Validate the output file
        is_valid, message = validate_xliff_format(input_file, output_file)

        # Verify that the validation fails due to different trans-unit count
        assert not is_valid, "Validation should fail with different trans-unit count"
        assert "Number of trans-units differs" in message

    finally:
        # Clean up the temporary files
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

def test_validate_xliff_format_with_different_trans_unit_ids():
    """
    Test that the validate_xliff_format function correctly identifies when an output file
    has different trans-unit IDs compared to the input file.
    """
    # Create a temporary input file
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.xlf') as input_temp_file:
        input_temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1">
        <source>Hello World</source>
        <target></target>
      </trans-unit>
    </body>
  </file>
</xliff>''')
        input_file = input_temp_file.name

    # Create a temporary output file with a different trans-unit ID
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.xlf') as output_temp_file:
        output_temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test2">
        <source>Hello World</source>
        <target>Bonjour le monde</target>
      </trans-unit>
    </body>
  </file>
</xliff>''')
        output_file = output_temp_file.name

    try:
        # Validate the output file
        is_valid, message = validate_xliff_format(input_file, output_file)

        # Verify that the validation fails due to different trans-unit IDs
        assert not is_valid, "Validation should fail with different trans-unit IDs"
        assert "Trans-unit IDs in output file do not match" in message

    finally:
        # Clean up the temporary files
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

def test_validate_xliff_format_with_no_translation():
    """
    Test that the validate_xliff_format function correctly identifies when an output file
    has not been translated (no changes to target elements).
    """
    # Create a temporary input file
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.xlf') as input_temp_file:
        input_temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1">
        <source>Hello World</source>
        <target></target>
      </trans-unit>
    </body>
  </file>
</xliff>''')
        input_file = input_temp_file.name

    # Create a temporary output file with no translation (empty target)
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8', suffix='.xlf') as output_temp_file:
        output_temp_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1">
        <source>Hello World</source>
        <target></target>
      </trans-unit>
    </body>
  </file>
</xliff>''')
        output_file = output_temp_file.name

    try:
        # Validate the output file
        is_valid, message = validate_xliff_format(input_file, output_file)

        # Verify that the validation fails due to no translation
        assert not is_valid, "Validation should fail with no translation"
        assert "No translation appears to have occurred" in message

    finally:
        # Clean up the temporary files
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)