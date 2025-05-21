"""
Tests for cross-drive file handling functionality.
"""
import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, Mock
import asyncio

# Import the functions to test
from bcxlftranslator.main import (
    translate_xliff, 
    are_on_different_drives, 
    copy_file_contents
)

# Sample XLIFF content for testing
SAMPLE_XLIFF = """<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="urn:oasis:names:tc:xliff:document:1.2 xliff-core-1.2-transitional.xsd">
  <file datatype="xml" source-language="en-US" target-language="da-dk" original="Test File">
    <body>
      <group id="body">
        <trans-unit id="test1" size-unit="char" translate="yes" xml:space="preserve">
          <source>Hello World</source>
          <target state="needs-translation"/>
          <note from="Developer" annotates="general" priority="2"/>
        </trans-unit>
      </group>
    </body>
  </file>
</xliff>"""

def test_are_on_different_drives():
    """
    Test the are_on_different_drives function.
    """
    # Test with same drive on Windows
    if os.name == 'nt':  # Windows
        assert not are_on_different_drives('C:\\path\\to\\file1', 'C:\\different\\path\\file2')
        assert are_on_different_drives('C:\\path\\to\\file1', 'D:\\path\\to\\file2')
    else:  # Unix-like
        # On Unix, we always return False for now
        assert not are_on_different_drives('/path/to/file1', '/different/path/file2')

def test_copy_file_contents():
    """
    Test the copy_file_contents function.
    """
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        source_file = os.path.join(temp_dir, 'source.txt')
        dest_file = os.path.join(temp_dir, 'dest.txt')
        
        # Write content to source file
        test_content = "This is test content for copy_file_contents"
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Copy the file contents
        result = copy_file_contents(source_file, dest_file)
        
        # Verify the result
        assert result is True
        
        # Verify the destination file has the correct content
        with open(dest_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert content == test_content

@pytest.mark.asyncio
async def test_translate_xliff_with_temp_dir():
    """
    Test that translate_xliff works correctly with a custom temporary directory.
    """
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_file = os.path.join(temp_dir, 'test_custom_temp.xlf')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(SAMPLE_XLIFF)
        
        # Create a custom temporary directory
        custom_temp_dir = os.path.join(temp_dir, 'custom_temp')
        os.makedirs(custom_temp_dir, exist_ok=True)
        
        # Mock the translation function to return a consistent result
        with patch('bcxlftranslator.main.translate_with_retry') as mock_translate:
            mock_translate.return_value = Mock(text="Hej Verden")
            
            # Run in-place translation with custom temp directory
            stats = await translate_xliff(test_file, test_file, temp_dir=custom_temp_dir)
            
            # Verify that the translation was successful
            assert stats is not None
            assert stats.total_count > 0
            
            # Verify that the file was modified
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Hej Verden" in content
                assert "<target state=\"translated\">Hej Verden</target>" in content
            
            # Verify no temporary files are left in the custom directory
            assert len(os.listdir(custom_temp_dir)) == 0

@pytest.mark.asyncio
async def test_cross_drive_simulation():
    """
    Test the cross-drive handling by simulating a cross-drive scenario.
    """
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_file = os.path.join(temp_dir, 'test_cross_drive.xlf')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(SAMPLE_XLIFF)
        
        # Mock the are_on_different_drives function to simulate cross-drive scenario
        with patch('bcxlftranslator.main.are_on_different_drives') as mock_different_drives:
            mock_different_drives.return_value = True
            
            # Mock the copy_file_contents function to verify it's called
            with patch('bcxlftranslator.main.copy_file_contents') as mock_copy:
                mock_copy.return_value = True
                
                # Mock the translation function to return a consistent result
                with patch('bcxlftranslator.main.translate_with_retry') as mock_translate:
                    mock_translate.return_value = Mock(text="Hej Verden")
                    
                    # Run in-place translation
                    stats = await translate_xliff(test_file, test_file)
                    
                    # Verify that the translation was successful
                    assert stats is not None
                    assert stats.total_count > 0
                    
                    # Verify that copy_file_contents was called instead of os.replace
                    mock_copy.assert_called_once()
