import os
import xml.etree.ElementTree as ET
import logging

from .exceptions import InvalidXliffError, EmptyXliffError

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
        xml.etree.ElementTree.ParseError: If the XML is malformed.
        InvalidXliffError: If the root element is not <xliff>.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if os.path.getsize(file_path) == 0:
        raise EmptyXliffError(f"File is empty: {file_path}")

    try:
        tree = ET.parse(file_path)
    except ET.ParseError as e:
        raise

    root = tree.getroot()
    # Handle namespace in root tag
    # root.tag can be '{namespace}xliff', so check localname
    if root.tag.endswith('xliff'):
        return tree
    else:
        raise InvalidXliffError(f"Root element is not <xliff>: {root.tag}")

def extract_trans_units(xliff_doc):
    """
    Extract all trans-unit elements from the parsed XLIFF document.

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
import re

def identify_object_type(trans_unit_dict):
    """
    Identify the Business Central object type from a trans-unit dictionary's 'id' field.

    Args:
        trans_unit_dict (dict): A dictionary with at least an 'id' key.

    Returns:
        dict: The original dictionary, enriched with 'object_type' and 'context' keys.
    """
    id_str = trans_unit_dict.get('id', '')
    id_lower = id_str.lower()

    object_type = None

    # Field: Table X - Field Y - ... or Page X - Field Y - ...
    field_pattern = re.compile(r'^(table|page)\s+\d+\s*-\s*field\s+\d+\b', re.IGNORECASE)
    # Table: Table X - ... (not Field)
    table_pattern = re.compile(r'^table\s+\d+\b', re.IGNORECASE)
    # Page: Page X - ... (not Field)
    page_pattern = re.compile(r'^page\s+\d+\b', re.IGNORECASE)

    if field_pattern.match(id_str):
        object_type = 'Field'
    elif table_pattern.match(id_str):
        object_type = 'Table'
    elif page_pattern.match(id_str):
        object_type = 'Page'
    else:
        object_type = None

    # For now, context extraction is not implemented
    context = None

    trans_unit_dict['object_type'] = object_type
    trans_unit_dict['context'] = context
    return trans_unit_dict
def filter_terminology_candidates(enriched_trans_units):
    """
    Filter a list of enriched trans-unit dictionaries to select good terminology candidates.

    Args:
        enriched_trans_units (list of dict): List of trans-unit dicts, each with keys like
            'id', 'source_text', 'target_text', 'object_type', 'context'.

    Returns:
        list of dict: New list containing only the dictionaries that meet the filtering criteria.
    """
    allowed_types = {'Table', 'Page', 'Field'}
    filtered = []
    for tu in enriched_trans_units:
        if tu.get('object_type') not in allowed_types:
            continue
        source = tu.get('source_text')
        target = tu.get('target_text')
        if not source or not target:
            continue
        if len(source) <= 2:
            continue
        filtered.append(tu)
    return filtered
# --- Logging Setup ---
# Basic configuration for logging within this module
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

# --- Main Parser Function ---

def parse_xliff_for_terminology(file_path):
    """
    Parses an XLIFF file to extract potential terminology candidates.

    Orchestrates the loading, extraction, identification, and filtering steps.

    Args:
        file_path (str): Path to the XLIFF file.

    Returns:
        list of dict: A list of dictionaries, each representing a terminology
                      candidate with keys like 'id', 'source_text', 'target_text',
                      'object_type', and 'context'.

    Raises:
        FileNotFoundError: If the file does not exist.
        EmptyXliffError: If the file is empty.
        xml.etree.ElementTree.ParseError: If the XML is malformed.
        InvalidXliffError: If the root element is not <xliff>.
        Exception: For any other unexpected errors during processing.
    """
    try:
        logger.info(f"Loading XLIFF file: {file_path}")
        xliff_doc = load_xliff_file(file_path)
        logger.debug("XLIFF file loaded successfully.")

        logger.info("Extracting trans-units...")
        trans_units = extract_trans_units(xliff_doc)
        logger.info(f"Extracted {len(trans_units)} trans-units.")
        logger.debug(f"Extracted trans-units: {trans_units}")

        logger.info("Identifying object types...")
        enriched_trans_units = []
        for tu in trans_units:
            enriched_tu = identify_object_type(tu.copy()) # Use copy to avoid modifying original list items
            enriched_trans_units.append(enriched_tu)
            logger.debug(f"Identified object type for unit {tu.get('id')}: {enriched_tu.get('object_type')}")
        logger.debug("Object type identification complete.")

        logger.info("Filtering terminology candidates...")
        candidates = filter_terminology_candidates(enriched_trans_units)
        logger.info(f"Filtered to {len(candidates)} terminology candidates.")
        logger.debug(f"Filtered candidates: {candidates}")

        return candidates

    except (FileNotFoundError, EmptyXliffError, ET.ParseError, InvalidXliffError) as e:
        logger.error(f"Error during XLIFF parsing: {e}")
        raise # Re-raise the specific exception
    except Exception as e:
        logger.error(f"An unexpected error occurred during parsing: {e}", exc_info=True)
        raise # Re-raise any other unexpected exception