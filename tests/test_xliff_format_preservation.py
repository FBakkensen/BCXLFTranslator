import os
import pytest
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from bcxlftranslator.xliff_parser import extract_header_footer, extract_trans_units, extract_trans_units_from_file, trans_units_to_text
from bcxlftranslator.exceptions import EmptyXliffError, InvalidXliffError

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
    Test that the extract_header_footer function raises ValueError
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
        with pytest.raises(ValueError, match="No trans-unit elements found"):
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