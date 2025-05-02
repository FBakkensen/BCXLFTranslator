import pytest
import os
import sys
import asyncio

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from bcxlftranslator.main import translate_xliff, translate_with_retry, Translator, LANGUAGES
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch
import tempfile
import shutil

@pytest.fixture
def test_files():
    input_file = os.path.join(os.path.dirname(__file__), 'fixtures', 'test.xlf')
    output_file = os.path.join(os.path.dirname(__file__), 'test_output.xlf')
    return input_file, output_file

@pytest.mark.asyncio
async def test_translation_process(test_files):
    input_file, output_file = test_files

    # Run translation
    await translate_xliff(input_file, output_file)

    # Verify the output file exists
    assert os.path.exists(output_file)

    # Parse and verify the translated file
    xliff_ns = 'urn:oasis:names:tc:xliff:document:1.2'
    ns = {'xliff': xliff_ns}

    tree = ET.parse(output_file)
    root = tree.getroot()

    # Get all translation units
    trans_units = root.findall('.//xliff:trans-unit', ns)

    # Verify we have the expected number of units
    assert len(trans_units) == 4

    # Check specific translations
    for unit in trans_units:
        unit_id = unit.get('id')
        source = unit.find('xliff:source', ns).text
        target = unit.find('xliff:target', ns)

        if unit_id == '3':
            # This unit should be skipped (translate="no")
            assert target.get('state') == 'needs-translation'
        else:
            # All other units should be translated
            assert target.text is not None
            assert target.get('state') == 'translated'

            # Verify case matching
            if unit_id == '4':
                assert target.text.isupper()
            elif unit_id == '2':
                # Verify comma-separated list handling
                assert target.text.count(',') == 2
                parts = [p.strip() for p in target.text.split(',')]
                assert all(p[0].isupper() for p in parts)

@pytest.mark.asyncio
async def test_translation_error_handling(test_files):
    input_file = "nonexistent.xlf"
    output_file = "error_output.xlf"

    with pytest.raises(SystemExit):
        await translate_xliff(input_file, output_file)

@pytest.mark.asyncio
async def test_translation_retry_mechanism():
    """Test that translation retry mechanism works properly"""
    # Mock translator that fails twice then succeeds
    class MockTranslator:
        def __init__(self):
            self.attempts = 0

        async def translate(self, text, dest, src):
            self.attempts += 1
            if self.attempts < 3:
                raise Exception("Translation failed")
            return Mock(text="translated text")

    translator = MockTranslator()
    result = await translate_with_retry(translator, "test", "da", "en")
    assert result is not None
    assert translator.attempts == 3

@pytest.mark.asyncio
async def test_translation_cache():
    """Test that translation caching works properly"""
    input_content = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en-US" target-language="da-DK">
    <body>
      <trans-unit id="1">
        <source>Duplicate text</source>
        <target state="needs-translation"></target>
      </trans-unit>
      <trans-unit id="2">
        <source>Duplicate text</source>
        <target state="needs-translation"></target>
      </trans-unit>
    </body>
  </file>
</xliff>'''

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlf') as f:
        f.write(input_content)
        temp_input = f.name

    temp_output = temp_input + '.out.xlf'

    try:
        # Run translation
        await translate_xliff(temp_input, temp_output)

        # Parse output and verify cache was used
        tree = ET.parse(temp_output)
        root = tree.getroot()
        ns = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2'}

        units = root.findall('.//xliff:trans-unit', ns)
        assert len(units) == 2

        # Both units should have the same translation
        translations = [u.find('xliff:target', ns).text for u in units]
        assert translations[0] == translations[1]

    finally:
        # Cleanup
        os.unlink(temp_input)
        if os.path.exists(temp_output):
            os.unlink(temp_output)

@pytest.mark.asyncio
async def test_language_code_handling():
    """Test handling of different language codes"""
    input_content = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en" target-language="da">
    <body>
      <trans-unit id="1">
        <source>Test</source>
        <target state="needs-translation"></target>
      </trans-unit>
    </body>
  </file>
</xliff>'''

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlf') as f:
        f.write(input_content)
        temp_input = f.name

    temp_output = temp_input + '.out.xlf'

    try:
        # Run translation
        await translate_xliff(temp_input, temp_output)

        # Verify file was processed successfully
        assert os.path.exists(temp_output)

    finally:
        # Cleanup
        os.unlink(temp_input)
        if os.path.exists(temp_output):
            os.unlink(temp_output)

@pytest.mark.asyncio
async def test_special_characters():
    """Test handling of special characters in translation"""
    special_chars = "Hello & < > \" ' world"  # XML special characters
    escaped_chars = "Hello &amp; &lt; &gt; &quot; &apos; world"  # Escaped version
    input_content = f'''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en-US" target-language="da-DK">
    <body>
      <trans-unit id="1">
        <source>{escaped_chars}</source>
        <target state="needs-translation"></target>
      </trans-unit>
    </body>
  </file>
</xliff>'''

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlf') as f:
        f.write(input_content)
        temp_input = f.name

    temp_output = temp_input + '.out.xlf'

    try:
        # Run translation
        await translate_xliff(temp_input, temp_output)

        # Parse and verify special characters were preserved
        tree = ET.parse(temp_output)
        root = tree.getroot()
        ns = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2'}

        source = root.find('.//xliff:source', ns).text
        assert source == special_chars

    finally:
        # Cleanup
        os.unlink(temp_input)
        if os.path.exists(temp_output):
            os.unlink(temp_output)

@pytest.mark.asyncio
async def test_output_directory_creation():
    """Test creation of output directory structure"""
    temp_dir = tempfile.mkdtemp()
    try:
        nested_dir = os.path.join(temp_dir, "a", "b", "c")
        output_file = os.path.join(nested_dir, "output.xlf")

        # Copy test.xlf to a temporary location
        input_file = os.path.join(os.path.dirname(__file__), 'fixtures', 'test.xlf')
        temp_input = os.path.join(temp_dir, "test.xlf")
        shutil.copy(input_file, temp_input)

        # Run translation
        await translate_xliff(temp_input, output_file)

        # Verify directory was created and file exists
        assert os.path.exists(nested_dir)
        assert os.path.exists(output_file)

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

# Update the cleanup fixture to handle new test files
@pytest.fixture(autouse=True)
def cleanup():
    yield
    patterns = ['test_output.xlf', '*.out.xlf']
    test_dir = os.path.dirname(__file__)
    for pattern in patterns:
        for file in [f for f in os.listdir(test_dir) if f.endswith(pattern)]:
            try:
                os.remove(os.path.join(test_dir, file))
            except OSError:
                pass

@pytest.mark.asyncio
async def test_translation_state_attributes():
    """Test that translation updates all required attributes and elements"""
    input_content = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en-US" target-language="da-DK">
    <body>
      <trans-unit id="Test" size-unit="char" translate="yes" xml:space="preserve">
        <source>Test text</source>
        <target state="needs-translation"></target>
        <note from="Developer" annotates="general" priority="2"></note>
        <note from="NAB AL Tool Refresh Xlf" annotates="general" priority="3">New translation.</note>
        <note from="Xliff Generator" annotates="general" priority="3">Some note</note>
      </trans-unit>
    </body>
  </file>
</xliff>'''

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlf') as f:
        f.write(input_content)
        temp_input = f.name

    temp_output = temp_input + '.out.xlf'

    try:
        # Run translation
        await translate_xliff(temp_input, temp_output)

        # Parse and verify the translated output
        tree = ET.parse(temp_output)
        root = tree.getroot()
        ns = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2'}

        # Get the translated unit
        unit = root.find('.//xliff:trans-unit', ns)
        target = unit.find('xliff:target', ns)

        # Verify target attributes
        assert target.get('state') == 'translated'
        assert target.get('state-qualifier') == 'exact-match'

        # Verify notes
        notes = unit.findall('xliff:note', ns)
        note_sources = [note.get('from') for note in notes]

        # Should have Developer and Xliff Generator notes, but not NAB AL Tool Refresh Xlf
        assert 'Developer' in note_sources
        assert 'Xliff Generator' in note_sources
        assert 'NAB AL Tool Refresh Xlf' not in note_sources

        # Verify original attributes are preserved
        assert unit.get('size-unit') == 'char'
        assert unit.get('translate') == 'yes'
        # Check xml:space using the full namespace URI
        assert unit.get('{http://www.w3.org/XML/1998/namespace}space') == 'preserve'

    finally:
        # Cleanup
        os.unlink(temp_input)
        if os.path.exists(temp_output):
            os.unlink(temp_output)

import pytest
import os
import sys
import asyncio
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, patch

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from bcxlftranslator.main import translate_xliff, translate_with_retry, Translator, LANGUAGES
from bcxlftranslator import note_generation

# ... existing test code remains the same ...

# Replace the TestAttributionProcess class with pytest-style async tests
@pytest.fixture
def attribution_test_files():
    """Setup test files for attribution tests."""
    xliff_content = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en-US" target-language="da-DK" datatype="xml">
    <body>
      <trans-unit id="Table 123456789" translate="yes">
        <source>Sales Quote</source>
        <target state="needs-translation"></target>
      </trans-unit>
    </body>
  </file>
</xliff>'''

    # Create temp files for input and output
    input_file = 'tests/fixtures/temp_input.xlf'
    output_file = 'tests/fixtures/temp_output.xlf'

    # Ensure the fixtures directory exists
    os.makedirs('tests/fixtures', exist_ok=True)

    # Write test content to input file
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(xliff_content)

    yield input_file, output_file

    # Cleanup after test
    for file in [input_file, output_file]:
        if os.path.exists(file):
            os.remove(file)

@pytest.mark.asyncio
async def test_microsoft_terminology_attribution(attribution_test_files):
    """Test that Microsoft Terminology translations are properly attributed."""
    input_file, output_file = attribution_test_files

    # Create mocks
    with patch('bcxlftranslator.main.Translator') as mock_translator_cls, \
         patch('bcxlftranslator.main.match_case') as mock_match_case, \
         patch('bcxlftranslator.note_generation.add_note_to_trans_unit') as mock_add_note, \
         patch('bcxlftranslator.main.terminology_lookup', return_value='Salgstilbud'):

        # Setup mocks
        mock_translator = MagicMock()
        mock_translator_cls.return_value.__aenter__.return_value = mock_translator
        mock_match_case.return_value = 'Salgstilbud'

        # Run the translation process
        await translate_xliff(input_file, output_file)

        # Verify note_generation.add_note_to_trans_unit was called
        mock_add_note.assert_called()
        # Check that the note contains "Microsoft Terminology"
        args, _ = mock_add_note.call_args
        assert "Microsoft Terminology" in args[1]

@pytest.mark.asyncio
async def test_google_translate_attribution(attribution_test_files):
    """Test that Google Translate translations are properly attributed."""
    input_file, output_file = attribution_test_files

    # Create mocks
    with patch('bcxlftranslator.main.Translator') as mock_translator_cls, \
         patch('bcxlftranslator.main.match_case') as mock_match_case, \
         patch('bcxlftranslator.note_generation.add_note_to_trans_unit') as mock_add_note, \
         patch('bcxlftranslator.main.terminology_lookup', return_value=None), \
         patch('bcxlftranslator.main.translate_with_retry') as mock_translate_with_retry:

        # Setup mocks for the translation process
        mock_translator = MagicMock()
        mock_translator_cls.return_value.__aenter__.return_value = mock_translator

        # Mock the translate_with_retry function to return a translated result
        mock_translate_with_retry.return_value = 'Tilbud'

        # Mock match_case to return the input (no case changes for simplicity)
        mock_match_case.return_value = 'Tilbud'

        # Run the translation process
        await translate_xliff(input_file, output_file)

        # Verify note_generation.add_note_to_trans_unit was called
        mock_add_note.assert_called()
        # Check that the note contains "Google Translate"
        args, _ = mock_add_note.call_args
        assert "Google Translate" in args[1]

@pytest.mark.asyncio
async def test_attribution_disabled(attribution_test_files):
    """Test that attribution can be disabled."""
    input_file, output_file = attribution_test_files

    # Create mocks
    with patch('bcxlftranslator.main.Translator') as mock_translator_cls, \
         patch('bcxlftranslator.note_generation.add_note_to_trans_unit') as mock_add_note:

        # Setup mocks
        mock_translator = MagicMock()
        mock_translator_cls.return_value.__aenter__.return_value = mock_translator

        # Run the translation process with attribution disabled
        await translate_xliff(input_file, output_file, add_attribution=False)

        # Verify note_generation.add_note_to_trans_unit was not called
        mock_add_note.assert_not_called()

@pytest.mark.asyncio
async def test_attribution_metadata(attribution_test_files):
    """Test that attribution contains metadata about the translation."""
    input_file, output_file = attribution_test_files

    # Create mocks
    with patch('bcxlftranslator.main.Translator') as mock_translator_cls, \
         patch('bcxlftranslator.main.match_case') as mock_match_case, \
         patch('bcxlftranslator.note_generation.generate_attribution_note') as mock_generate_note, \
         patch('bcxlftranslator.note_generation.add_note_to_trans_unit') as mock_add_note, \
         patch('bcxlftranslator.main.terminology_lookup', return_value='Salgstilbud'):

        # Setup mocks
        mock_translator = MagicMock()
        mock_translator_cls.return_value.__aenter__.return_value = mock_translator
        mock_match_case.return_value = 'Salgstilbud'

        # Setup the mock generate_attribution_note to return a valid note
        mock_generate_note.return_value = "Source: Microsoft Terminology"

        # Run the translation process
        await translate_xliff(input_file, output_file)

        # Verify generate_attribution_note was called with metadata
        mock_generate_note.assert_called()

        # Just verify it was called with some parameters indicating metadata was passed
        call_kwargs = mock_generate_note.call_args.kwargs
        assert "metadata" in call_kwargs
        assert "source_text" in call_kwargs["metadata"]