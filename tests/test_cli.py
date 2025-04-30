import pytest
import sys
import argparse
from unittest.mock import patch
from main import translate_xliff, main
import asyncio

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_cli_no_args():
    """Test CLI with no arguments"""
    with patch('sys.argv', ['main.py']):
        with pytest.raises(SystemExit):
            main()

def test_cli_help(capsys):
    """Test help output"""
    with patch('sys.argv', ['main.py', '--help']):
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert 'Translate XLIFF files' in captured.out
        assert 'input_file' in captured.out
        assert 'output_file' in captured.out

@pytest.mark.asyncio
async def test_progress_reporting(capsys):
    """Test that progress is reported correctly"""
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
        # Run translation
        await translate_xliff(temp_input, temp_output)

        # Capture output
        captured = capsys.readouterr()

        # Verify progress reporting
        assert "Processing file:" in captured.out
        assert "Progress:" in captured.out
        assert "Found 2 translation units" in captured.out
        assert "Translation process finished" in captured.out
        assert "Success rate:" in captured.out

    finally:
        # Cleanup
        os.unlink(temp_input)
        if os.path.exists(temp_output):
            os.unlink(temp_output)