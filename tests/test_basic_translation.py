import os
import sys
import asyncio
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch, AsyncMock

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from bcxlftranslator.main import translate_xliff
from bcxlftranslator.statistics import StatisticsCollector

class TestBasicTranslation:
    """
    Tests for the basic translation functionality using Google Translate.
    """

    def test_translate_xliff_basic(self):
        """
        Test that the translate_xliff function works with a simple XLIFF file.
        """
        # Create a simple XLIFF file
        xliff_content = """<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file datatype="xml" source-language="en-US" target-language="fr-FR">
    <body>
      <trans-unit id="test1">
        <source>Hello World</source>
        <target></target>
      </trans-unit>
    </body>
  </file>
</xliff>
"""
        # Create temporary input and output files
        input_file = "test_input.xlf"
        output_file = "test_output.xlf"

        try:
            # Write the test XLIFF to the input file
            with open(input_file, "w", encoding="utf-8") as f:
                f.write(xliff_content)

            # Mock the translator to return a fixed translation
            mock_translator = AsyncMock()
            mock_result = Mock()
            mock_result.text = "Bonjour le monde"
            mock_translator.translate.return_value = mock_result
            mock_translator.__aenter__.return_value = mock_translator
            mock_translator.__aexit__.return_value = None

            # Patch the Translator class
            with patch('bcxlftranslator.main.Translator', return_value=mock_translator):
                # Run the translation
                stats = asyncio.run(translate_xliff(input_file, output_file))

                # Check that the output file was created
                assert os.path.exists(output_file)

                # Parse the output file
                tree = ET.parse(output_file)
                root = tree.getroot()

                # Find the trans-unit
                ns = {'x': 'urn:oasis:names:tc:xliff:document:1.2'}
                trans_unit = root.find('.//x:trans-unit', ns)
                target = trans_unit.find('./x:target', ns)

                # Check that the target was translated
                # The capitalization is affected by the match_case function
                assert target.text.lower() == "bonjour le monde"

                # Check that the statistics were updated
                assert stats.google_translate_count == 1
                assert stats.total_count == 1

        finally:
            # Clean up the temporary files
            if os.path.exists(input_file):
                os.remove(input_file)
            if os.path.exists(output_file):
                os.remove(output_file)
