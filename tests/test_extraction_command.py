import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os

# Assume the extraction command is exposed as extract_terminology_command in main.py for testability
from src.bcxlftranslator import main


def test_extract_from_valid_xliff(tmp_path):
    """
    Given a valid reference XLIFF file
    When the extraction command is invoked
    Then it should extract terminology and report the correct count
    """
    xliff_content = '''<?xml version="1.0" encoding="utf-8"?>
    <xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
      <file source-language="en-US" target-language="da-DK">
        <body>
          <trans-unit id="1">
            <source>Customer</source>
            <target>Kunde</target>
          </trans-unit>
        </body>
      </file>
    </xliff>'''
    xliff_file = tmp_path / "input.xlf"
    xliff_file.write_text(xliff_content, encoding="utf-8")

    # Patch reporting to capture output
    with patch("src.bcxlftranslator.main.report_extraction_results") as mock_report:
        result = main.extract_terminology_command(str(xliff_file), lang="da-DK")
        assert result.success
        mock_report.assert_called()
        assert result.count_extracted == 1


def test_extract_missing_file():
    """
    Given a missing XLIFF file
    When the extraction command is invoked
    Then it should report an appropriate error
    """
    with pytest.raises(FileNotFoundError):
        main.extract_terminology_command("nonexistent.xlf", lang="da-DK")


def test_extract_malformed_xliff(tmp_path):
    """
    Given a malformed XLIFF file
    When the extraction command is invoked
    Then it should report a parse error
    """
    malformed = "<xliff><file></xliff"  # Invalid XML
    bad_file = tmp_path / "bad.xlf"
    bad_file.write_text(malformed, encoding="utf-8")
    with pytest.raises(Exception):  # Use a more specific exception if available
        main.extract_terminology_command(str(bad_file), lang="da-DK")


def test_extract_reports_term_count(tmp_path):
    """
    Given a valid XLIFF file with multiple terms
    When the extraction command is invoked
    Then it should report the correct number of terms extracted
    """
    xliff_content = '''<?xml version="1.0" encoding="utf-8"?>
    <xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
      <file source-language="en-US" target-language="da-DK">
        <body>
          <trans-unit id="1">
            <source>Customer</source>
            <target>Kunde</target>
          </trans-unit>
          <trans-unit id="2">
            <source>Vendor</source>
            <target>Leverandør</target>
          </trans-unit>
        </body>
      </file>
    </xliff>'''
    xliff_file = tmp_path / "input.xlf"
    xliff_file.write_text(xliff_content, encoding="utf-8")
    with patch("src.bcxlftranslator.main.report_extraction_results") as mock_report:
        result = main.extract_terminology_command(str(xliff_file), lang="da-DK")
        assert result.count_extracted == 2
        mock_report.assert_called()


def test_extract_with_filtering(tmp_path):
    """
    Given a valid XLIFF file with various object types
    When the extraction command is invoked with a filter
    Then it should extract only matching terms
    """
    xliff_content = '''<?xml version="1.0" encoding="utf-8"?>
    <xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
      <file source-language="en-US" target-language="da-DK">
        <body>
          <trans-unit id="table1">
            <source>Customer</source>
            <target>Kunde</target>
          </trans-unit>
          <trans-unit id="page1">
            <source>Home</source>
            <target>Hjem</target>
          </trans-unit>
        </body>
      </file>
    </xliff>'''
    xliff_file = tmp_path / "input.xlf"
    xliff_file.write_text(xliff_content, encoding="utf-8")
    with patch("src.bcxlftranslator.main.report_extraction_results") as mock_report:
        result = main.extract_terminology_command(str(xliff_file), lang="da-DK", filter_type="Table")
        assert result.count_extracted == 1
        mock_report.assert_called()


def test_extract_progress_reporting(tmp_path):
    """
    Given a large XLIFF file
    When the extraction command is invoked
    Then it should report progress during extraction
    """
    units = "".join([
        f'<trans-unit id="{i}"><source>Term{i}</source><target>Term{i}Target</target></trans-unit>'
        for i in range(100)
    ])
    xliff_content = f'''<?xml version="1.0" encoding="utf-8"?>
    <xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
      <file source-language="en-US" target-language="da-DK">
        <body>{units}</body>
      </file>
    </xliff>'''
    xliff_file = tmp_path / "input.xlf"
    xliff_file.write_text(xliff_content, encoding="utf-8")
    with patch("src.bcxlftranslator.main.report_progress") as mock_progress:
        main.extract_terminology_command(str(xliff_file), lang="da-DK")
        assert mock_progress.called
