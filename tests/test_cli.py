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
        with patch('bcxlftranslator.main.translate_with_retry') as mock_translate:
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

def test_extract_terminology_arg_parsing():
    """
    Given the CLI is run with --extract-terminology and a valid file path
    When the main function is called
    Then it should parse the argument and not raise
    """
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlf') as f:
        f.write('<xliff version="1.2"></xliff>')
        temp_input = f.name
    try:
        with patch('sys.argv', ['main.py', '--extract-terminology', temp_input, '--lang', 'da-DK']):
            try:
                main()
            except SystemExit as e:
                assert e.code == 0 or e.code is None
    finally:
        os.unlink(temp_input)


def test_extract_terminology_lang_parsing():
    """
    Given the CLI is run with --lang and valid language codes
    When the main function is called
    Then it should parse the language argument correctly
    """
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlf') as f:
        f.write('<xliff version="1.2"></xliff>')
        temp_input = f.name
    try:
        with patch('sys.argv', ['main.py', '--extract-terminology', temp_input, '--lang', 'fr-FR']):
            try:
                main()
            except SystemExit as e:
                assert e.code == 0 or e.code is None
    finally:
        os.unlink(temp_input)


def test_extract_terminology_optional_params():
    """
    Given the CLI is run with optional extraction parameters
    When the main function is called
    Then it should parse the options without error
    """
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlf') as f:
        f.write('<xliff version="1.2"></xliff>')
        temp_input = f.name
    try:
        with patch('sys.argv', ['main.py', '--extract-terminology', temp_input, '--lang', 'da-DK', '--filter', 'Table']):
            try:
                main()
            except SystemExit as e:
                assert e.code == 0 or e.code is None
    finally:
        os.unlink(temp_input)


def test_extract_terminology_missing_required():
    """
    Given the CLI is run with --extract-terminology but missing required --lang
    When the main function is called
    Then it should exit with an error
    """
    with patch('sys.argv', ['main.py', '--extract-terminology', 'input.xlf']):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0


def test_extract_terminology_help_contains_info(capsys):
    """
    Given the CLI is run with --help
    When the main function is called
    Then it should display help text including extract-terminology info
    """
    with patch('sys.argv', ['main.py', '--help']):
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert '--extract-terminology' in captured.out
        assert '--lang' in captured.out
        assert 'terminology' in captured.out.lower()


def test_use_terminology_flag_parsing():
    """
    Given the CLI is run with --use-terminology
    When the main function is called
    Then it should parse the flag without error
    """
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlf') as f:
        f.write('<xliff version="1.2"></xliff>')
        temp_input = f.name
    try:
        with patch('sys.argv', ['main.py', temp_input, 'out.xlf', '--use-terminology']):
            try:
                main()
            except SystemExit as e:
                # Should exit with success or normal translation exit
                assert e.code == 0 or e.code is None or e.code == 1
    finally:
        os.unlink(temp_input)


def test_terminology_db_path_parsing():
    """
    Given the CLI is run with --db and a path
    When the main function is called
    Then it should parse the db path argument without error
    """
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlf') as f:
        f.write('<xliff version="1.2"></xliff>')
        temp_input = f.name
    try:
        with patch('sys.argv', ['main.py', temp_input, 'out.xlf', '--use-terminology', '--db', 'test_terminology.db']):
            try:
                main()
            except SystemExit as e:
                assert e.code == 0 or e.code is None or e.code == 1
    finally:
        os.unlink(temp_input)


def test_terminology_feature_enable_disable():
    """
    Given the CLI is run with specific terminology feature enable/disable flags
    When the main function is called
    Then it should parse those feature parameters without error
    """
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlf') as f:
        f.write('<xliff version="1.2"></xliff>')
        temp_input = f.name
    try:
        with patch('sys.argv', ['main.py', temp_input, 'out.xlf', '--use-terminology', '--enable-term-matching', '--disable-term-highlighting']):
            try:
                main()
            except SystemExit as e:
                assert e.code == 0 or e.code is None or e.code == 1
    finally:
        os.unlink(temp_input)


def test_terminology_invalid_param_combinations():
    """
    Given the CLI is run with conflicting terminology parameters
    When the main function is called
    Then it should exit with an error
    """
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlf') as f:
        f.write('<xliff version="1.2"></xliff>')
        temp_input = f.name
    try:
        with patch('sys.argv', ['main.py', temp_input, 'out.xlf', '--use-terminology', '--enable-term-matching', '--disable-term-matching']):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code != 0
    finally:
        os.unlink(temp_input)


def test_help_includes_terminology_options(capsys):
    """
    Given the CLI is run with --help
    When the main function is called
    Then it should display help text including terminology options
    """
    with patch('sys.argv', ['main.py', '--help']):
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert '--use-terminology' in captured.out
        assert '--db' in captured.out or '--db-path' in captured.out
        assert 'terminology' in captured.out.lower()


def test_help_includes_terminology_basic_description(capsys):
    """
    Given the CLI is run with --help
    When the main function is called
    Then it should display help text including a basic description of the terminology feature
    """
    with patch('sys.argv', ['main.py', '--help']):
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert 'terminology' in captured.out.lower()
        assert 'business central' in captured.out.lower() or 'bc' in captured.out.lower()
        assert 'translation' in captured.out.lower()

def test_help_includes_terminology_command_parameters(capsys):
    """
    Given the CLI is run with --help
    When the main function is called
    Then it should display help text including all terminology command parameters
    """
    with patch('sys.argv', ['main.py', '--help']):
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        help_text = captured.out.lower()
        
        # Check for terminology-related parameters
        # Allow for variations in parameter names
        assert any(term in help_text for term in ['--use-terminology', '--terminology', '--use-term'])
        assert any(term in help_text for term in ['--db', '--db-path', '--terminology-db'])
        assert any(term in help_text for term in [
            '--enable-term-highlighting', '--highlight-terms', 
            '--term-highlighting', '--highlight-terminology'
        ])

def test_help_includes_terminology_examples(capsys):
    """
    Given the CLI is run with --help
    When the main function is called
    Then it should display help text including practical examples of terminology usage
    """
    with patch('sys.argv', ['main.py', '--help']):
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        help_text = captured.out.lower()
        
        # Check for examples in the help text
        assert 'example' in help_text
        
        # Check for terminology-related terms in the help text
        # Be flexible about the exact parameter names
        assert any(term in help_text for term in ['terminology', 'term', 'db'])

def test_help_includes_terminology_best_practices(capsys):
    """
    Given the CLI is run with --help
    When the main function is called
    Then it should display help text containing a best practices section for terminology
    """
    with patch('sys.argv', ['main.py', '--help']):
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert 'best practice' in captured.out.lower() or 'recommended' in captured.out.lower()

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
    Then help should be accessible and show terminology options in both cases
    """
    for help_flag in ['--help', '-h']:
        with patch('sys.argv', ['main.py', help_flag]):
            with pytest.raises(SystemExit):
                main()
            captured = capsys.readouterr()
            assert 'terminology' in captured.out.lower()