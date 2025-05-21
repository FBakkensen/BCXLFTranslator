import os
import xml.etree.ElementTree as ET
import logging
import re

from .exceptions import InvalidXliffError, EmptyXliffError, MalformedXliffError, NoTransUnitsError

def load_xliff_file(file_path):
    """
    Load and parse an XLIFF file.

    Args:
        file_path (str): Path to the XLIFF file.

    Returns:
        xml.etree.ElementTree.ElementTree: Parsed XML document object.

    Raises:
        FileNotFoundError: If the file does not exist.
        EmptyXliffError: If the file is empty.
        MalformedXliffError: If the XML is malformed.
        InvalidXliffError: If the root element is not <xliff>.
        NoTransUnitsError: If no trans-unit elements are found in the file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if os.path.getsize(file_path) == 0:
        raise EmptyXliffError(f"File is empty: {file_path}")

    try:
        tree = ET.parse(file_path)
    except ET.ParseError as e:
        raise MalformedXliffError(f"Malformed XML in file: {file_path}. Error: {str(e)}")

    root = tree.getroot()
    # Handle namespace in root tag
    # root.tag can be '{namespace}xliff', so check localname
    if root.tag.endswith('xliff'):
        # Check if the file has at least one trans-unit
        ns = {'x': 'urn:oasis:names:tc:xliff:document:1.2'}
        trans_units = root.findall('.//x:trans-unit', ns)
        if not trans_units:
            # Try without namespace
            trans_units = root.findall('.//trans-unit')
            if not trans_units:
                raise NoTransUnitsError(f"No trans-unit elements found in {file_path}")
        return tree
    else:
        raise InvalidXliffError(f"Root element is not <xliff>: {root.tag}")

def extract_trans_units_as_dict(xliff_doc):
    """
    Extract all trans-unit elements from the parsed XLIFF document as dictionaries.

    Args:
        xliff_doc (xml.etree.ElementTree.ElementTree): Parsed XLIFF document.

    Returns:
        list of dict: List of dictionaries with keys 'id', 'source_text', 'target_text'.
    """
    ns = {'x': 'urn:oasis:names:tc:xliff:document:1.2'}
    root = xliff_doc.getroot()
    trans_units = []
    for tu in root.findall('.//x:trans-unit', ns):
        tu_id = tu.get('id')
        source_elem = tu.find('x:source', ns)
        target_elem = tu.find('x:target', ns)

        if source_elem is None:
            source_text = None
        else:
            source_text = source_elem.text
            if source_text is None:
                source_text = ""

        if target_elem is None:
            target_text = None
        else:
            target_text = target_elem.text
            if target_text is None:
                target_text = ""

        trans_units.append({
            'id': tu_id,
            'source_text': source_text,
            'target_text': target_text
        })
    return trans_units

def extract_trans_units(xliff_doc):
    """
    Extract all trans-unit elements from the parsed XLIFF document as XML Element objects.

    Args:
        xliff_doc (xml.etree.ElementTree.ElementTree): Parsed XLIFF document.

    Returns:
        list: List of xml.etree.ElementTree.Element objects representing trans-units.
    """
    ns = {'x': 'urn:oasis:names:tc:xliff:document:1.2'}
    root = xliff_doc.getroot()
    return root.findall('.//x:trans-unit', ns)

def extract_trans_units_from_file(file_path):
    """
    Extract all trans-unit elements from an XLIFF file as XML Element objects.

    Args:
        file_path (str): Path to the XLIFF file.

    Returns:
        list: List of xml.etree.ElementTree.Element objects representing trans-units.

    Raises:
        FileNotFoundError: If the file does not exist.
        EmptyXliffError: If the file is empty.
        MalformedXliffError: If the XML is malformed.
        InvalidXliffError: If the root element is not <xliff>.
        NoTransUnitsError: If no trans-unit elements are found in the file.
    """
    xliff_doc = load_xliff_file(file_path)
    return extract_trans_units(xliff_doc)

# --- Logging Setup ---
# Basic configuration for logging within this module
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

# --- Main Parser Function ---

def extract_header_footer(file_path):
    """
    Reads an XLIFF file as text and extracts the exact header (everything before the first trans-unit)
    and footer (everything after the last trans-unit).

    Args:
        file_path (str): Path to the XLIFF file.

    Returns:
        tuple: A tuple containing (header, footer) as strings.

    Raises:
        FileNotFoundError: If the file does not exist.
        EmptyXliffError: If the file is empty.
        NoTransUnitsError: If no trans-unit elements are found in the file.
        MalformedXliffError: If the XLIFF file is malformed (e.g., mismatched tags).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if os.path.getsize(file_path) == 0:
        raise EmptyXliffError(f"File is empty: {file_path}")

    try:
        # Read the entire file as text
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Basic XML validation check
        if not content.strip().startswith('<?xml') and not content.strip().startswith('<xliff'):
            raise MalformedXliffError(f"File does not appear to be a valid XML/XLIFF file: {file_path}")

        # Check for basic XML structure issues
        if content.count('<') != content.count('>'):
            raise MalformedXliffError(f"Mismatched XML tags in file: {file_path}")

        # Find the first trans-unit opening tag (with or without namespace)
        first_trans_unit_match = re.search(r'<(?:[^>]*:)?trans-unit', content)
        if not first_trans_unit_match:
            raise NoTransUnitsError(f"No trans-unit elements found in {file_path}")

        first_trans_unit_start = first_trans_unit_match.start()

        # Find the last trans-unit closing tag
        # First, try to find all closing tags (both with and without namespace)
        trans_unit_end_tags = list(re.finditer(r'</(?:[^>]*:)?trans-unit>', content))
        if not trans_unit_end_tags:
            raise MalformedXliffError(f"No closing trans-unit tags found in {file_path}. File may be malformed.")

        # Get the position of the last closing tag
        last_trans_unit_end = trans_unit_end_tags[-1].end()

        # Validate that the first opening tag comes before the last closing tag
        if first_trans_unit_start >= last_trans_unit_end:
            raise MalformedXliffError(f"Invalid trans-unit structure in file: {file_path}. Opening tag appears after closing tag.")

        # Extract header and footer
        header = content[:first_trans_unit_start]
        footer = content[last_trans_unit_end:]

        # Validate that essential XLIFF elements are present in the header
        if '<xliff' not in header:
            raise MalformedXliffError(f"Missing <xliff> element in file: {file_path}")

        if '<file' not in header:
            raise MalformedXliffError(f"Missing <file> element in file: {file_path}")

        # Validate that essential XLIFF closing elements are present in the footer
        if '</xliff>' not in footer:
            raise MalformedXliffError(f"Missing </xliff> closing tag in file: {file_path}")

        return header, footer

    except (UnicodeDecodeError, IOError) as e:
        raise MalformedXliffError(f"Error reading file {file_path}: {str(e)}")
    except Exception as e:
        if isinstance(e, (NoTransUnitsError, MalformedXliffError, EmptyXliffError, FileNotFoundError)):
            raise
        raise MalformedXliffError(f"Unexpected error processing file {file_path}: {str(e)}")

def preserve_indentation(file_path):
    """
    Extracts the indentation pattern from the original trans-units and returns a dictionary
    with the indentation patterns for different elements.

    Args:
        file_path (str): Path to the XLIFF file.

    Returns:
        dict: A dictionary with keys 'trans_unit' and 'child' containing the indentation patterns.

    Raises:
        FileNotFoundError: If the file does not exist.
        EmptyXliffError: If the file is empty.
        NoTransUnitsError: If no trans-unit elements are found in the file.
        MalformedXliffError: If the XLIFF file is malformed or cannot be read.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if os.path.getsize(file_path) == 0:
        raise EmptyXliffError(f"File is empty: {file_path}")

    # Initialize indentation patterns
    indentation_patterns = {
        'trans_unit': None,
        'child': None
    }

    try:
        # Read the file line by line
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Check if the line contains a trans-unit tag
                if '<trans-unit' in line:
                    # Extract the leading whitespace
                    indentation_patterns['trans_unit'] = line[:line.find('<trans-unit')]

                # Check if the line contains a child element (source, target, note)
                elif any(tag in line for tag in ['<source', '<target', '<note']):
                    # Extract the leading whitespace
                    for tag in ['<source', '<target', '<note']:
                        if tag in line:
                            indentation_patterns['child'] = line[:line.find(tag)]
                            break

                # If we have found both patterns, we can stop
                if all(indentation_patterns.values()):
                    break

        # If we didn't find any trans-unit elements, raise an error
        if indentation_patterns['trans_unit'] is None:
            raise NoTransUnitsError(f"No trans-unit elements found in {file_path}")

        # If we didn't find any child elements, use a default (trans_unit + 2 spaces)
        if indentation_patterns['child'] is None:
            indentation_patterns['child'] = indentation_patterns['trans_unit'] + '  '

        return indentation_patterns

    except UnicodeDecodeError as e:
        raise MalformedXliffError(f"Error reading file {file_path}: {str(e)}. The file may not be a valid UTF-8 encoded file.")
    except IOError as e:
        raise MalformedXliffError(f"I/O error reading file {file_path}: {str(e)}")
    except Exception as e:
        if isinstance(e, (NoTransUnitsError, MalformedXliffError, EmptyXliffError, FileNotFoundError)):
            raise
        raise MalformedXliffError(f"Unexpected error processing file {file_path}: {str(e)}")

def trans_units_to_text(trans_units, indent_level=2, indentation_patterns=None):
    """
    Converts a list of processed trans-unit XML Element objects back to properly formatted text,
    preserving all attributes and maintaining consistent indentation.

    Args:
        trans_units (list): List of xml.etree.ElementTree.Element objects representing trans-units.
        indent_level (int, optional): Number of spaces to use for indentation. Defaults to 2.
            Only used if indentation_patterns is None.
        indentation_patterns (dict, optional): Dictionary with indentation patterns for different elements.
            If provided, indent_level is ignored.

    Returns:
        str: Properly formatted text representation of the trans-units.

    Raises:
        TypeError: If trans_units is not a list or contains non-Element objects.
    """
    if not isinstance(trans_units, list):
        raise TypeError("trans_units must be a list")

    if not all(isinstance(tu, ET.Element) for tu in trans_units):
        raise TypeError("All items in trans_units must be xml.etree.ElementTree.Element objects")

    # If the list is empty, return an empty string
    if not trans_units:
        return ""

    # Create a string buffer for the output
    output = []

    # Determine indentation to use
    if indentation_patterns:
        base_indent = indentation_patterns['trans_unit']
        child_indent = indentation_patterns['child']
    else:
        # Use the default calculation based on indent_level
        base_indent = ' ' * indent_level * 2
        child_indent = base_indent + ' ' * 2

    # Define common XML namespaces
    xml_ns = 'http://www.w3.org/XML/1998/namespace'
    xliff_ns = 'urn:oasis:names:tc:xliff:document:1.2'
    xsi_ns = 'http://www.w3.org/2001/XMLSchema-instance'

    # Create a namespace mapping for known namespaces
    ns_map = {
        f'{{{xml_ns}}}': 'xml:',
        f'{{{xliff_ns}}}': '',  # Default namespace doesn't need a prefix
        f'{{{xsi_ns}}}': 'xsi:'
    }

    # Function to get the prefixed name for a namespaced attribute or tag
    def get_prefixed_name(name):
        if not name.startswith('{'):
            return name

        for ns_uri, prefix in ns_map.items():
            if name.startswith(ns_uri):
                local_name = name.replace(ns_uri, '')
                return f"{prefix}{local_name}"

        # If namespace not in our map, extract and use a generic prefix
        ns_uri = name[1:name.find('}')]
        local_name = name[name.find('}')+1:]
        # Add to our map for future use
        prefix = f"ns{len(ns_map)-3}:"  # Generate a new prefix
        ns_map[f'{{{ns_uri}}}'] = prefix
        return f"{prefix}{local_name}"

    for tu in trans_units:
        # Convert the trans-unit to string with proper indentation
        # Handle attributes, including namespaced ones
        attrs = []
        for k, v in tu.attrib.items():
            # Get the prefixed attribute name
            prefixed_name = get_prefixed_name(k)
            attrs.append(f'{prefixed_name}="{v}"')

        attr_str = ' '.join(attrs)
        if attr_str:
            output.append(f"{base_indent}<trans-unit {attr_str}>")
        else:
            output.append(f"{base_indent}<trans-unit>")

        # Process each child element (source, target, notes, etc.)
        for child in tu:
            # Get the prefixed tag name
            if '}' in child.tag:
                tag_name = get_prefixed_name(child.tag)
            else:
                tag_name = child.tag

            # Process attributes, including namespaced ones
            child_attrs = []
            for k, v in child.attrib.items():
                # Get the prefixed attribute name
                prefixed_name = get_prefixed_name(k)
                child_attrs.append(f'{prefixed_name}="{v}"')

            child_attr_str = ' '.join(child_attrs)

            # Handle the element content
            if child.text is not None and child.text.strip():
                # Element with non-empty text content
                # Escape special characters in text
                escaped_text = child.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")
                if child_attr_str:
                    output.append(f"{child_indent}<{tag_name} {child_attr_str}>{escaped_text}</{tag_name}>")
                else:
                    output.append(f"{child_indent}<{tag_name}>{escaped_text}</{tag_name}>")
            else:
                # Empty element or element with only whitespace
                if len(child) == 0:  # No children
                    if child_attr_str:
                        # Use self-closing tag for empty elements with attributes
                        output.append(f"{child_indent}<{tag_name} {child_attr_str}/>")
                    else:
                        # Use self-closing tag for empty elements
                        output.append(f"{child_indent}<{tag_name}/>")
                else:
                    # Element with children but no text
                    if child_attr_str:
                        output.append(f"{child_indent}<{tag_name} {child_attr_str}>")
                    else:
                        output.append(f"{child_indent}<{tag_name}>")

            # Process any nested elements (uncommon but possible)
            if len(child) > 0:
                gc_indent = child_indent + ' ' * 2
                for grandchild in child:
                    # Get the prefixed tag name
                    if '}' in grandchild.tag:
                        gc_tag = get_prefixed_name(grandchild.tag)
                    else:
                        gc_tag = grandchild.tag

                    # Process attributes
                    gc_attrs = []
                    for k, v in grandchild.attrib.items():
                        # Get the prefixed attribute name
                        prefixed_name = get_prefixed_name(k)
                        gc_attrs.append(f'{prefixed_name}="{v}"')

                    gc_attr_str = ' '.join(gc_attrs)

                    if grandchild.text is not None and grandchild.text.strip():
                        # Escape special characters in text
                        escaped_text = grandchild.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")
                        if gc_attr_str:
                            output.append(f"{gc_indent}<{gc_tag} {gc_attr_str}>{escaped_text}</{gc_tag}>")
                        else:
                            output.append(f"{gc_indent}<{gc_tag}>{escaped_text}</{gc_tag}>")
                    else:
                        if len(grandchild) == 0:  # No children
                            if gc_attr_str:
                                output.append(f"{gc_indent}<{gc_tag} {gc_attr_str}/>")
                            else:
                                output.append(f"{gc_indent}<{gc_tag}/>")
                        else:
                            # Element with children but no text
                            if gc_attr_str:
                                output.append(f"{gc_indent}<{gc_tag} {gc_attr_str}>")
                            else:
                                output.append(f"{gc_indent}<{gc_tag}>")

                            # For deeper nesting, we would need a recursive approach
                            # This implementation handles up to 3 levels of nesting

                # Close the parent element if it has children
                output.append(f"{child_indent}</{tag_name}>")

        # Close the trans-unit tag
        output.append(f"{base_indent}</trans-unit>")

    # Join all lines with newlines
    return '\n'.join(output)

def parse_xliff_file(file_path):
    """
    Parses an XLIFF file to extract translation units.

    Args:
        file_path (str): Path to the XLIFF file.

    Returns:
        list of dict: A list of dictionaries, each representing a translation unit
                      with keys like 'id', 'source_text', and 'target_text'.

    Raises:
        FileNotFoundError: If the file does not exist.
        EmptyXliffError: If the file is empty.
        MalformedXliffError: If the XML is malformed.
        InvalidXliffError: If the root element is not <xliff>.
        NoTransUnitsError: If no trans-unit elements are found in the file.
        Exception: For any other unexpected errors during processing.
    """
    try:
        logger.info(f"Loading XLIFF file: {file_path}")
        xliff_doc = load_xliff_file(file_path)
        logger.debug("XLIFF file loaded successfully.")

        logger.info("Extracting trans-units...")
        trans_units = extract_trans_units_as_dict(xliff_doc)
        logger.info(f"Extracted {len(trans_units)} trans-units.")
        logger.debug(f"Extracted trans-units: {trans_units}")

        if not trans_units:
            logger.warning(f"No trans-units found in {file_path}")
            raise NoTransUnitsError(f"No trans-unit elements found in {file_path}")

        return trans_units

    except (FileNotFoundError, EmptyXliffError, MalformedXliffError, InvalidXliffError, NoTransUnitsError) as e:
        logger.error(f"Error during XLIFF parsing: {e}")
        raise # Re-raise the specific exception
    except Exception as e:
        logger.error(f"An unexpected error occurred during parsing: {e}", exc_info=True)
        raise MalformedXliffError(f"Unexpected error processing file {file_path}: {str(e)}")