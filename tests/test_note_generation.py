import unittest
from unittest.mock import patch, MagicMock
import pytest
from datetime import datetime
import sys
import os
import xml.etree.ElementTree as ET

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from bcxlftranslator import note_generation


class TestNoteGeneration(unittest.TestCase):
    """Test cases for attribution note generation functionality."""

    def test_generate_microsoft_terminology_note(self):
        """Test generating a note for Microsoft Terminology source."""
        note = note_generation.generate_attribution_note(source="MICROSOFT")

        # Basic validation of the note content
        self.assertIsNotNone(note)
        self.assertIn("Microsoft Terminology", note)

    def test_generate_google_translate_note(self):
        """Test generating a note for Google Translate source."""
        note = note_generation.generate_attribution_note(source="GOOGLE")

        # Basic validation of the note content
        self.assertIsNotNone(note)
        self.assertIn("Google Translate", note)

    def test_generate_note_with_custom_metadata(self):
        """Test generating a note with additional metadata."""
        metadata = {
            "term": "Quote",
            "translated_term": "Tilbud",
            "object_type": "Field"
        }
        note = note_generation.generate_attribution_note(
            source="MICROSOFT",
            metadata=metadata
        )

        # Check if metadata is included in the note
        self.assertIn("Quote", note)
        self.assertIn("Tilbud", note)
        self.assertIn("Field", note)

    def test_generate_note_with_timestamp(self):
        """Test that notes include a timestamp."""
        with patch('bcxlftranslator.note_generation.datetime') as mock_datetime:
            # Set a fixed datetime for testing
            mock_date = datetime(2025, 5, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_date
            mock_datetime.strftime = datetime.strftime

            note = note_generation.generate_attribution_note(source="MICROSOFT")

            # Check if the timestamp is included in the note
            self.assertIn("2025-05-01", note)

    def test_invalid_source(self):
        """Test handling of invalid source type."""
        with pytest.raises(ValueError):
            note_generation.generate_attribution_note(source="INVALID_SOURCE")

    def test_generate_mixed_source_note(self):
        """Test generating a note for translations with mixed sources."""
        note = note_generation.generate_attribution_note(source="MIXED",
                                                        microsoft_percentage=70,
                                                        google_percentage=30)

        # Check if both sources are mentioned and percentages are included
        self.assertIn("Microsoft Terminology", note)
        self.assertIn("Google Translate", note)
        self.assertIn("70%", note)
        self.assertIn("30%", note)

    def test_custom_attribution_template(self):
        """Test using a custom attribution template."""
        # Test with a custom template for Microsoft source
        template = "Custom template: {source} translated {term} on {date}"
        note = note_generation.generate_attribution_note(
            source="MICROSOFT",
            template=template,
            metadata={"term": "Quote"}
        )

        # Verify the custom template was used
        self.assertIn("Custom template:", note)
        self.assertIn("Microsoft Terminology", note)
        self.assertIn("translated Quote on", note)

    def test_custom_template_with_all_placeholders(self):
        """Test a custom template with all possible placeholders."""
        template = "{source} - {term}:{translated_term} ({date}, {time})"
        metadata = {
            "term": "Quote",
            "translated_term": "Tilbud"
        }

        with patch('bcxlftranslator.note_generation.datetime') as mock_datetime:
            # Set a fixed datetime for testing
            mock_date = datetime(2025, 5, 1, 12, 30, 45)
            mock_datetime.now.return_value = mock_date
            mock_datetime.strftime = datetime.strftime

            note = note_generation.generate_attribution_note(
                source="MICROSOFT",
                template=template,
                metadata=metadata
            )

        # Verify all placeholders were replaced
        self.assertEqual(note, "Microsoft Terminology - Quote:Tilbud (2025-05-01, 12:30:45)")

    def test_template_missing_required_placeholders(self):
        """Test that a template must have required placeholders."""
        # Template missing the {source} placeholder, which is required
        template = "Translation generated on {date}"

        with pytest.raises(ValueError):
            note_generation.generate_attribution_note(
                source="MICROSOFT",
                template=template
            )

    def test_default_templates(self):
        """Test using the default templates."""
        # Test getting the default Microsoft template
        microsoft_template = note_generation.get_default_template("MICROSOFT")
        self.assertIsNotNone(microsoft_template)
        self.assertIn("{source}", microsoft_template)

        # Test getting the default Google template
        google_template = note_generation.get_default_template("GOOGLE")
        self.assertIsNotNone(google_template)
        self.assertIn("{source}", google_template)

        # Test getting the default Mixed template
        mixed_template = note_generation.get_default_template("MIXED")
        self.assertIsNotNone(mixed_template)
        self.assertIn("{microsoft_percentage}", mixed_template)

    def test_template_with_missing_metadata(self):
        """Test handling a template with placeholders for missing metadata."""
        template = "{source} - {term}:{translated_term}"

        # No metadata provided but template requires it
        with pytest.raises(KeyError):
            note_generation.generate_attribution_note(
                source="MICROSOFT",
                template=template
            )

        # Partial metadata provided
        metadata = {"term": "Quote"}  # Missing translated_term
        with pytest.raises(KeyError):
            note_generation.generate_attribution_note(
                source="MICROSOFT",
                template=template,
                metadata=metadata
            )


class TestXliffNoteIntegration(unittest.TestCase):
    """Test cases for integrating attribution notes into XLIFF trans-units."""

    def setUp(self):
        """Set up the XML namespace for XLIFF files."""
        self.xliff_ns = 'urn:oasis:names:tc:xliff:document:1.2'
        ET.register_namespace('', self.xliff_ns)
        self.ns = {'xliff': self.xliff_ns}

        # Create a simple trans-unit element for testing
        self.trans_unit = ET.Element('{%s}trans-unit' % self.xliff_ns, id='test-id')
        self.source = ET.SubElement(self.trans_unit, '{%s}source' % self.xliff_ns)
        self.source.text = 'Test source'
        self.target = ET.SubElement(self.trans_unit, '{%s}target' % self.xliff_ns)
        self.target.text = 'Test target'

    def test_add_note_to_trans_unit(self):
        """Test adding a note to a trans-unit with no existing notes."""
        note_text = "Source: Microsoft Terminology"

        # Call the function to add a note
        result = note_generation.add_note_to_trans_unit(
            self.trans_unit,
            note_text,
            from_attribute="BCXLFTranslator"
        )

        # Verify the note was added correctly
        self.assertTrue(result)

        # Check if the note element exists and has correct attributes and text
        notes = self.trans_unit.findall('.//{%s}note' % self.xliff_ns)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].text, note_text)
        self.assertEqual(notes[0].get('from'), 'BCXLFTranslator')

    def test_add_note_to_trans_unit_with_existing_note(self):
        """Test adding a note to a trans-unit that already has a note."""
        # Add an existing note first
        existing_note = ET.SubElement(self.trans_unit, '{%s}note' % self.xliff_ns)
        existing_note.text = "Existing note"
        existing_note.set('from', 'OtherSource')

        note_text = "Source: Google Translate"

        # Call the function to add a new note
        result = note_generation.add_note_to_trans_unit(
            self.trans_unit,
            note_text,
            from_attribute="BCXLFTranslator"
        )

        # Verify the note was added correctly
        self.assertTrue(result)

        # Check if both notes exist
        notes = self.trans_unit.findall('.//{%s}note' % self.xliff_ns)
        self.assertEqual(len(notes), 2)

        # Find our new note
        bc_notes = [note for note in notes if note.get('from') == 'BCXLFTranslator']
        self.assertEqual(len(bc_notes), 1)
        self.assertEqual(bc_notes[0].text, note_text)

        # Ensure the existing note is still there
        other_notes = [note for note in notes if note.get('from') == 'OtherSource']
        self.assertEqual(len(other_notes), 1)
        self.assertEqual(other_notes[0].text, "Existing note")

    def test_add_note_updating_existing_note(self):
        """Test updating an existing note from the same source."""
        # Add an existing note first
        existing_note = ET.SubElement(self.trans_unit, '{%s}note' % self.xliff_ns)
        existing_note.text = "Source: Google Translate"
        existing_note.set('from', 'BCXLFTranslator')

        new_note_text = "Source: Microsoft Terminology"

        # Call the function to update the note, with update_existing=True
        result = note_generation.add_note_to_trans_unit(
            self.trans_unit,
            new_note_text,
            from_attribute="BCXLFTranslator",
            update_existing=True
        )

        # Verify the note was updated correctly
        self.assertTrue(result)

        # Check that there's still only one note and it has the new text
        notes = self.trans_unit.findall('.//{%s}note' % self.xliff_ns)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].text, new_note_text)
        self.assertEqual(notes[0].get('from'), 'BCXLFTranslator')

    def test_add_note_without_update_existing(self):
        """Test adding a new note when update_existing=False."""
        # Add an existing note first
        existing_note = ET.SubElement(self.trans_unit, '{%s}note' % self.xliff_ns)
        existing_note.text = "Source: Google Translate"
        existing_note.set('from', 'BCXLFTranslator')

        new_note_text = "Source: Microsoft Terminology"

        # Call the function to add a new note, with update_existing=False
        result = note_generation.add_note_to_trans_unit(
            self.trans_unit,
            new_note_text,
            from_attribute="BCXLFTranslator",
            update_existing=False
        )

        # Verify the note was added correctly
        self.assertTrue(result)

        # Check that there are now two notes
        notes = self.trans_unit.findall('.//{%s}note' % self.xliff_ns)
        self.assertEqual(len(notes), 2)

        # Both notes should have the 'from' attribute set to BCXLFTranslator
        bc_notes = [note for note in notes if note.get('from') == 'BCXLFTranslator']
        self.assertEqual(len(bc_notes), 2)
        note_texts = [note.text for note in bc_notes]
        self.assertIn("Source: Google Translate", note_texts)
        self.assertIn("Source: Microsoft Terminology", note_texts)

    def test_add_note_invalid_inputs(self):
        """Test handling of invalid inputs."""
        # Test with None trans_unit
        with pytest.raises(ValueError):
            note_generation.add_note_to_trans_unit(None, "Note text")

        # Test with empty note text
        result = note_generation.add_note_to_trans_unit(self.trans_unit, "")
        self.assertFalse(result)

        # Test with None note text
        result = note_generation.add_note_to_trans_unit(self.trans_unit, None)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()