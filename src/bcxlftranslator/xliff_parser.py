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

# --- Logging Setup ---
# Basic configuration for logging within this module
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

# --- Main Parser Function ---

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

        return trans_units

    except (FileNotFoundError, EmptyXliffError, ET.ParseError, InvalidXliffError) as e:
        logger.error(f"Error during XLIFF parsing: {e}")
        raise # Re-raise the specific exception
    except Exception as e:
        logger.error(f"An unexpected error occurred during parsing: {e}", exc_info=True)
        raise # Re-raise any other unexpected exception