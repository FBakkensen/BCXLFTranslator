# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import argparse
import time
import sys
from googletrans import Translator, LANGUAGES
import os # Added for path checking
import asyncio
import aiohttp

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
                part = source[current_pos:]
                source_parts.append((source[current_pos:current_pos + len(part.strip())], part.strip()))
                break

            # Get the part including its whitespace
            part = source[current_pos:next_comma]
            # Store the part and its stripped version
            source_parts.append((part, part.strip()))
            current_pos = next_comma + 1

        # Split translated text into parts
        translated_parts = [p.strip() for p in translated.split(',')]

        # If parts don't match, fall back to simple case matching
        if len(source_parts) != len(translated_parts):
            # Just capitalize the first letter when parts don't match
            return translated[0].upper() + translated[1:] if translated else translated

        # Build result with original spacing
        result = ""
        for i, ((original_part, stripped_source), translated_part) in enumerate(zip(source_parts, translated_parts)):
            # Add comma if not first part
            if i > 0:
                result += ','

            # Calculate leading/trailing spaces from original part
            leading_spaces = len(original_part) - len(original_part.lstrip())
            trailing_spaces = len(original_part) - len(original_part.rstrip())

            # Add leading spaces
            result += ' ' * leading_spaces

            # Add case-matched translation
            result += match_single_text(stripped_source, translated_part)

            # Add trailing spaces
            result += ' ' * trailing_spaces

        return result

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
    """Helper function to handle translation with retries"""
    try:
        result = await translator.translate(text, dest=dest_lang, src=src_lang)
        if result and result.text:
            # Match the capitalization pattern of the source text
            return match_case(text, result.text)
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

async def translate_xliff(input_file, output_file, add_attribution=True):
    """Main translation function - googletrans 4.0.2 version using async context manager"""
    if input_file is None or output_file is None:
        return main()  # Handle CLI when called without arguments

    print(f"Processing file: {input_file}")

    try:
        # Parse the XML file and register namespaces
        xliff_ns = 'urn:oasis:names:tc:xliff:document:1.2'
        xml_ns = 'http://www.w3.org/XML/1998/namespace'
        ET.register_namespace('', xliff_ns)
        ET.register_namespace('xml', xml_ns)
        ns = {
            'xliff': xliff_ns,
            'xml': xml_ns
        }

        tree = ET.parse(input_file)
        root = tree.getroot()

        # When finding trans-units, use both namespaces
        trans_units = root.findall('.//xliff:trans-unit[@xml:space]', ns)
        for unit in trans_units:
            # Get the space attribute with proper namespace
            space_value = unit.get('{%s}space' % xml_ns)
            # Store it temporarily
            unit.set('_space', space_value)

        # No need to manually handle xml:space as it will be preserved with proper namespace registration

        # Find the <file> element to get language info
        file_element = root.find('xliff:file', ns)
        if file_element is None:
            print("Error: Could not find the <file> element in the XLIFF.")
            sys.exit(1)

        source_lang_code = file_element.get('source-language')
        target_lang_code = file_element.get('target-language')

        if not target_lang_code:
            print("Error: Could not find 'target-language' attribute in <file> tag.")
            sys.exit(1)

        # Convert language codes to the format googletrans expects (lowercase)
        source_lang_google = source_lang_code.split('-')[0].lower() if source_lang_code else 'auto'
        target_lang_google = target_lang_code.split('-')[0].lower()

        if target_lang_google not in LANGUAGES:
             print(f"Warning: Target language code '{target_lang_google}' (from '{target_lang_code}') might not be directly supported by googletrans.")
             print("Attempting translation anyway...")
             # You might need to manually map specific codes if issues arise.

        print(f"Source Language: {source_lang_code} (Using '{source_lang_google}' for translation)")
        print(f"Target Language: {target_lang_code} (Using '{target_lang_google}' for translation)")

        # --- Caching Mechanism ---
        translation_cache = {} # Dictionary to store {source_text: translated_text}

        # Find all trans-unit elements
        trans_units = root.findall('.//xliff:trans-unit', ns)
        total_units = len(trans_units)
        print(f"Found {total_units} translation units.")

        translated_count = 0
        cached_count = 0
        skipped_count = 0
        error_count = 0
        current_unit = 0

        # Statistics for attribution
        microsoft_term_count = 0
        google_term_count = 0

        async with Translator() as translator:
            for unit in trans_units:
                current_unit += 1
                # Display progress every 10 units
                if current_unit % 10 == 0 or current_unit == total_units:
                    progress = (current_unit / total_units) * 100
                    print(f"\nProgress: {current_unit}/{total_units} ({progress:.1f}%)")
                    print(f"Translated: {translated_count}, Cached: {cached_count}, Skipped: {skipped_count}, Errors: {error_count}\n")

                # Check if translation is required for this unit
                translate_attr = unit.get('translate', 'yes') # Default to 'yes' if attribute is missing
                if translate_attr.lower() != 'yes':
                    skipped_count += 1
                    continue

                target_element = unit.find('xliff:target', ns)
                source_element = unit.find('xliff:source', ns)

                if target_element is not None and source_element is not None:
                    target_state = target_element.get('state')

                    # Check if the target needs translation
                    if target_state == 'needs-translation':
                        source_text = source_element.text
                        if source_text and source_text.strip(): # Check if source text exists and is not empty

                            # --- Check Cache ---
                            if source_text in translation_cache:
                                cached_translation = translation_cache[source_text]
                                if cached_translation: # Ensure cached value isn't None (from a previous error)
                                    target_element.text = cached_translation
                                    target_element.set('state', 'translated') # Update state
                                    target_element.set('state-qualifier', 'exact-match')
                                    cached_count += 1

                                    # Add attribution if needed
                                    if add_attribution:
                                        # Determine source based on the cache entry's metadata
                                        if source_text in translation_cache:
                                            source_info = translation_cache.get(f"{source_text}_source", "GOOGLE")

                                            # Generate and add attribution note
                                            from bcxlftranslator import note_generation

                                            # Add metadata about the translation
                                            metadata = {
                                                "source_text": source_text,
                                                "translated_text": cached_translation,
                                                "unit_id": unit.get('id', ''),
                                            }

                                            note_text = note_generation.generate_attribution_note(
                                                source=source_info,
                                                metadata=metadata
                                            )

                                            note_generation.add_note_to_trans_unit(
                                                unit,
                                                note_text,
                                                from_attribute="BCXLFTranslator"
                                            )
                                else:
                                    # Source text was seen before, but failed to translate. Skip again.
                                    skipped_count += 1
                                continue # Move to the next unit

                            # --- Check Terminology Database First ---
                            terminology_translation = terminology_lookup(source_text, target_lang_code)

                            if terminology_translation:
                                # Use Microsoft terminology if available
                                target_element.text = match_case(source_text, terminology_translation)
                                target_element.set('state', 'translated')
                                target_element.set('state-qualifier', 'exact-match')
                                translated_count += 1
                                microsoft_term_count += 1

                                # Cache both the translation and its source
                                translation_cache[source_text] = target_element.text
                                translation_cache[f"{source_text}_source"] = "MICROSOFT"

                                # Add attribution note if enabled
                                if add_attribution:
                                    from bcxlftranslator import note_generation

                                    # Add metadata about the translation
                                    metadata = {
                                        "source_text": source_text,
                                        "translated_text": target_element.text,
                                        "unit_id": unit.get('id', ''),
                                    }

                                    note_text = note_generation.generate_attribution_note(
                                        source="MICROSOFT",
                                        metadata=metadata
                                    )

                                    note_generation.add_note_to_trans_unit(
                                        unit,
                                        note_text,
                                        from_attribute="BCXLFTranslator"
                                    )

                                # Remove the NAB AL Tool Refresh Xlf note if it exists
                                refresh_notes = unit.findall('xliff:note[@from="NAB AL Tool Refresh Xlf"]', ns)
                                for note in refresh_notes:
                                    unit.remove(note)

                                continue  # Skip Google Translate for this unit

                            # --- Not in Terminology Database: Translate with Google ---
                            source_text_preview = source_text[:50] + "..." if len(source_text) > 50 else source_text
                            print(f"[{current_unit}/{total_units}] Translating: '{source_text_preview}'")
                            translated_text = None # Initialize variable
                            try:
                                # Add delay before making the request
                                if DELAY_BETWEEN_REQUESTS > 0:
                                    await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

                                translated_text = await translate_with_retry(
                                    translator,
                                    source_text,
                                    target_lang_google,
                                    source_lang_google
                                )

                                if translated_text:
                                    # Set the translation and attributes
                                    target_element.text = translated_text
                                    target_element.set('state', 'translated')
                                    target_element.set('state-qualifier', 'exact-match')

                                    # Remove the NAB AL Tool Refresh Xlf note if it exists
                                    refresh_notes = unit.findall('xliff:note[@from="NAB AL Tool Refresh Xlf"]', ns)
                                    for note in refresh_notes:
                                        unit.remove(note)

                                    # Add attribution note if enabled
                                    if add_attribution:
                                        from bcxlftranslator import note_generation

                                        # Add metadata about the translation
                                        metadata = {
                                            "source_text": source_text,
                                            "translated_text": translated_text,
                                            "unit_id": unit.get('id', ''),
                                        }

                                        note_text = note_generation.generate_attribution_note(
                                            source="GOOGLE",
                                            metadata=metadata
                                        )

                                        note_generation.add_note_to_trans_unit(
                                            unit,
                                            note_text,
                                            from_attribute="BCXLFTranslator"
                                        )

                                    print(f"    -> Translated: '{translated_text[:50]}...'")
                                    translated_count += 1
                                    google_term_count += 1
                                    translation_cache[source_text] = translated_text
                                    translation_cache[f"{source_text}_source"] = "GOOGLE"
                                else:
                                    print(f"    -> Error: Translation failed after retries")
                                    error_count += 1
                                    translation_cache[source_text] = None

                            except Exception as e:
                                print(f"    -> Error translating: {e}")
                                print(f"    -> Debug: Translation error details for text: '{source_text}'")
                                error_count += 1
                                translation_cache[source_text] = None

                        else:
                            print(f"  Skipping unit {unit.get('id')}: Empty source text.")
                            skipped_count += 1
                    else:
                        # Skip units that don't need translation (already translated, etc.)
                        skipped_count += 1
                else:
                    # Skip units missing source or target elements
                    print(f"  Skipping unit {unit.get('id')}: Missing source or target element.")
                    skipped_count += 1

        # Before writing, restore the xml:space attributes
        for unit in root.findall('.//xliff:trans-unit', ns):
            # Preserve xml:space if present in the original attributes
            orig_unit = unit
            xml_space = orig_unit.get('{%s}space' % xml_ns)
            if xml_space is not None:
                unit.set('{%s}space' % xml_ns, xml_space)

        # Ensure output directory exists before writing
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                print(f"Created output directory: {output_dir}")
            except OSError as e:
                print(f"Error creating output directory '{output_dir}': {e}")
                sys.exit(1)  # Exit if we can't create the directory

        # Register XML namespace for proper attribute handling
        ET.register_namespace('xml', 'http://www.w3.org/XML/1998/namespace')

        # Write the modified tree
        tree.write(output_file, encoding='utf-8', xml_declaration=True)

        print("\n=== Translation process finished ===")
        print(f"Total units processed:  {total_units}")
        print(f"Units translated:       {translated_count}")
        print(f"  - Microsoft Terminology: {microsoft_term_count}")
        print(f"  - Google Translate:      {google_term_count}")
        print(f"Units from cache:       {cached_count}")
        print(f"Units skipped:          {skipped_count}")
        print(f"Errors occurred:        {error_count}")
        print(f"Success rate:           {((translated_count + cached_count) / total_units * 100):.1f}%")

        print(f"Translated file saved as: {output_file}")

        # Ensure all database connections are closed after translation
        from bcxlftranslator import terminology_db
        terminology_db.TerminologyDatabaseRegistry.close_all()

    except ET.ParseError as e:
        print(f"Error parsing XML file '{input_file}': {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_file}'")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

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
        from bcxlftranslator.terminology_db import get_terminology_database
        db = get_terminology_database()
        if db is None:
            return None
        result = db.lookup_term(source_text, target_lang)
        return result
    except Exception as e:
        print(f"Error looking up term in terminology database: {e}")
        return None

def extract_terminology_command(xliff_file, lang, filter_type=None):
    """
    Command function for terminology extraction. Minimal implementation for TDD.
    """
    import xml.etree.ElementTree as ET
    class Result:
        def __init__(self, success, count_extracted):
            self.success = success
            self.count_extracted = count_extracted
    try:
        tree = ET.parse(xliff_file)
        root = tree.getroot()
        ns = {'x': 'urn:oasis:names:tc:xliff:document:1.2'}
        trans_units = root.findall('.//x:trans-unit', ns)
        if filter_type:
            filtered = [tu for tu in trans_units if tu.get('id', '').lower().startswith(filter_type.lower())]
            units_to_process = filtered
        else:
            units_to_process = trans_units
        # Call report_progress if processing many units
        if len(units_to_process) > 10:
            for idx, _ in enumerate(units_to_process):
                if idx % 10 == 0:
                    report_progress(idx, len(units_to_process))
        elif len(units_to_process) > 0:
            report_progress(len(units_to_process), len(units_to_process))
        count = len(units_to_process)
        report_extraction_results()
        return Result(success=True, count_extracted=count)
    except FileNotFoundError:
        raise
    except ET.ParseError:
        raise
    except Exception as e:
        raise

def report_extraction_results(*args, **kwargs):
    """
    Stub for reporting extraction results. TDD stub.
    """
    pass


def report_progress(*args, **kwargs):
    """
    Stub for progress reporting. TDD stub.
    """
    pass

def main():
    """Main entry point for the translator"""
    parser = argparse.ArgumentParser(
        description="Translate XLIFF files using Google Translate (via googletrans library) with caching, or extract terminology from XLIFF files.")
    subparsers = parser.add_subparsers(dest="command", required=False)

    # Extraction command group (Step 8.1)
    parser.add_argument('--extract-terminology', metavar='XLIFF_FILE', help='Extract terminology from the given XLIFF file')
    parser.add_argument('--lang', metavar='LANG', help='Language code for extraction (e.g., da-DK)')
    parser.add_argument('--filter', metavar='FILTER', help='Optional filter for extraction (e.g., Table, Field, Page)')

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
        sys.exit(0)

    # Translation mode (default)
    if args.input_file and args.output_file:
        asyncio.run(translate_xliff(args.input_file, args.output_file))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
