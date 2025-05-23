# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import argparse
import time
import sys
from googletrans import Translator, LANGUAGES
import os # Added for path checking
import asyncio
import aiohttp
import copy
import tempfile # Added for temporary file creation
import shutil # Added for file backup
import atexit # Added for cleanup on exit

# Import the XLIFF parser functions for header/footer preservation
try:
    # Try relative import first
    from .xliff_parser import extract_header_footer, extract_trans_units_from_file, trans_units_to_text, preserve_indentation
    from .exceptions import InvalidXliffError, EmptyXliffError, MalformedXliffError, NoTransUnitsError
except ImportError:
    # Fall back to absolute import (when installed as package)
    from bcxlftranslator.xliff_parser import extract_header_footer, extract_trans_units_from_file, trans_units_to_text, preserve_indentation
    from bcxlftranslator.exceptions import InvalidXliffError, EmptyXliffError, MalformedXliffError, NoTransUnitsError

# Global registry to track temporary files for cleanup
_temp_files = set()
_backup_files = set()

def are_on_different_drives(path1, path2):
    """
    Check if two file paths are on different drives (Windows) or filesystems (Unix).

    Args:
        path1 (str): First file path
        path2 (str): Second file path

    Returns:
        bool: True if the paths are on different drives/filesystems, False otherwise
    """
    if os.name == 'nt':  # Windows
        # Extract drive letters (e.g., 'C:' from 'C:\path\to\file')
        drive1 = os.path.splitdrive(os.path.abspath(path1))[0].upper()
        drive2 = os.path.splitdrive(os.path.abspath(path2))[0].upper()
        return drive1 != drive2
    else:  # Unix-like systems
        # For Unix, we'll consider them on the same filesystem
        # A more accurate check would use os.stat().st_dev, but that's not needed for now
        return False

def copy_file_contents(src, dst):
    """
    Copy file contents from source to destination.

    Args:
        src (str): Source file path
        dst (str): Destination file path

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(src, 'rb') as src_file:
            with open(dst, 'wb') as dst_file:
                # Copy in chunks to handle large files efficiently
                shutil.copyfileobj(src_file, dst_file)
        return True
    except Exception as e:
        print(f"Error copying file contents: {e}")
        return False

def register_temp_file(file_path):
    """Register a temporary file for cleanup"""
    if file_path and os.path.exists(file_path):
        _temp_files.add(file_path)

def register_backup_file(file_path):
    """Register a backup file for cleanup"""
    if file_path and os.path.exists(file_path):
        _backup_files.add(file_path)

def unregister_temp_file(file_path):
    """Unregister a temporary file from cleanup"""
    if file_path and file_path in _temp_files:
        _temp_files.remove(file_path)

def unregister_backup_file(file_path):
    """Unregister a backup file from cleanup"""
    if file_path and file_path in _backup_files:
        _backup_files.remove(file_path)

def cleanup_registered_files():
    """Clean up all registered temporary and backup files"""
    # Clean up temporary files
    temp_files_to_remove = _temp_files.copy()
    for file_path in temp_files_to_remove:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up temporary file: {file_path}")
                _temp_files.remove(file_path)
        except Exception as e:
            print(f"Warning: Could not remove temporary file {file_path}: {e}")

    # Clean up backup files
    backup_files_to_remove = _backup_files.copy()
    for file_path in backup_files_to_remove:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up backup file: {file_path}")
                _backup_files.remove(file_path)
        except Exception as e:
            print(f"Warning: Could not remove backup file {file_path}: {e}")

# Register cleanup function to run on exit
atexit.register(cleanup_registered_files)

# --- Configuration ---
DELAY_BETWEEN_REQUESTS = 0.5  # increased from 1.0 to 2.0 seconds to reduce rate limiting
MAX_RETRIES = 3
RETRY_DELAY = 3.0  # increased from 2.0 to 3.0 seconds

def match_case(source, translated):
    """Match the capitalization pattern of the source text in the translated text"""
    if not source or not translated:
        return translated

    # Handle comma-separated lists
    if ',' in source:
        source_parts = []
        current_pos = 0

        # First, collect all parts with their preceding spaces and the parts themselves
        while current_pos < len(source):
            # Find next comma
            next_comma = source.find(',', current_pos)
            if (next_comma == -1):
                # No more commas, take the rest of the string
                source_parts.append(source[current_pos:])
                break
            else:
                source_parts.append(source[current_pos:next_comma])
                current_pos = next_comma + 1

        translated_parts = [p.strip() for p in translated.split(',')]
        if len(source_parts) == len(translated_parts):
            # Match each part
            result = ''
            for i, (original_part, translated_part) in enumerate(zip(source_parts, translated_parts)):
                if i > 0:
                    result += ','
                leading_spaces = len(original_part) - len(original_part.lstrip())
                trailing_spaces = len(original_part) - len(original_part.rstrip())
                result += ' ' * leading_spaces
                result += match_single_text(original_part.strip(), translated_part)
                result += ' ' * trailing_spaces
            return result
        else:
            # Fallback: simple sentence case (capitalize only first letter, rest lower)
            if not translated:
                return translated
            return translated[0].upper() + translated[1:]
    return match_single_text(source, translated)

def match_single_text(source, translated):
    """Match the capitalization pattern of a single text string, including title case and dotted words"""
    if not source or not translated:
        return translated

    # If source is all uppercase, convert translated to uppercase
    if source.isupper():
        return translated.upper()

    # If source is all lowercase, convert translated to lowercase
    if source.islower():
        return translated.lower()

    import re

    # Helper function to detect if a word is a common preposition, article, etc.
    def is_lowercase_word(word):
        lowercase_words = {'on', 'in', 'at', 'by', 'for', 'with', 'a', 'an', 'the',
                          'and', 'but', 'or', 'nor', 'to', 'of'}
        return word.lower() in lowercase_words

    # Split the source and translated text into words and handle dotted words
    def split_with_dots(text):
        # First split by spaces
        space_parts = text.split()
        result = []

        for part in space_parts:
            # For each word, check if it contains dots
            if '.' in part:
                # Process dotted word
                dot_segments = part.split('.')
                processed_segments = []

                for segment in dot_segments:
                    processed_segments.append(segment)

                result.append({
                    'type': 'dotted',
                    'segments': processed_segments,
                    'original': part
                })
            else:
                # Regular word
                result.append({
                    'type': 'regular',
                    'word': part,
                    'is_lowercase_word': is_lowercase_word(part)
                })

        return result

    # Process source and translated text
    source_parts = split_with_dots(source)
    translated_parts = split_with_dots(translated)

    # Build result based on capitalization patterns
    result_words = []

    # Apply capitalization rules for each word in translated text
    for i, trans_part in enumerate(translated_parts):
        if trans_part['type'] == 'regular':
            word = trans_part['word']
            # Default capitalization (just capitalize first word)
            if i == 0 and source and source[0].isupper():
                result_words.append(word[0].upper() + word[1:])
            # Keep prepositions lowercase in middle of phrase when source does the same
            elif trans_part['is_lowercase_word'] and i > 0:
                result_words.append(word.lower())
            # For other words, apply source capitalization pattern if available
            elif i < len(source_parts) and source_parts[i]['type'] == 'regular':
                # Match capitalization of corresponding source word
                src_word = source_parts[i]['word']
                if src_word[0].isupper():
                    result_words.append(word[0].upper() + word[1:])
                else:
                    result_words.append(word)
            else:
                # Default to keeping original
                result_words.append(word)
        else:  # dotted word
            # Handle dotted words like "Prod.Order"
            segments = trans_part['segments']
            processed_segments = []

            # Apply capitalization to each segment of the dotted word
            for j, segment in enumerate(segments):
                # Find a matching dotted word in source to use its capitalization
                matching_source_part = None
                for src_part in source_parts:
                    if src_part['type'] == 'dotted':
                        matching_source_part = src_part
                        break

                if matching_source_part:
                    # Apply capitalization from source's dotted segments
                    src_segments = matching_source_part['segments']
                    if j < len(src_segments) and src_segments[j] and src_segments[j][0].isupper():
                        processed_segments.append(segment[0].upper() + segment[1:] if segment else '')
                    else:
                        processed_segments.append(segment)
                else:
                    # Default: capitalize first letter of each segment
                    processed_segments.append(segment[0].upper() + segment[1:] if segment and segment[0].isalpha() else segment)

            # Combine segments back with dots
            result_words.append('.'.join(processed_segments))

    return ' '.join(result_words)

# --- Important Notes ---
# 1. Installation: You need to install the googletrans library:
#    pip install googletrans==4.0.2
#
# 2. Reliability Warning: This script uses the googletrans library
#    that interacts with Google Translate. While more stable than
#    previous versions, it may still have limitations.
#
# 3. Rate Limiting: Making too many requests too quickly might get your IP
#    temporarily blocked by Google Translate. The DELAY_BETWEEN_REQUESTS
#    setting attempts to mitigate this, but may need adjustment.
#
# 4. Caching: This version caches translations for identical source texts within
#    a single run to ensure consistency and reduce API calls.
#
# 5. Alternatives: For reliable, supported translation, consider using the
#    official Google Cloud Translation API (which has costs) or other
#    translation services/APIs.
# ---

async def translate_with_retry(translator, text, dest_lang, src_lang, retries=0):
    """
    Helper function to handle translation with retries

    Args:
        translator: The translator instance to use
        text: The text to translate
        dest_lang: The destination language code
        src_lang: The source language code
        retries: The current retry count

    Returns:
        An object with a text attribute containing the translated text, or None if translation failed
    """
    try:
        result = await translator.translate(text, dest=dest_lang, src=src_lang)
        if result and hasattr(result, 'text') and result.text:
            # Return the result object directly, which has a text attribute
            return result
        else:
            # If we got a string or other non-object result, wrap it in a Mock with a text attribute
            from unittest.mock import Mock
            if result and isinstance(result, str):
                mock_result = Mock()
                mock_result.text = result
                return mock_result
            # If we got None or an invalid result, return None
            return None
    except Exception as e:
        if retries < MAX_RETRIES:
            print(f"    -> Translation failed, retrying in {RETRY_DELAY} seconds... (Attempt {retries + 1}/{MAX_RETRIES})")
            await asyncio.sleep(RETRY_DELAY)
            return await translate_with_retry(translator, text, dest_lang, src_lang, retries + 1)
        else:
            print(f"    -> Error translating after {MAX_RETRIES} retries: {str(e)}")
            return None

def escape_xml(text):
    """Escape XML special characters in text"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

def copy_attributes(elem, ns):
    """Copy all attributes including XML namespace attributes to a new dict"""
    attrs = elem.attrib.copy()
    # Handle xml namespace attributes explicitly
    xml_attrs = {k: v for k, v in elem.items() if k.startswith('xml:')}
    attrs.update(xml_attrs)
    return attrs

def strip_namespace(elem):
    elem.tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
    # Remove namespace from attributes, but preserve xml:space
    new_attrib = {}
    for k, v in elem.attrib.items():
        if k == '{http://www.w3.org/XML/1998/namespace}space':
            new_attrib[k] = v  # Preserve xml:space
        else:
            new_attrib[k.split('}')[-1] if '}' in k else k] = v
    elem.attrib = new_attrib
    for child in elem:
        strip_namespace(child)

def remove_specific_notes(trans_unit, ns):
    """
    Remove note elements with from="NAB AL Tool Refresh Xlf" from a trans-unit.

    Args:
        trans_unit (ET.Element): The trans-unit element to process
        ns (str): The namespace prefix to use for finding elements

    Returns:
        bool: True if any notes were removed, False otherwise
    """
    if trans_unit is None:
        return False

    # Find all note elements
    notes_to_remove = []
    for child in trans_unit:
        # Check if this is a note element with the specific 'from' attribute
        if child.tag.endswith('note') and child.get('from') == "NAB AL Tool Refresh Xlf":
            notes_to_remove.append(child)

    # Remove the identified notes
    for note in notes_to_remove:
        trans_unit.remove(note)

    return len(notes_to_remove) > 0

async def translate_xliff(input_file, output_file, add_attribution=True, temp_dir=None):
    """
    Main translation function - googletrans 4.0.2 version using async context manager
    with header/footer preservation approach

    Args:
        input_file (str): Path to the input XLIFF file
        output_file (str): Path to save the translated XLIFF file. If same as input_file,
                          performs in-place translation using a temporary file.
        add_attribution (bool): Whether to add attribution notes to translation units
        temp_dir (str, optional): Custom temporary directory to use for in-place translation.
                                 If provided, must be on the same drive as the input file.

    Returns:
        StatisticsCollector or None: Statistics object if successful, None if failed
    """
    # Initialize statistics collector
    try:
        # Try relative import first
        from .statistics import StatisticsCollector
    except ImportError:
        # Fall back to absolute import (when installed as package)
        from bcxlftranslator.statistics import StatisticsCollector
    stats_collector = StatisticsCollector()

    # Check if in-place translation is requested (input_file == output_file)
    is_inplace = input_file == output_file
    temp_file = None
    actual_output_file = output_file

    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' not found.")
            return stats_collector  # Return empty stats instead of None

        # If in-place translation, create a temporary file
        if is_inplace:
            # If a custom temporary directory is provided, use it
            if temp_dir and os.path.isdir(temp_dir):
                # Create a temporary file in the specified directory
                file_ext = os.path.splitext(input_file)[1]
                temp_file = os.path.join(temp_dir, f"bcxlf_temp_{int(time.time())}{file_ext}")
                with open(temp_file, 'w') as f:
                    pass  # Create an empty file
                print(f"Using custom temporary directory: {temp_dir}")
            else:
                # Create a temporary file with the same extension as the input file
                fd, temp_file = tempfile.mkstemp(suffix=os.path.splitext(input_file)[1])
                os.close(fd)  # Close the file descriptor

            actual_output_file = temp_file
            # Register the temporary file for cleanup
            register_temp_file(temp_file)
            print(f"In-place translation requested. Using temporary file: {temp_file}")

            # Check if the temporary file is on the same drive as the input file
            if are_on_different_drives(temp_file, input_file):
                print("Warning: Temporary file is on a different drive than the input file.")
                print("This may cause issues when replacing the original file.")
                print("Consider using --temp-dir option to specify a temporary directory on the same drive.")

        # Create output directory if it doesn't exist (only for non-in-place translation)
        if not is_inplace:
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

        # Step 1: Extract header and footer from the input file
        print(f"Extracting header and footer from {input_file}")
        header, footer = extract_header_footer(input_file)
        print("Header and footer extracted successfully.")

        # Step 2: Extract indentation patterns from the input file
        print("Extracting indentation patterns")
        indentation_patterns = preserve_indentation(input_file)
        print("Indentation patterns extracted successfully.")

        # Step 3: Extract trans-units for processing
        print("Extracting trans-units for processing")
        trans_units = extract_trans_units_from_file(input_file)
        total_units = len(trans_units)
        print(f"Found {total_units} translation units.")

        # Parse the XLIFF file to get language information
        tree = ET.parse(input_file)
        root = tree.getroot()

        # Get the namespace if present
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # Find the target language
        file_elem = root.find(f"{ns}file")
        if file_elem is None:
            print(f"Error: No file element found in XLIFF. Root tag: {root.tag}, Namespace used: '{ns}'")
            print("Children tags:", [child.tag for child in root])
            return stats_collector  # Return empty stats instead of None

        target_lang = file_elem.get("target-language", "")
        source_lang = file_elem.get("source-language", "en")

        # Convert language codes to format expected by Google Translate
        # XLIFF uses codes like 'en-US', Google Translate uses 'en'
        target_lang_code = target_lang.split("-")[0] if target_lang else "da"  # Default to Danish if not specified
        source_lang_code = source_lang.split("-")[0] if source_lang else "en"  # Default to English if not specified

        # Check if target language is supported
        if target_lang_code not in LANGUAGES:
            print(f"Warning: Target language '{target_lang_code}' not in supported languages list. Trying anyway...")

        # Translation cache to avoid re-translating the same text
        translation_cache = {}

        # Step 3: Process the trans-units
        print("Processing trans-units...")
        # Create a translator instance using async context manager
        async with Translator() as translator:
            # Process each translation unit
            for i, trans_unit in enumerate(trans_units):
                # Report progress
                report_progress(i, total_units)

                # Get source and target elements
                source_elem = trans_unit.find(f"{ns}source")
                target_elem = trans_unit.find(f"{ns}target")

                if source_elem is not None and target_elem is not None:
                    source_text = source_elem.text or ""
                    target_text = target_elem.text or ""

                    # Skip empty source text
                    if not source_text.strip():
                        continue

                    # Skip if target already has content
                    if target_text.strip():
                        continue

                    # Translate using Google Translate
                    target_text = None
                    # Check if we've already translated this text
                    if source_text in translation_cache:
                        target_text = translation_cache[source_text]
                    else:
                        try:
                            # Translate the text
                            result = await translate_with_retry(translator, source_text, target_lang_code, source_lang_code)
                            if result is None:
                                print(f"Warning: Translation failed for '{source_text}': No result returned")
                                # Skip this unit rather than exiting
                                continue
                            target_text = result.text

                            # Cache the translation
                            translation_cache[source_text] = target_text
                        except Exception as e:
                            print(f"Warning: Translation failed for '{source_text}': {e}")
                            # Skip this unit rather than exiting
                            continue

                    # Skip if translation failed
                    if target_text is None:
                        print(f"Warning: No translation result for '{source_text}'")
                        continue

                    # Track Google Translate usage in statistics
                    stats_collector.track_translation("Google Translate",
                                                   source_text=source_text,
                                                   target_text=target_text)

                    # Apply case matching to the translated text
                    target_text = match_case(source_text, target_text)

                    # Update the target element
                    target_elem.text = target_text
                    target_elem.set("state", "translated")

                    # Remove specific notes with from="NAB AL Tool Refresh Xlf"
                    remove_specific_notes(trans_unit, ns)

                    # Add attribution note if requested
                    if add_attribution:
                        try:
                            # Try relative import first
                            from .note_generation import add_note_to_trans_unit, generate_attribution_note
                        except ImportError:
                            # Fall back to absolute import (when installed as package)
                            from bcxlftranslator.note_generation import add_note_to_trans_unit, generate_attribution_note

                        # Generate and add the note
                        note_text = generate_attribution_note("GOOGLE")
                        add_note_to_trans_unit(trans_unit, note_text)

        # Report final progress
        report_progress(total_units, total_units)
        print("\nTranslation complete.")

        # Step 4: Convert processed trans-units back to text with preserved indentation
        print("Converting processed trans-units back to text with preserved indentation")
        trans_units_text = trans_units_to_text(trans_units, indentation_patterns=indentation_patterns)

        # Fix any inconsistent indentation in the first trans-unit
        # This ensures all trans-units have exactly the same indentation
        lines = trans_units_text.splitlines()
        if lines and '<trans-unit' in lines[0]:
            # Find the first line with a trans-unit
            first_trans_unit_line = lines[0]
            # Count the leading spaces
            leading_spaces = len(first_trans_unit_line) - len(first_trans_unit_line.lstrip())

            # If the indentation is not the standard 8 spaces, fix it
            if leading_spaces != 8:
                # Replace the indentation with exactly 8 spaces
                lines[0] = ' ' * 8 + first_trans_unit_line.lstrip()
                # Rejoin the lines
                trans_units_text = '\n'.join(lines)

        print("Trans-units converted successfully.")

        # Calculate statistics before writing to file
        stats = stats_collector.get_statistics()

        # Step 5: Combine header, processed trans-units, and footer to create the output file
        print(f"Creating output file: {actual_output_file}")
        with open(actual_output_file, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write(trans_units_text)
            f.write(footer)
        print(f"Output file created successfully: {actual_output_file}")

        # If in-place translation was requested, only replace the original file if translations were performed
        if is_inplace and temp_file and os.path.exists(temp_file):
            if stats.total_count > 0:
                try:
                    # Validate the temporary file before replacing the original
                    print("Validating translated file before replacing original...")
                    try:
                        # Verify that the temporary file is a valid XLIFF file
                        validation_tree = ET.parse(temp_file)
                        validation_root = validation_tree.getroot()

                        # Check if it's an XLIFF file
                        if not validation_root.tag.endswith('xliff'):
                            raise InvalidXliffError("Temporary file does not contain a valid XLIFF root element")

                        # Check if it has at least one trans-unit
                        ns = {'x': 'urn:oasis:names:tc:xliff:document:1.2'}
                        trans_units = validation_root.findall('.//x:trans-unit', ns)
                        if not trans_units:
                            # Try without namespace
                            trans_units = validation_root.findall('.//trans-unit')
                            if not trans_units:
                                raise NoTransUnitsError("No trans-unit elements found in temporary file")

                        print("Validation successful. Replacing original file...")
                    except (ET.ParseError, InvalidXliffError, NoTransUnitsError) as e:
                        print(f"Error: Validation of temporary file failed - {e}")
                        print("The original file will not be modified to prevent data loss.")
                        print(f"Translated content is available in temporary file: {temp_file}")
                        # Don't delete the temp file so the user can recover the translation
                        temp_file = None  # Set to None to prevent deletion in finally block
                        return stats_collector

                    # Create a backup of the original file before replacing it
                    backup_file = None
                    try:
                        backup_file = input_file + ".bak"
                        shutil.copy2(input_file, backup_file)
                        # Register the backup file for cleanup
                        register_backup_file(backup_file)
                        print(f"Created backup of original file: {backup_file}")
                    except Exception as e:
                        print(f"Warning: Could not create backup file - {e}")
                        print("Proceeding without backup...")

                    # Check if the files are on different drives
                    if are_on_different_drives(temp_file, input_file):
                        print("Files are on different drives. Using copy method instead of direct replacement...")
                        # Copy the contents of the temporary file to the original file
                        if copy_file_contents(temp_file, input_file):
                            print(f"Successfully copied translated content to original file: {input_file}")
                            # Remove the temporary file after successful copy
                            try:
                                os.remove(temp_file)
                                unregister_temp_file(temp_file)
                            except Exception as e:
                                print(f"Warning: Could not remove temporary file after copy: {e}")
                        else:
                            raise OSError("Failed to copy file contents between drives")
                    else:
                        # Replace the original file with the temporary file (same drive)
                        os.replace(temp_file, input_file)
                        print(f"Successfully replaced original file with translated content: {input_file}")

                    # Remove backup if everything went well
                    if backup_file and os.path.exists(backup_file):
                        try:
                            os.remove(backup_file)
                            # Unregister the backup file since it's been removed
                            unregister_backup_file(backup_file)
                        except Exception as e:
                            print(f"Note: Backup file was not removed and is available at: {backup_file}")

                    # Set temp_file to None to indicate it's been handled
                    # Unregister the temporary file since it's been replaced
                    unregister_temp_file(temp_file)
                    temp_file = None
                except PermissionError as e:
                    print(f"Error: Permission denied when replacing original file - {e}")
                    print(f"Translated content is available in temporary file: {temp_file}")
                    # Don't delete the temp file so the user can recover the translation
                    temp_file = None  # Set to None to prevent deletion in finally block
                    return stats_collector
                except OSError as e:
                    error_message = str(e)
                    if "different disk drive" in error_message or "WinError 17" in error_message:
                        print(f"Error: Cannot move file between different drives - {e}")
                        print("This is likely because the temporary file and the original file are on different drives.")
                        print("Try using a temporary directory on the same drive as the original file.")
                        print(f"Translated content is available in temporary file: {temp_file}")
                    else:
                        print(f"Error: OS error when replacing original file - {e}")
                        print(f"Translated content is available in temporary file: {temp_file}")
                    # Don't delete the temp file so the user can recover the translation
                    temp_file = None  # Set to None to prevent deletion in finally block
                    return stats_collector
                except Exception as e:
                    print(f"Error: Unexpected error when replacing original file - {e}")
                    print(f"Translated content is available in temporary file: {temp_file}")
                    # Don't delete the temp file so the user can recover the translation
                    temp_file = None  # Set to None to prevent deletion in finally block
                    return stats_collector
            else:
                print("No translations were performed. Original file will not be modified.")
                # Set temp_file to None to indicate we're not using it
                temp_file = None

        # Print statistics
        try:
            # Try relative import first
            from .statistics_reporting import StatisticsReporter
        except ImportError:
            # Fall back to absolute import (when installed as package)
            from bcxlftranslator.statistics_reporting import StatisticsReporter

        reporter = StatisticsReporter()
        reporter.print_statistics(stats)

        return stats  # Return statistics for testing and further processing

    except FileNotFoundError as e:
        print(f"Error: Input file not found - {e}")
        # Do not replace the original file if an error occurred
        temp_file = None  # Set to None to prevent deletion in finally block
        return stats_collector  # Return stats collector even on error
    except ET.ParseError as e:
        print(f"Error: XML parsing error - {e}")
        print("The XLIFF file appears to be malformed. The original file will not be modified.")
        temp_file = None  # Set to None to prevent deletion in finally block
        return stats_collector  # Return stats collector even on error
    except (InvalidXliffError, EmptyXliffError, MalformedXliffError, NoTransUnitsError) as e:
        print(f"Error: XLIFF validation error - {e}")
        print("The XLIFF file does not meet the required format. The original file will not be modified.")
        temp_file = None  # Set to None to prevent deletion in finally block
        return stats_collector  # Return stats collector even on error
    except aiohttp.ClientError as e:
        print(f"Error: Network error during translation - {e}")
        print("Failed to connect to translation service. The original file will not be modified.")
        temp_file = None  # Set to None to prevent deletion in finally block
        return stats_collector  # Return stats collector even on error
    except PermissionError as e:
        print(f"Error: Permission denied - {e}")
        print("Cannot write to the output file due to permission issues. The original file will not be modified.")
        temp_file = None  # Set to None to prevent deletion in finally block
        return stats_collector  # Return stats collector even on error
    except Exception as e:
        print(f"Error: Unexpected error - {e}")
        import traceback
        traceback.print_exc()
        print("An unexpected error occurred. The original file will not be modified.")
        # Do not replace the original file if an error occurred
        temp_file = None  # Set to None to prevent deletion in finally block
        return stats_collector  # Return stats collector even on error
    finally:
        # Clean up temporary file if it exists and hasn't been handled yet
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                # Unregister the temporary file since it's been removed
                unregister_temp_file(temp_file)
                print(f"Temporary file removed: {temp_file}")
            except PermissionError as e:
                print(f"Warning: Could not remove temporary file due to permission error: {e}")
                print(f"You may need to remove it manually: {temp_file}")
                # Keep the file registered for cleanup on exit
            except OSError as e:
                print(f"Warning: Could not remove temporary file due to OS error: {e}")
                print(f"You may need to remove it manually: {temp_file}")
                # Keep the file registered for cleanup on exit
            except Exception as e:
                print(f"Warning: Could not remove temporary file due to unexpected error: {e}")
                print(f"You may need to remove it manually: {temp_file}")
                # Keep the file registered for cleanup on exit

def parse_xliff(*args, **kwargs):
    """
    Stub for parse_xliff for TDD/test compatibility (for patching in tests).
    """
    return None
parse_xliff.is_stub = True


def report_progress(current, total):
    """
    Report progress during extraction or translation processes.

    Args:
        current (int): Current position in the process
        total (int): Total number of items to process
    """
    percent = int(current / total * 100) if total > 0 else 0
    print(f"Progress: {current}/{total} ({percent}%)")

def main():
    """Main entry point for the translator"""
    parser = argparse.ArgumentParser(
        description=(
            "Translate XLIFF files for Microsoft Dynamics 365 Business Central\n"
            "using Google Translate (via googletrans library) with caching.\n\n"
            "This tool provides a simple way to translate XLIFF files using Google Translate.\n\n"
            "Two operation modes are supported:\n"
            "1. Two-file mode: Translate from an input file to a separate output file\n"
            "2. In-place mode: Translate a file and update it directly (with safety measures)\n\n"
            "In-place translation uses temporary files and validation to ensure the original\n"
            "file is only modified if translation is successful. A backup is created before\n"
            "replacing the original file for additional safety."
        ),
        epilog=(
            "\nEXAMPLES:\n"
            "  # Two-file mode: Translate an XLIFF file to a new file\n"
            "  main.py input.xlf output.xlf\n\n"
            "  # In-place mode: Translate an XLIFF file in-place (modifies the original file)\n"
            "  main.py input.xlf\n\n"
            "  # Example with language-specific files\n"
            "  main.py BaseApp.en-US.xlf BaseApp.fr-FR.xlf    # Two-file mode\n"
            "  main.py BaseApp.fr-FR.xlf                      # In-place mode\n"
            "\nFor more information, see project documentation or use --help.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Translation CLI arguments
    parser.add_argument("input_file", nargs='?',
                       help="Path to the input XLIFF file to be translated.")
    parser.add_argument("output_file", nargs='?',
                       help="Path to save the translated XLIFF file. If not provided, the input file will be translated in-place with safety measures.")

    # Add some options to ensure help text formatting is consistent and provide useful information
    parser.add_argument("--delay", type=float,
                       help="  Set delay between translation requests in seconds (default: 0.5).")
    parser.add_argument("--retries", type=int,
                       help="  Set maximum number of retries for failed translations (default: 3).")
    parser.add_argument("--safe", action="store_true",
                       help="  Enable additional safety measures for in-place translation (already enabled by default).")
    parser.add_argument("--temp-dir", type=str,
                       help="  Specify a custom temporary directory for in-place translation. Useful when input file is on a different drive than the system temp directory.")

    args = parser.parse_args()

    # Check if input file is provided
    if args.input_file:
        # Determine output file
        output_file = args.output_file if args.output_file else args.input_file

        # If output_file is the same as input_file, it's in-place translation
        if output_file == args.input_file:
            print(f"Performing in-place translation on: {args.input_file}")
        else:
            print(f"Translating from {args.input_file} to {output_file}")

        # Run translation with appropriate settings
        asyncio.run(translate_xliff(
            args.input_file,
            output_file,
            add_attribution=True,
            temp_dir=args.temp_dir
        ))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
