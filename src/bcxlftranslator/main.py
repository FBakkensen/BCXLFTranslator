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

async def translate_xliff(input_file, output_file, add_attribution=True, use_terminology=False, highlight_terms=False, db_path=None):
    """
    Main translation function - googletrans 4.0.2 version using async context manager
    
    Args:
        input_file (str): Path to the input XLIFF file
        output_file (str): Path to save the translated XLIFF file
        add_attribution (bool): Whether to add attribution notes to translation units
        use_terminology (bool): Whether to use terminology database for translation
        highlight_terms (bool): Whether to highlight terms from terminology database
        db_path (str): Path to the terminology database file
        
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
    
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' not found.")
            return stats_collector  # Return empty stats instead of None

        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Parse the XLIFF file
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

        # Initialize terminology database if terminology is enabled
        if use_terminology:
            try:
                # Try relative import first
                from .terminology_db import get_terminology_database
            except ImportError:
                # Fall back to absolute import (when installed as package)
                from bcxlftranslator.terminology_db import get_terminology_database
            
            try:
                if db_path:
                    get_terminology_database(db_path)
                    print(f"Using terminology database: {db_path}")
                else:
                    # Use default in-memory database if no path specified
                    get_terminology_database()
                    print("Using in-memory terminology database")
            except Exception as e:
                print(f"Warning: Failed to initialize terminology database: {e}")
                print("Continuing without terminology support.")
                use_terminology = False

        # Find all translation units
        trans_units = root.findall(f".//{ns}trans-unit")
        total_units = len(trans_units)
        print(f"Found {total_units} translation units.")

        # Translation cache to avoid re-translating the same text
        translation_cache = {}

        # Create a translator instance using async context manager
        async with Translator() as translator:
            # Process each translation unit
            for i, trans_unit in enumerate(trans_units):
                # Report progress
                report_progress(i, total_units)

                # Check if this unit should be translated
                translate_attr = trans_unit.get("translate", "yes")
                if translate_attr.lower() == "no":
                    continue

                # Get source and target elements
                source_elem = trans_unit.find(f"{ns}source")
                target_elem = trans_unit.find(f"{ns}target")

                if source_elem is not None and target_elem is not None:
                    source_text = source_elem.text or ""
                    
                    # Skip empty source text
                    if not source_text.strip():
                        continue

                    # Try to translate using terminology database first if enabled
                    target_text = None
                    terminology_used = False
                    
                    if use_terminology:
                        try:
                            # Look up in terminology database
                            term_translation = terminology_lookup(source_text, target_lang)
                            if term_translation:
                                target_text = term_translation
                                terminology_used = True
                                # Track terminology usage in statistics
                                stats_collector.track_translation("Microsoft Terminology", 
                                                               source_text=source_text, 
                                                               target_text=target_text)
                        except Exception as e:
                            print(f"Warning: Terminology lookup failed: {e}")
                            # Continue with Google Translate
                    
                    # If terminology didn't provide a translation, use Google Translate
                    if not terminology_used:
                        # Check if we've already translated this text
                        if source_text in translation_cache:
                            target_text = translation_cache[source_text]
                        else:
                            try:
                                # Translate the text
                                result = await translate_with_retry(translator, source_text, target_lang_code, source_lang_code)
                                target_text = result.text
                                
                                # Cache the translation
                                translation_cache[source_text] = target_text
                            except Exception as e:
                                print(f"Warning: Translation failed for '{source_text}': {e}")
                                # Skip this unit rather than exiting
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
                    
                    # Add state-qualifier attribute for terminology matches if highlighting is enabled
                    if terminology_used and highlight_terms:
                        target_elem.set("state-qualifier", "exact-match")
                    
                    # Add attribution note if requested
                    if add_attribution:
                        try:
                            # Try relative import first
                            from .note_generation import add_note_to_trans_unit, generate_attribution_note
                        except ImportError:
                            # Fall back to absolute import (when installed as package)
                            from bcxlftranslator.note_generation import add_note_to_trans_unit, generate_attribution_note
                        
                        # Determine the source for the note
                        if terminology_used:
                            note_source = "MICROSOFT"
                        else:
                            note_source = "GOOGLE"
                        
                        # Generate and add the note
                        note_text = generate_attribution_note(note_source)
                        add_note_to_trans_unit(trans_unit, note_text)

        # Report final progress
        report_progress(total_units, total_units)
        print("\nTranslation complete.")

        # Calculate and display statistics
        stats = stats_collector.get_statistics()
        
        # Print statistics
        try:
            # Try relative import first
            from .statistics_reporting import StatisticsReporter
        except ImportError:
            # Fall back to absolute import (when installed as package)
            from bcxlftranslator.statistics_reporting import StatisticsReporter
        
        reporter = StatisticsReporter()
        reporter.print_statistics(stats)

        # Write the translated XLIFF to the output file
        try:
            # Try to use lxml for better namespace handling if available
            try:
                from lxml import etree
                print("Using lxml for namespace preservation.")
                # Convert ElementTree to string
                xml_str = ET.tostring(root, encoding='utf-8')
                lxml_root = etree.fromstring(xml_str)
                # Remove all namespace prefixes (force default namespace)
                for elem in lxml_root.iter():
                    if not hasattr(elem.tag, 'find'):
                        continue
                    if elem.tag.startswith('{'):
                        uri, local = elem.tag[1:].split('}')
                        elem.tag = local
                # Register the default namespace
                default_ns = root.tag.split('}')[0][1:]
                nsmap = {None: default_ns}
                new_root = etree.Element('xliff', nsmap=nsmap)
                # Copy attributes from original root
                for k, v in lxml_root.attrib.items():
                    new_root.set(k, v)
                # Move children to new root
                for child in lxml_root:
                    new_root.append(child)
                tree_lxml = etree.ElementTree(new_root)
                tree_lxml.write(output_file, encoding="utf-8", xml_declaration=True, pretty_print=True)
                print("lxml write complete.")
            except ImportError:
                print("lxml not available; using ElementTree fallback.")
                # Deep copy and strip namespaces
                clean_root = copy.deepcopy(root)
                strip_namespace(clean_root)
                # Set correct default namespace on root
                clean_root.set('xmlns', 'urn:oasis:names:tc:xliff:document:1.2')
                clean_tree = ET.ElementTree(clean_root)
                # Add new helper function for pretty-printing XML using ElementTree
                def indent(element, indent_level=0):
                    i = "\n" + "  " * indent_level
                    if len(element):
                        if not element.text or not element.text.strip():
                            element.text = i + "  "
                        for child in element:
                            indent(child, indent_level + 1)
                            if not child.tail or not child.tail.strip():
                                child.tail = i + "  "
                        if not child.tail or not child.tail.strip():
                            child.tail = i
                    else:
                        if indent_level and (not element.tail or not element.tail.strip()):
                            element.tail = i
                # In translate_xliff ElementTree fallback, add indentation before write
                indent(clean_root)
                clean_tree.write(output_file, encoding="utf-8", xml_declaration=True)
                print("Wrote cleaned XLIFF without prefixes using ElementTree fallback.")
            except Exception as e:
                print(f"Exception in lxml branch: {e}. Using regex fallback.")
                import re
                tree.write(output_file, encoding="utf-8", xml_declaration=True)
                with open(output_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Remove ns0: from opening and closing tags, even with whitespace, newlines, or attributes
                content = re.sub(r'<(/?)\s*ns0:', r'<\1', content, flags=re.MULTILINE)
                # Remove xmlns:ns0 definitions (with possible whitespace)
                content = re.sub(r'\s+xmlns:ns0="[^"]*"', '', content)
                # Remove any leftover empty xmlns attributes (e.g., xmlns:ns0="")
                content = re.sub(r'\s+xmlns:ns0=""', '', content)
                # Remove any remaining xmlns attributes with empty value
                content = re.sub(r'\s+xmlns=""', '', content)
                # Ensure the root xliff tag has the correct default namespace (force replace the first <xliff ...>)
                content = re.sub(r'<xliff(\s|>)', r'<xliff xmlns="urn:oasis:names:tc:xliff:document:1.2"\1', content, count=1)
                # Optionally clean up double spaces
                content = re.sub(r'\s{2,}', ' ', content)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("Warning: Could not fully preserve namespace via lxml; applied string-based fallback.")
                print('--- OUTPUT FILE CONTENT (regex fallback) ---')
                print(content)
                print('---------------------------------------------')
        except Exception as e:
            print(f"Error writing XLIFF output: {e}")
            raise
        print(f"Translated XLIFF saved to {output_file}")
        
        return stats  # Return statistics for testing and further processing

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return stats_collector  # Return stats collector even on error

def terminology_lookup(source_text, target_lang_code):
    """
    Look up a source text in the terminology database for the target language.

    Args:
        source_text (str): The source text to look up
        target_lang_code (str): The target language code (e.g., 'da-DK')

    Returns:
        str or None: The translated term from terminology database, or None if not found
    """
    try:
        # Normalize target language code to just the language part if needed
        target_lang = target_lang_code.split('-')[0].lower() if '-' in target_lang_code else target_lang_code.lower()

        # Get the terminology database singleton
        try:
            # Try relative import first
            from .terminology_db import get_terminology_database
        except ImportError:
            # Fall back to absolute import (when installed as package)
            from bcxlftranslator.terminology_db import get_terminology_database
        
        db = get_terminology_database()
        if db is None:
            return None
        result = db.lookup_term(source_text, target_lang)
        return result.get('target_term') if result else None
    except Exception as e:
        print(f"Error looking up term in terminology database: {e}")
        return None

def parse_xliff(*args, **kwargs):
    """
    Stub for parse_xliff for TDD/test compatibility (for patching in tests).
    """
    return None
parse_xliff.is_stub = True

def extract_terminology_command(xliff_file, lang, filter_type=None, db_path=None, overwrite=False, verbose=False, quiet=False):
    """
    Command function for terminology extraction. Now supports advanced options for TDD Step 8.5.
    """
    try:
        # Import here to allow patching in tests
        import src.bcxlftranslator.terminology_db as terminology_db
    except ImportError:
        try:
            import bcxlftranslator.terminology_db as terminology_db
        except ImportError:
            terminology_db = None
    class Result:
        def __init__(self, success, count_extracted, exit_code=0):
            self.success = success
            self.count_extracted = count_extracted
            self.exit_code = exit_code
    try:
        # Allow test patching of parse_xliff (only if not the built-in stub)
        use_parse_xliff = (
            'parse_xliff' in globals()
            and callable(globals()['parse_xliff'])
            and not getattr(globals()['parse_xliff'], 'is_stub', False)
        )
        if use_parse_xliff:
            terms = parse_xliff(xliff_file, lang)
            units_to_process = terms if terms is not None else []
            count = len(units_to_process)
        else:
            tree = ET.parse(xliff_file)
            root = tree.getroot()
            # Simulate filtering by type
            trans_units = root.findall('.//{urn:oasis:names:tc:xliff:document:1.2}trans-unit')
            units_to_process = []
            for tu in trans_units:
                tu_id = tu.get('id', '')
                if filter_type and filter_type.lower() not in tu_id.lower():
                    continue
                units_to_process.append(tu)
            count = len(units_to_process)
        # Simulate DB storage
        if db_path and terminology_db:
            db = terminology_db.TerminologyDatabase(db_path)
            # If parse_xliff was used, terms may be dicts, otherwise ElementTree elements
            if units_to_process and isinstance(units_to_process[0], dict):
                db.store_terms(units_to_process, overwrite=overwrite)
            else:
                db.store_terms([
                    {'id': tu.get('id'), 'source': tu.findtext('{urn:oasis:names:tc:xliff:document:1.2}source'), 'target': tu.findtext('{urn:oasis:names:tc:xliff:document:1.2}target')}
                    for tu in units_to_process
                ], overwrite=overwrite)
        # Reporting
        if not quiet:
            if verbose:
                print(f"Extracted {count} terms from {xliff_file} (lang={lang}, filter={filter_type}, overwrite={overwrite})")
                # Print details for both dict and ET.Element
                for tu in units_to_process:
                    if isinstance(tu, dict):
                        print(f"Term: {tu.get('source')} -> {tu.get('target')}")
                    else:
                        print(f"Term: {tu.findtext('{urn:oasis:names:tc:xliff:document:1.2}source')} -> {tu.findtext('{urn:oasis:names:tc:xliff:document:1.2}target')}")
            else:
                print(f"Extracted {count} terms.")
        # Simulate warning exit code if no terms
        exit_code = 0 if count > 0 else 1
        report_extraction_results()
        # Progress reporting for large files (only if not quiet mode)
        if not quiet:
            if len(units_to_process) > 10:
                for idx, _ in enumerate(units_to_process):
                    if idx % 10 == 0:
                        report_progress(idx, len(units_to_process))
            elif len(units_to_process) > 0:
                report_progress(len(units_to_process), len(units_to_process))
        return Result(success=True, count_extracted=count, exit_code=exit_code)
    except FileNotFoundError as e:
        if not quiet:
            print(f"Error: File not found: {xliff_file}")
        raise
    except ET.ParseError as e:
        if not quiet:
            print(f"Error: XML parse error in {xliff_file}: {e}")
        raise
    except Exception as e:
        if not quiet:
            print(f"Error during extraction: {e}")
        raise

def report_extraction_results(*args, **kwargs):
    """
    Stub for reporting extraction results. TDD stub.
    """
    pass


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
            "Translate XLIFF files for Microsoft Dynamics 365 Business Central using Google Translate (via googletrans library) with caching, or extract and use Business Central terminology from XLIFF files.\n\n"
            "This tool supports advanced terminology integration for Business Central translation workflows, enabling consistent use of approved terms and fallback to machine translation where needed."
        ),
        epilog=(
            "\nEXAMPLES:\n"
            "  # Translate using terminology database\n"
            "  main.py input.xlf output.xlf --use-terminology --db bc_terms.db\n"
            "\n  # Extract terminology from an XLIFF reference file\n"
            "  main.py --extract-terminology reference.xlf --lang da-DK --db-path bc_terms.db\n"
            "\nBEST PRACTICES FOR TERMINOLOGY USAGE:\n"
            "  - Always use the latest approved terminology database for Business Central projects.\n"
            "  - Review extracted terms for accuracy and context before translation.\n"
            "  - Use --enable-term-matching to enforce strict term usage in regulated scenarios.\n"
            "  - Use --disable-term-highlighting for production files to avoid extra markup.\n"
            "  - Fallback to Google Translate is automatic when a term is not found in the terminology DB.\n"
            "  - For large projects, batch process with consistent terminology options.\n"
            "\nFor more information, see project documentation or use --help with any command.\n"
        )
    )
    
    # Extraction command group (Step 8.1)
    parser.add_argument('--extract-terminology', metavar='XLIFF_FILE', help='Extract terminology from the given XLIFF file')
    parser.add_argument('--lang', metavar='LANG', help='Language code for extraction (e.g., da-DK)')
    parser.add_argument('--filter', metavar='FILTER', help='Optional filter for extraction (e.g., Table, Field, Page)')
    parser.add_argument('--db-path', metavar='DB_PATH', help='Path to the terminology database file')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing terms in the database')
    parser.add_argument('--verbose', action='store_true', help='Print detailed extraction information')
    parser.add_argument('--quiet', action='store_true', help='Suppress extraction output')

    # Step 9.1: Terminology usage CLI arguments for translation
    parser.add_argument('--use-terminology', action='store_true', help='Enable usage of terminology database for translation')
    parser.add_argument('--db', type=str, help='Path to the terminology database file (for translation)')
    parser.add_argument('--enable-term-matching', action='store_true', help='Enable terminology matching feature')
    parser.add_argument('--disable-term-matching', action='store_true', help='Disable terminology matching feature')
    parser.add_argument('--enable-term-highlighting', action='store_true', help='Enable terminology highlighting feature')
    parser.add_argument('--disable-term-highlighting', action='store_true', help='Disable terminology highlighting feature')

    # Original translation CLI arguments
    parser.add_argument("input_file", nargs='?', help="Path to the input XLIFF file.")
    parser.add_argument("output_file", nargs='?', help="Path to save the translated XLIFF file.")

    args = parser.parse_args()

    # Extraction mode
    if args.extract_terminology:
        if not args.lang:
            parser.error('The --lang parameter is required when using --extract-terminology.')
        # For now, just print parsed values (minimal implementation for TDD)
        print(f"Extracting terminology from: {args.extract_terminology} (lang={args.lang}, filter={args.filter})")
        extract_terminology_command(args.extract_terminology, args.lang, args.filter, args.db_path, args.overwrite, args.verbose, args.quiet)
        sys.exit(0)

    # Step 9.1: Validate terminology argument combinations (translation mode only)
    if args.use_terminology:
        if args.enable_term_matching and args.disable_term_matching:
            parser.error('Cannot use both --enable-term-matching and --disable-term-matching.')
        if args.enable_term_highlighting and args.disable_term_highlighting:
            parser.error('Cannot use both --enable-term-highlighting and --disable-term-highlighting.')

    # Translation mode (default)
    if args.input_file and args.output_file:
        # Determine terminology settings
        use_terminology = args.use_terminology
        highlight_terms = args.enable_term_highlighting and not args.disable_term_highlighting
        db_path = args.db or None
        
        # Run translation with appropriate settings
        asyncio.run(translate_xliff(
            args.input_file, 
            args.output_file, 
            add_attribution=True,
            use_terminology=use_terminology,
            highlight_terms=highlight_terms,
            db_path=db_path
        ))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
