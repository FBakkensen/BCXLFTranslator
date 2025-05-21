import pytest
import sys
import argparse
from unittest.mock import patch, Mock
from src.bcxlftranslator.main import translate_xliff, main
import asyncio

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_cli_no_args():
    """
    Given the CLI is run with no arguments
    When the main function is called
    Then it should exit with a SystemExit
    """
    with patch('sys.argv', ['main.py']):
        with pytest.raises(SystemExit):
            main()

def test_cli_help(capsys):
    """
    Given the CLI is run with the --help argument
    When the main function is called
    Then it should display help text including input_file and output_file options
    """
    with patch('sys.argv', ['main.py', '--help']):
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert 'Translate XLIFF files' in captured.out
        assert 'input_file' in captured.out
        assert 'output_file' in captured.out

@pytest.mark.asyncio
async def test_progress_reporting(capsys):
    """
    Given an XLIFF file with translation units
    When the translate_xliff function is called
    Then it should report progress information to stdout
    """
    input_content = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en-US" target-language="da-DK">
    <body>
      <trans-unit id="1">
        <source>Text 1</source>
        <target state="needs-translation"></target>
      </trans-unit>
      <trans-unit id="2">
        <source>Text 2</source>
        <target state="needs-translation"></target>
      </trans-unit>
    </body>
  </file>
</xliff>'''

    # Create temporary input file
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlf') as f:
        f.write(input_content)
        temp_input = f.name

    temp_output = temp_input + '.out.xlf'

    try:
        # Mock translate_with_retry to avoid actual translation calls
        with patch('src.bcxlftranslator.main.translate_with_retry') as mock_translate:
            # Setup mock translator for fallback
            mock_translate.return_value = Mock(text="Translated Text")

            # Run translation
            stats = await translate_xliff(temp_input, temp_output)

            # Verify stats were returned
            assert stats is not None

            # Capture output
            captured = capsys.readouterr()
            output_text = captured.out.lower()

            # Verify progress reporting - check for key information
            # We expect to see the number of units found
            assert "2" in output_text and ("units" in output_text or "trans-unit" in output_text)

            # We expect to see progress percentage
            assert any(percent in output_text for percent in ["50%", "100%"])

            # We expect to see a completion message
            assert any(msg.lower() in output_text for msg in [
                "complete",
                "finished",
                "done",
                "translated"
            ])

            # Verify the output file was created
            assert os.path.exists(temp_output)

    finally:
        # Cleanup
        os.unlink(temp_input)
        if os.path.exists(temp_output):
            os.unlink(temp_output)

def test_help_text_formatting_consistency(capsys):
    """
    Given the CLI is run with --help
    When the main function is called
    Then the help text formatting should be consistent and readable
    """
    with patch('sys.argv', ['main.py', '--help']):
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        # Check for consistent indentation and line breaks
        lines = captured.out.splitlines()
        assert any(line.startswith('  --') for line in lines)  # Indented options
        assert all(len(line) < 120 for line in lines if line.strip())  # No overly long lines

def test_help_accessible_from_multiple_invocations(capsys):
    """
    Given the CLI is run with -h and --help
    When the main function is called
    Then help should be accessible in both cases
    """
    for help_flag in ['--help', '-h']:
        with patch('sys.argv', ['main.py', help_flag]):
            with pytest.raises(SystemExit):
                main()
            captured = capsys.readouterr()
            # Ensure basic help output is present
            assert 'usage:' in captured.out.lower()
            assert 'translate xliff files' in captured.out.lower()