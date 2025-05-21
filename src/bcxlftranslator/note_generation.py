"""
Module for generating attribution notes for translations.
"""
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

# Define default template for Google Translate
DEFAULT_TEMPLATE = "Source: Google Translate (generated on {date} {time})"

def generate_attribution_note(source=None, metadata=None, template=None):
    """
    Generates an attribution note for a translation.

    Args:
        source (str, optional): The source of the translation (ignored, always uses Google Translate)
        metadata (dict, optional): Additional metadata to include in the note
        template (str, optional): Custom template string with placeholders

    Returns:
        str: Formatted attribution note

    Raises:
        ValueError: If template is missing required placeholders
        KeyError: If template contains placeholders not found in metadata
    """
    # Get template to use
    if template is None:
        template = DEFAULT_TEMPLATE

    # No need to check for specific placeholders anymore

    # Prepare template data
    timestamp = datetime.now(timezone.utc)
    template_data = {
        "date": timestamp.strftime("%Y-%m-%d"),
        "time": timestamp.strftime("%H:%M:%S")
    }

    # Add metadata if provided
    if metadata:
        # Add metadata to template_data for use in custom templates
        template_data.update(metadata)

    # Format the template with the data
    try:
        note = template.format(**template_data)
    except KeyError as e:
        raise KeyError(f"Template contains placeholder {e} not found in metadata")

    # Add metadata as a suffix if we're using the default template
    if metadata and template == DEFAULT_TEMPLATE:
        metadata_str = ", ".join([f"{key}: {value}" for key, value in metadata.items()])
        note += f" [{metadata_str}]"

    return note


def add_note_to_trans_unit(trans_unit, note_text, from_attribute="BCXLFTranslator", update_existing=True):
    """
    Adds an attribution note to an XLIFF trans-unit element.

    Args:
        trans_unit (ET.Element): The trans-unit element to add the note to
        note_text (str): The text content of the note
        from_attribute (str, optional): The 'from' attribute value for the note
        update_existing (bool, optional): Whether to update existing notes with the same 'from' attribute

    Returns:
        bool: True if the note was added or updated successfully, False otherwise

    Raises:
        ValueError: If trans_unit is None
    """
    if trans_unit is None:
        raise ValueError("trans_unit parameter cannot be None")
    if not note_text:
        return False

    import xml.etree.ElementTree as ET

    # Get namespace from trans_unit tag if present
    if trans_unit.tag.startswith("{"):
        ns = trans_unit.tag.split("}")[0][1:]
        note_tag = f"{{{ns}}}note"
    else:
        note_tag = "note"

    # Check if we need to update an existing note
    if update_existing:
        for child in trans_unit:
            if child.tag.endswith('note') and child.get('from') == from_attribute:
                child.text = note_text
                return True
    # Add a new note
    note_elem = ET.Element(note_tag)
    note_elem.set("from", from_attribute)
    note_elem.text = note_text
    trans_unit.append(note_elem)
    return True