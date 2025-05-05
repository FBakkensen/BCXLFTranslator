import pytest
import os
import sys
import asyncio
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil
import gc

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from bcxlftranslator.main import translate_xliff, translate_with_retry, Translator, LANGUAGES
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch
import tempfile
import shutil
import gc

@pytest.fixture
def test_files():
    input_file = os.path.join(os.path.dirname(__file__), 'fixtures', 'test.xlf')
    output_file = os.path.join(os.path.dirname(__file__), 'test_output.xlf')
    return input_file, output_file

@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
async def test_translation_process(test_files):
    """
    Given a valid XLIFF file for translation
    When the translate_xliff function is called
    Then it should translate the file correctly and preserve format-specific attributes
    """
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

    try:
        # Cleanup
        from bcxlftranslator.terminology_db import close_terminology_database
        close_terminology_database()
        import gc
        gc.collect()
    finally:
        from bcxlftranslator.terminology_db import TerminologyDatabaseRegistry
        TerminologyDatabaseRegistry.close_all()
        import gc
        gc.collect()

@pytest.mark.asyncio
async def test_translation_error_handling(test_files):
    """
    Given a non-existent input file
    When the translate_xliff function is called
    Then it should raise SystemExit
    """
    input_file = "nonexistent.xlf"
    output_file = "error_output.xlf"

    with pytest.raises(SystemExit):
        await translate_xliff(input_file, output_file)

@pytest.mark.asyncio
async def test_translation_retry_mechanism():
    """
    Given a translator that fails twice then succeeds
    When the translate_with_retry function is called
    Then it should retry and eventually return a successful translation
    """
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
    """
    Given an XLIFF file with duplicate text
    When the translate_xliff function is called
    Then it should only translate each unique text once and reuse cached translations
    """
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
    """
    Given an XLIFF file with short language codes (en/da instead of en-US/da-DK)
    When the translate_xliff function is called
    Then it should correctly handle the language codes and translate successfully
    """
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
    """
    Given an XLIFF file containing XML special characters (&, <, >, ", ')
    When the translate_xliff function is called
    Then it should properly handle character escaping while preserving the meaning
    """
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
    """
    Given an output file path with non-existent parent directories
    When the translate_xliff function is called
    Then it should create all the necessary directories before writing the file
    """
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

@pytest.mark.asyncio
async def test_translation_state_attributes():
    """
    Given an XLIFF file with trans-unit containing multiple attributes and notes
    When the translate_xliff function is called
    Then it should update the state correctly and preserve appropriate attributes and notes
    """
    input_content = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en-US" target-language="da-DK">
    <body>
      <trans-unit id="Test" size-unit="char" translate="yes" xml:space="preserve">
        <source>Test text</source>
        <target state="needs-translation"></target>
        <note from="Developer" annotates="general" priority="2"></note>
        <note from="Xliff Generator" annotates="general" priority="3">Some note</note>
        <note from="NAB AL Tool Refresh Xlf" annotates="general" priority="3">New translation.</note>
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

@pytest.mark.asyncio
async def test_translation_with_terminology(monkeypatch, tmp_path):
    """
    Given terminology usage is enabled and a terminology DB is available
    When the translate_xliff function is called
    Then it should use terminology for matching terms, fall back to Google Translate when not found, and report terminology status
    """
    # Setup test input and output files
    input_file = os.path.join(os.path.dirname(__file__), 'fixtures', 'test.xlf')
    output_file = tmp_path / 'output_with_terminology.xlf'

    # Mock terminology_lookup to return a translation for a specific term
    def mock_terminology_lookup(source_text, target_lang_code):
        if source_text == "Offer":
            return "Salgstilbud"  # Simulate terminology match
        return None  # Simulate fallback

    # Patch terminology_lookup and translation
    with patch('bcxlftranslator.main.terminology_lookup', side_effect=mock_terminology_lookup) as mock_term_lookup, \
         patch('bcxlftranslator.main.Translator') as mock_translator_cls, \
         patch('bcxlftranslator.main.match_case', side_effect=lambda s, t: t), \
         patch('bcxlftranslator.note_generation.add_note_to_trans_unit') as mock_add_note:

        # Setup mock translator for fallback
        mock_translator = Mock()
        mock_translator.translate = AsyncMock(return_value=Mock(text="Oversættelse"))
        mock_translator_cls.return_value.__aenter__.return_value = mock_translator

        # Run translation with terminology enabled
        import sys
        sys.argv = [sys.argv[0], '--use-terminology', input_file, str(output_file)]
        await translate_xliff(input_file, str(output_file))

        # Check terminology_lookup was called for all units
        assert mock_term_lookup.called
        # Check that fallback translation was used for non-matching terms
        assert mock_translator.translate.called
        # Check that a note was added for terminology usage
        assert mock_add_note.called

        # Optionally, parse output and check target text for terminology match
        tree = ET.parse(str(output_file))
        root = tree.getroot()
        ns = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2'}
        for unit in root.findall('.//xliff:trans-unit', ns):
            source = unit.find('xliff:source', ns).text
            target = unit.find('xliff:target', ns).text
            if source == "Offer":
                assert target == "Salgstilbud"

@pytest.fixture(autouse=True)
def close_db_after_test():
    yield
    from bcxlftranslator.terminology_db import TerminologyDatabaseRegistry
    TerminologyDatabaseRegistry.close_all()
    import gc
    gc.collect()  # Force cleanup of any unclosed connections

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