"""
Module for generating attribution notes for translations based on source.
"""
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

# Define default templates for different sources
DEFAULT_TEMPLATES = {
    "MICROSOFT": "Source: {source} (generated on {date} {time})",
    "GOOGLE": "Source: {source} (generated on {date} {time})",
    "MIXED": "Source: {source} - Microsoft Terminology ({microsoft_percentage}%), Google Translate ({google_percentage}%) (generated on {date} {time})"
}

def get_default_template(source):
    """
    Get the default template for a given source.

    Args:
        source (str): The source of the translation ('MICROSOFT', 'GOOGLE', or 'MIXED')

    Returns:
        str: The default template for the source

    Raises:
        ValueError: If source is not one of the valid options
    """
    if source not in DEFAULT_TEMPLATES:
        raise ValueError(f"Invalid translation source: {source}. Must be one of {list(DEFAULT_TEMPLATES.keys())}")

    return DEFAULT_TEMPLATES[source]

def generate_attribution_note(source, metadata=None, microsoft_percentage=None, google_percentage=None, template=None):
    """
    Generates an attribution note for a translation based on its source.

    Args:
        source (str): The source of the translation ('MICROSOFT', 'GOOGLE', or 'MIXED')
        metadata (dict, optional): Additional metadata to include in the note
        microsoft_percentage (int, optional): For MIXED source, percentage from Microsoft
        google_percentage (int, optional): For MIXED source, percentage from Google
        template (str, optional): Custom template string with placeholders

    Returns:
        str: Formatted attribution note

    Raises:
        ValueError: If source is not one of the valid options
        ValueError: If template is missing required placeholders
        KeyError: If template contains placeholders not found in metadata
    """
    # Validate the source parameter
    valid_sources = list(DEFAULT_TEMPLATES.keys())
    if source not in valid_sources:
        raise ValueError(f"Invalid translation source: {source}. Must be one of {valid_sources}")

    # Get template to use
    if template is None:
        template = get_default_template(source)

    # Ensure template contains the required {source} placeholder
    if "{source}" not in template:
        raise ValueError("Template must contain a {source} placeholder")

    # Prepare template data
    timestamp = datetime.now(timezone.utc)
    template_data = {
        "source": {
            "MICROSOFT": "Microsoft Terminology",
            "GOOGLE": "Google Translate",
            "MIXED": "Mixed Sources"
        }.get(source),
        "date": timestamp.strftime("%Y-%m-%d"),
        "time": timestamp.strftime("%H:%M:%S")
    }

    # Add source-specific data
    if source == "MIXED":
        if microsoft_percentage is None or google_percentage is None:
            raise ValueError("Mixed source requires both microsoft_percentage and google_percentage")
        template_data["microsoft_percentage"] = microsoft_percentage
        template_data["google_percentage"] = google_percentage

    # Add metadata if provided
    if metadata:
        # Format note to include metadata
        metadata_str = ", ".join([f"{key}: {value}" for key, value in metadata.items()])

        # Add metadata to template_data for use in custom templates
        template_data.update(metadata)

    # Format the template with the data
    try:
        note = template.format(**template_data)
    except KeyError as e:
        raise KeyError(f"Template contains placeholder {e} not found in metadata")

    # Add metadata as a suffix if we're using default templates
    if metadata and template in DEFAULT_TEMPLATES.values():
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