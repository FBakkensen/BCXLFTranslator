import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os
from xml.etree import ElementTree as ET

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
    with pytest.raises(ET.ParseError):  # Use a more specific exception if available
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


def test_extracted_terms_are_stored_in_database(tmp_path):
    """
    Given a valid XLIFF file and a terminology database
    When the extraction command is invoked
    Then the extracted terms should be stored in the database with correct metadata
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

    db_path = tmp_path / "terminology.db"
    # Patch the TerminologyDatabase class in the correct module
    with patch("src.bcxlftranslator.terminology_db.TerminologyDatabase") as mock_db_class:
        mock_instance = mock_db_class.return_value
        result = main.extract_terminology_command(str(xliff_file), lang="da-DK", db_path=str(db_path))
        # Check that the database's store_terms method was called with expected data
        assert mock_instance.store_terms.called
        # Optionally, check the call arguments for correct metadata
        called_args, called_kwargs = mock_instance.store_terms.call_args
        assert any("Customer" in str(arg) and "Kunde" in str(arg) for arg in called_args)
        # Ensure result indicates success
        assert result.success


def test_end_to_end_extraction_workflow(tmp_path):
    """
    Given a valid XLIFF file and database
    When the extraction command is invoked end-to-end
    Then it should parse, store, and report extracted terms successfully
    """
    xliff_content = '''<?xml version="1.0" encoding="utf-8"?>\n<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2"><file source-language="en-US" target-language="da-DK"><body><trans-unit id="1"><source>Customer</source><target>Kunde</target></trans-unit></body></file></xliff>'''
    xliff_file = tmp_path / "input.xlf"
    xliff_file.write_text(xliff_content, encoding="utf-8")
    db_path = tmp_path / "terms.db"
    with patch("src.bcxlftranslator.terminology_db.TerminologyDatabase") as mock_db_class, \
         patch("src.bcxlftranslator.main.report_extraction_results") as mock_report:
        mock_instance = mock_db_class.return_value
        result = main.extract_terminology_command(str(xliff_file), lang="da-DK", db_path=str(db_path))
        assert result.success
        assert mock_instance.store_terms.called
        mock_report.assert_called()


def test_extraction_advanced_options(tmp_path):
    """
    Given a valid XLIFF file
    When the extraction command is invoked with advanced filtering and overwrite options
    Then it should respect the filter and overwrite parameters
    """
    xliff_content = '''<?xml version="1.0" encoding="utf-8"?>\n<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2"><file source-language="en-US" target-language="da-DK"><body><trans-unit id="table1"><source>Customer</source><target>Kunde</target></trans-unit><trans-unit id="page1"><source>Home</source><target>Hjem</target></trans-unit></body></file></xliff>'''
    xliff_file = tmp_path / "input.xlf"
    xliff_file.write_text(xliff_content, encoding="utf-8")
    db_path = tmp_path / "terms.db"
    with patch("src.bcxlftranslator.terminology_db.TerminologyDatabase") as mock_db_class:
        mock_instance = mock_db_class.return_value
        main.extract_terminology_command(str(xliff_file), lang="da-DK", db_path=str(db_path), filter_type="Table", overwrite=True)
        # Should only store filtered terms and overwrite existing
        assert mock_instance.store_terms.called
        called_args, called_kwargs = mock_instance.store_terms.call_args
        assert any("Customer" in str(arg) for arg in called_args)


def test_extraction_exit_codes(tmp_path):
    """
    Given various extraction scenarios
    When the extraction command is invoked
    Then it should return correct exit codes for success, warnings, and errors
    """
    xliff_content = '''<?xml version="1.0" encoding="utf-8"?>\n<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2"><file source-language="en-US" target-language="da-DK"><body><trans-unit id="1"><source>Customer</source><target>Kunde</target></trans-unit></body></file></xliff>'''
    xliff_file = tmp_path / "input.xlf"
    xliff_file.write_text(xliff_content, encoding="utf-8")
    with patch("src.bcxlftranslator.main.report_extraction_results"):
        # Success - should have exit_code=0 when terms are extracted
        result = main.extract_terminology_command(str(xliff_file), lang="da-DK")
        assert result.exit_code == 0
    # Error case: missing file
    with pytest.raises(FileNotFoundError):
        main.extract_terminology_command("doesnotexist.xlf", lang="da-DK")
    # Simulate warning (e.g., no terms extracted)
    empty_xliff = '''<?xml version="1.0" encoding="utf-8"?>\n<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2"><file source-language="en-US" target-language="da-DK"><body></body></file></xliff>'''
    empty_file = tmp_path / "empty.xlf"
    empty_file.write_text(empty_xliff, encoding="utf-8")
    result = main.extract_terminology_command(str(empty_file), lang="da-DK")
    assert result.exit_code == 1  # convention: 1 for warning (no terms)


def test_extraction_error_feedback(tmp_path):
    """
    Given invalid input, file errors, and DB errors
    When the extraction command is invoked
    Then it should provide clear error feedback
    """
    # Invalid file
    with pytest.raises(FileNotFoundError):
        main.extract_terminology_command("nofile.xlf", lang="da-DK")
    # Malformed XLIFF
    bad_file = tmp_path / "bad.xlf"
    bad_file.write_text("<xliff><file></xliff", encoding="utf-8")
    with pytest.raises(ET.ParseError):
        main.extract_terminology_command(str(bad_file), lang="da-DK")
    # DB error - use a more direct approach to ensure exception is raised
    xliff_content = '''<?xml version="1.0" encoding="utf-8"?>\n<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2"><file source-language="en-US" target-language="da-DK"><body><trans-unit id="1"><source>Customer</source><target>Kunde</target></trans-unit></body></file></xliff>'''
    xliff_file = tmp_path / "input.xlf"
    xliff_file.write_text(xliff_content, encoding="utf-8")
    
    # Create a mock that will raise an exception when store_terms is called
    mock_db = MagicMock()
    mock_db.store_terms.side_effect = Exception("DB error")
    
    with patch("src.bcxlftranslator.terminology_db.TerminologyDatabase", return_value=mock_db):
        with pytest.raises(Exception):
            main.extract_terminology_command(str(xliff_file), lang="da-DK", db_path="test.db")


def test_extraction_comprehensive_error_handling(tmp_path):
    """
    Given various failure scenarios
    When the extraction command is invoked
    Then it should handle errors gracefully and not crash
    """
    # Simulate DB error
    xliff_content = '''<?xml version="1.0" encoding="utf-8"?>\n<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2"><file source-language="en-US" target-language="da-DK"><body><trans-unit id="1"><source>Customer</source><target>Kunde</target></trans-unit></body></file></xliff>'''
    xliff_file = tmp_path / "input.xlf"
    xliff_file.write_text(xliff_content, encoding="utf-8")
    
    # Create a mock that will raise an exception when store_terms is called
    mock_db = MagicMock()
    mock_db.store_terms.side_effect = Exception("DB error")
    
    with patch("src.bcxlftranslator.terminology_db.TerminologyDatabase", return_value=mock_db):
        with pytest.raises(Exception):
            main.extract_terminology_command(str(xliff_file), lang="da-DK", db_path="test.db")
            
    # Simulate parser error using a patched parse_xliff that raises an exception
    parse_xliff_mock = MagicMock(side_effect=ET.ParseError("Parse error"))
    parse_xliff_mock.is_stub = False  # Mark as not a stub so it will be used
    
    with patch("src.bcxlftranslator.main.parse_xliff", parse_xliff_mock):
        with pytest.raises(ET.ParseError):
            main.extract_terminology_command(str(xliff_file), lang="da-DK")


def test_extraction_verbose_and_quiet_modes(tmp_path, capsys):
    """
    Given a valid XLIFF file
    When the extraction command is invoked with verbose and quiet modes
    Then verbose mode provides detailed output and quiet mode suppresses output
    """
    xliff_content = '''<?xml version="1.0" encoding="utf-8"?>\n<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2"><file source-language="en-US" target-language="da-DK"><body><trans-unit id="1"><source>Customer</source><target>Kunde</target></trans-unit></body></file></xliff>'''
    xliff_file = tmp_path / "input.xlf"
    xliff_file.write_text(xliff_content, encoding="utf-8")
    # Verbose mode
    main.extract_terminology_command(str(xliff_file), lang="da-DK", verbose=True)
    out = capsys.readouterr().out
    assert "Extracted" in out or "Customer" in out
    # Quiet mode
    main.extract_terminology_command(str(xliff_file), lang="da-DK", quiet=True)
    out = capsys.readouterr().out
    assert out.strip() == ""
