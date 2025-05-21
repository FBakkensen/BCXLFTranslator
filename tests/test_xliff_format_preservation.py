import os
import pytest
import tempfile
from pathlib import Path

from bcxlftranslator.xliff_parser import extract_header_footer
from bcxlftranslator.exceptions import EmptyXliffError

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
