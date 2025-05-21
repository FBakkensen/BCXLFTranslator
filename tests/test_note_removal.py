"""
Tests for the note removal functionality in BCXLFTranslator.
"""
import os
import pytest
import tempfile
import xml.etree.ElementTree as ET
import asyncio
from unittest.mock import Mock, patch

from bcxlftranslator.main import remove_specific_notes, translate_xliff

class TestNoteRemoval:
    """Tests for the note removal functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a sample trans-unit with various notes
        self.xliff_ns = "urn:oasis:names:tc:xliff:document:1.2"
        self.ns = "{" + self.xliff_ns + "}"

        # Create a trans-unit element
        self.trans_unit = ET.Element(f"{self.ns}trans-unit")
        self.trans_unit.set("id", "test1")

        # Add source and target elements
        source = ET.SubElement(self.trans_unit, f"{self.ns}source")
        source.text = "Test Source"

        target = ET.SubElement(self.trans_unit, f"{self.ns}target")
        target.text = ""

        # Add various note elements
        note1 = ET.SubElement(self.trans_unit, f"{self.ns}note")
        note1.set("from", "Developer")
        note1.set("annotates", "general")
        note1.set("priority", "2")

        note2 = ET.SubElement(self.trans_unit, f"{self.ns}note")
        note2.set("from", "NAB AL Tool Refresh Xlf")
        note2.set("annotates", "general")
        note2.set("priority", "3")
        note2.text = "New translation."

        note3 = ET.SubElement(self.trans_unit, f"{self.ns}note")
        note3.set("from", "Xliff Generator")
        note3.set("annotates", "general")
        note3.set("priority", "3")
        note3.text = "Table Test - Property Caption"

    def test_remove_specific_notes(self):
        """Test that notes with from='NAB AL Tool Refresh Xlf' are removed."""
        # Count notes before removal
        notes_before = len(self.trans_unit.findall(f"{self.ns}note"))
        assert notes_before == 3

        # Check that the specific note exists
        nab_notes = [note for note in self.trans_unit.findall(f"{self.ns}note")
                    if note.get("from") == "NAB AL Tool Refresh Xlf"]
        assert len(nab_notes) == 1

        # Call the function to remove specific notes
        result = remove_specific_notes(self.trans_unit, self.ns)

        # Verify the result
        assert result is True

        # Count notes after removal
        notes_after = len(self.trans_unit.findall(f"{self.ns}note"))
        assert notes_after == 2

        # Check that the specific note was removed
        nab_notes_after = [note for note in self.trans_unit.findall(f"{self.ns}note")
                          if note.get("from") == "NAB AL Tool Refresh Xlf"]
        assert len(nab_notes_after) == 0

        # Check that other notes are preserved
        dev_notes = [note for note in self.trans_unit.findall(f"{self.ns}note")
                    if note.get("from") == "Developer"]
        assert len(dev_notes) == 1

        xliff_gen_notes = [note for note in self.trans_unit.findall(f"{self.ns}note")
                          if note.get("from") == "Xliff Generator"]
        assert len(xliff_gen_notes) == 1

    def test_remove_specific_notes_none_found(self):
        """Test behavior when no matching notes are found."""
        # Remove the NAB note first
        for note in self.trans_unit.findall(f"{self.ns}note"):
            if note.get("from") == "NAB AL Tool Refresh Xlf":
                self.trans_unit.remove(note)

        # Count notes before removal
        notes_before = len(self.trans_unit.findall(f"{self.ns}note"))
        assert notes_before == 2

        # Call the function to remove specific notes
        result = remove_specific_notes(self.trans_unit, self.ns)

        # Verify the result
        assert result is False

        # Count notes after removal - should be unchanged
        notes_after = len(self.trans_unit.findall(f"{self.ns}note"))
        assert notes_after == 2

    def test_remove_specific_notes_null_input(self):
        """Test behavior with null input."""
        result = remove_specific_notes(None, self.ns)
        assert result is False

@pytest.mark.asyncio
async def test_integration_note_removal():
    """
    Integration test to verify that notes are removed during translation.
    """
    # Create a temporary XLIFF file with a note that should be removed
    xliff_content = """<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1">
        <source>Hello World</source>
        <target></target>
        <note from="Developer" annotates="general" priority="2"></note>
        <note from="NAB AL Tool Refresh Xlf" annotates="general" priority="3">New translation.</note>
        <note from="Xliff Generator" annotates="general" priority="3">Table Test - Property Caption</note>
      </trans-unit>
    </body>
  </file>
</xliff>
"""

    # Create temporary input and output files
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlf') as temp_input:
        input_file = temp_input.name
        temp_input.write(xliff_content.encode('utf-8'))

    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlf') as temp_output:
        output_file = temp_output.name

    try:
        # Mock the translator to avoid actual API calls
        with patch('bcxlftranslator.main.translate_with_retry') as mock_translate:
            # Set up the mock to return a translation
            mock_result = Mock()
            mock_result.text = "Bonjour le monde"
            mock_translate.return_value = mock_result

            # Run the translation
            await translate_xliff(input_file, output_file)

            # Parse the output file
            tree = ET.parse(output_file)
            root = tree.getroot()
            ns = {'x': 'urn:oasis:names:tc:xliff:document:1.2'}

            # Find the trans-unit
            trans_unit = root.find('.//x:trans-unit', ns)
            assert trans_unit is not None

            # Check that the target was translated
            target = trans_unit.find('x:target', ns)
            assert target is not None
            # The case matching function might capitalize "Le" to match "World"
            assert target.text.lower() == "bonjour le monde"

            # Check that the NAB note was removed
            nab_notes = trans_unit.findall('.//x:note[@from="NAB AL Tool Refresh Xlf"]', ns)
            assert len(nab_notes) == 0

            # Check that other notes are preserved
            dev_notes = trans_unit.findall('.//x:note[@from="Developer"]', ns)
            assert len(dev_notes) == 1

            xliff_gen_notes = trans_unit.findall('.//x:note[@from="Xliff Generator"]', ns)
            assert len(xliff_gen_notes) == 1

            # Check that the BCXLFTranslator note was added
            bcxlf_notes = trans_unit.findall('.//x:note[@from="BCXLFTranslator"]', ns)
            assert len(bcxlf_notes) == 1

    finally:
        # Clean up temporary files
        if os.path.exists(input_file):
            os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)
