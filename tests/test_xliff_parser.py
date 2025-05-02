import os
import sys
import pytest
import xml.etree.ElementTree as ET
import logging # For caplog

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from bcxlftranslator.xliff_parser import (
    load_xliff_file,
    identify_object_type,
    filter_terminology_candidates,
    parse_xliff_for_terminology # New function
)
from bcxlftranslator.exceptions import InvalidXliffError, EmptyXliffError

@pytest.fixture
def invalid_xliff_file(tmp_path):
    file = tmp_path / "invalid.xlf"
    # Add namespace to root to simulate a non-xliff root with namespace
    file.write_text("<ns:root xmlns:ns='http://example.com/ns'>Not xliff root</ns:root>", encoding="utf-8")
    return str(file)

@pytest.fixture
def empty_file(tmp_path):
    file = tmp_path / "empty.xlf"
    file.write_text("", encoding="utf-8")
    return str(file)

@pytest.fixture
def malformed_xml_file(tmp_path):
    file = tmp_path / "malformed.xlf"
    file.write_text("<xliff><unclosed>Oops</xliff>", encoding="utf-8")
    return str(file)

def test_load_valid_xliff():
    """
    Given a valid XLIFF file
    When the load_xliff_file function is called
    Then it should return a valid ElementTree with an xliff root element
    """
    # Use existing fixture file for valid XLIFF
    valid_file = os.path.join("tests", "fixtures", "test.xlf")
    tree = load_xliff_file(valid_file)
    root = tree.getroot()
    # root.tag may include namespace, so check localname
    assert root.tag.endswith("xliff")

def test_load_nonexistent_file():
    """
    Given a file path that does not exist
    When the load_xliff_file function is called
    Then it should raise a FileNotFoundError
    """
    with pytest.raises(FileNotFoundError):
        load_xliff_file("nonexistent_file.xlf")

def test_load_invalid_xliff(invalid_xliff_file):
    """
    Given an XML file that is not a valid XLIFF file
    When the load_xliff_file function is called
    Then it should raise an InvalidXliffError
    """
    with pytest.raises(InvalidXliffError):
        load_xliff_file(invalid_xliff_file)

def test_load_empty_file(empty_file):
    """
    Given an empty file
    When the load_xliff_file function is called
    Then it should raise an EmptyXliffError
    """
    with pytest.raises(EmptyXliffError):
        load_xliff_file(empty_file)

def test_load_malformed_xml(malformed_xml_file):
    """
    Given a malformed XML file
    When the load_xliff_file function is called
    Then it should raise a ParseError
    """
    with pytest.raises(ET.ParseError):
        load_xliff_file(malformed_xml_file)
import io
import xml.etree.ElementTree as ET
import pytest

from bcxlftranslator.xliff_parser import extract_trans_units

@pytest.fixture
def simple_xliff_doc():
    xliff_str = '''<?xml version="1.0" encoding="UTF-8"?>
    <xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
      <file source-language="en" target-language="fr" datatype="plaintext" original="file.ext">
        <body>
          <trans-unit id="1">
            <source>Hello</source>
            <target>Bonjour</target>
          </trans-unit>
          <trans-unit id="2">
            <source>World</source>
            <target>Monde</target>
          </trans-unit>
        </body>
      </file>
    </xliff>'''
    root = ET.fromstring(xliff_str)
    return ET.ElementTree(root)

@pytest.fixture
def empty_source_target_xliff_doc():
    xliff_str = '''<?xml version="1.0" encoding="UTF-8"?>
    <xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
      <file>
        <body>
          <trans-unit id="1">
            <source></source>
            <target></target>
          </trans-unit>
        </body>
      </file>
    </xliff>'''
    root = ET.fromstring(xliff_str)
    return ET.ElementTree(root)

@pytest.fixture
def missing_source_target_xliff_doc():
    xliff_str = '''<?xml version="1.0" encoding="UTF-8"?>
    <xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
      <file>
        <body>
          <trans-unit id="1">
            <!-- no source or target -->
          </trans-unit>
          <trans-unit id="2">
            <source>Only source</source>
          </trans-unit>
          <trans-unit id="3">
            <target>Only target</target>
          </trans-unit>
        </body>
      </file>
    </xliff>'''
    root = ET.fromstring(xliff_str)
    return ET.ElementTree(root)

@pytest.fixture
def complex_xliff_doc():
    xliff_str = '''<?xml version="1.0" encoding="UTF-8"?>
    <xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
      <file>
        <body>
          <group id="g1">
            <trans-unit id="1">
              <source>Group source</source>
              <target>Groupe cible</target>
            </trans-unit>
          </group>
          <trans-unit id="2">
            <source>Outside group</source>
            <target>En dehors du groupe</target>
          </trans-unit>
        </body>
      </file>
    </xliff>'''
    root = ET.fromstring(xliff_str)
    return ET.ElementTree(root)

def test_extract_trans_units_simple(simple_xliff_doc):
    """
    Given a simple XLIFF document with two translation units
    When the extract_trans_units function is called
    Then it should return a list of two translation units with correct source and target texts
    """
    result = extract_trans_units(simple_xliff_doc)
    assert len(result) == 2
    assert result[0] == {'id': '1', 'source_text': 'Hello', 'target_text': 'Bonjour'}
    assert result[1] == {'id': '2', 'source_text': 'World', 'target_text': 'Monde'}

def test_extract_trans_units_empty_source_target(empty_source_target_xliff_doc):
    """
    Given an XLIFF document with empty source and target elements
    When the extract_trans_units function is called
    Then it should return a translation unit with empty strings for source and target texts
    """
    result = extract_trans_units(empty_source_target_xliff_doc)
    assert len(result) == 1
    assert result[0]['source_text'] == ""
    assert result[0]['target_text'] == ""

def test_extract_trans_units_missing_source_target(missing_source_target_xliff_doc):
    """
    Given an XLIFF document with missing source and target elements
    When the extract_trans_units function is called
    Then it should return translation units with None values for missing elements
    """
    result = extract_trans_units(missing_source_target_xliff_doc)
    assert len(result) == 3
    assert result[0] == {'id': '1', 'source_text': None, 'target_text': None}
    assert result[1] == {'id': '2', 'source_text': 'Only source', 'target_text': None}
    assert result[2] == {'id': '3', 'source_text': None, 'target_text': 'Only target'}

def test_extract_trans_units_complex_structure(complex_xliff_doc):
    """
    Given an XLIFF document with a complex nested structure
    When the extract_trans_units function is called
    Then it should extract all translation units regardless of nesting
    """
    result = extract_trans_units(complex_xliff_doc)
    assert len(result) == 2
    assert any(tu['id'] == '1' and tu['source_text'] == 'Group source' and tu['target_text'] == 'Groupe cible' for tu in result)
    assert any(tu['id'] == '2' and tu['source_text'] == 'Outside group' and tu['target_text'] == 'En dehors du groupe' for tu in result)
from bcxlftranslator.xliff_parser import identify_object_type

@pytest.fixture
def sample_trans_units_for_object_type():
    return [
        # Table property
        {'id': 'Table 18 - Property Name', 'source_text': 'Customer', 'target_text': 'Kunde'},
        # Table field
        {'id': 'Table 18 - Field 2 - Property Caption', 'source_text': 'No.', 'target_text': 'Nr.'},
        # Page property
        {'id': 'Page 21 - Property Caption', 'source_text': 'Customer Card', 'target_text': 'Kundekort'},
        # Page action
        {'id': 'Page 21 - Action 1102601000 - Property Caption', 'source_text': 'Post', 'target_text': 'Bogfør'},
        # Unrecognized pattern
        {'id': 'Random String - Something Else', 'source_text': 'Test', 'target_text': 'Test'},
        # Field with different pattern
        {'id': 'Table 27 - Field 3 - Property Description', 'source_text': 'Name', 'target_text': 'Navn'},
        # Page field
        {'id': 'Page 22 - Field 5 - Property Caption', 'source_text': 'Address', 'target_text': 'Adresse'},
        # Table only
        {'id': 'Table 5050 - Property Caption', 'source_text': 'Contact', 'target_text': 'Kontakt'},
        # Page only
        {'id': 'Page 5051 - Property Caption', 'source_text': 'Contact Card', 'target_text': 'Kontaktkort'},
        # Edge: lowercase
        {'id': 'table 18 - property name', 'source_text': 'Customer', 'target_text': 'Kunde'},
    ]

def test_identify_object_type_table_property(sample_trans_units_for_object_type):
    """
    Given a translation unit with a Table property ID pattern
    When the identify_object_type function is called
    Then it should identify the object type as 'Table' with no context
    """
    tu = sample_trans_units_for_object_type[0].copy()
    result = identify_object_type(tu)
    assert result['object_type'] == 'Table'
    assert result['context'] is None

def test_identify_object_type_table_field(sample_trans_units_for_object_type):
    """
    Given a translation unit with a Table field ID pattern
    When the identify_object_type function is called
    Then it should identify the object type as 'Field' with no context
    """
    tu = sample_trans_units_for_object_type[1].copy()
    result = identify_object_type(tu)
    assert result['object_type'] == 'Field'
    assert result['context'] is None

def test_identify_object_type_page_property(sample_trans_units_for_object_type):
    """
    Given a translation unit with a Page property ID pattern
    When the identify_object_type function is called
    Then it should identify the object type as 'Page' with no context
    """
    tu = sample_trans_units_for_object_type[2].copy()
    result = identify_object_type(tu)
    assert result['object_type'] == 'Page'
    assert result['context'] is None

def test_identify_object_type_page_action(sample_trans_units_for_object_type):
    """
    Given a translation unit with a Page action ID pattern
    When the identify_object_type function is called
    Then it should identify the object type as 'Page' with no context
    """
    tu = sample_trans_units_for_object_type[3].copy()
    result = identify_object_type(tu)
    assert result['object_type'] == 'Page'
    assert result['context'] is None

def test_identify_object_type_unrecognized(sample_trans_units_for_object_type):
    """
    Given a translation unit with an unrecognized ID pattern
    When the identify_object_type function is called
    Then it should return None for both object_type and context
    """
    tu = sample_trans_units_for_object_type[4].copy()
    result = identify_object_type(tu)
    assert result['object_type'] is None
    assert result['context'] is None

def test_identify_object_type_field_description(sample_trans_units_for_object_type):
    """
    Given a translation unit with a field description ID pattern
    When the identify_object_type function is called
    Then it should identify the object type as 'Field' with no context
    """
    tu = sample_trans_units_for_object_type[5].copy()
    result = identify_object_type(tu)
    assert result['object_type'] == 'Field'
    assert result['context'] is None

def test_identify_object_type_page_field(sample_trans_units_for_object_type):
    """
    Given a translation unit with a Page field ID pattern
    When the identify_object_type function is called
    Then it should identify the object type as 'Field' with no context
    """
    tu = sample_trans_units_for_object_type[6].copy()
    result = identify_object_type(tu)
    assert result['object_type'] == 'Field'
    assert result['context'] is None

def test_identify_object_type_table_only(sample_trans_units_for_object_type):
    """
    Given a translation unit with a Table only ID pattern
    When the identify_object_type function is called
    Then it should identify the object type as 'Table' with no context
    """
    tu = sample_trans_units_for_object_type[7].copy()
    result = identify_object_type(tu)
    assert result['object_type'] == 'Table'
    assert result['context'] is None

def test_identify_object_type_page_only(sample_trans_units_for_object_type):
    """
    Given a translation unit with a Page only ID pattern
    When the identify_object_type function is called
    Then it should identify the object type as 'Page' with no context
    """
    tu = sample_trans_units_for_object_type[8].copy()
    result = identify_object_type(tu)
    assert result['object_type'] == 'Page'
    assert result['context'] is None

def test_identify_object_type_case_insensitive(sample_trans_units_for_object_type):
    """
    Given a translation unit with a lowercase ID pattern
    When the identify_object_type function is called
    Then it should identify the object type case-insensitively
    """
    tu = sample_trans_units_for_object_type[9].copy()
    result = identify_object_type(tu)
    assert result['object_type'] == 'Table'
from bcxlftranslator.xliff_parser import filter_terminology_candidates

@pytest.fixture
def enriched_trans_units_sample():
    return [
        # Good candidates
        {'id': 'Table 18 - Property Name', 'source_text': 'Customer', 'target_text': 'Kunde', 'object_type': 'Table', 'context': None},
        {'id': 'Page 21 - Property Caption', 'source_text': 'Customer Card', 'target_text': 'Kundekort', 'object_type': 'Page', 'context': None},
        {'id': 'Table 18 - Field 2 - Property Caption', 'source_text': 'No.', 'target_text': 'Nr.', 'object_type': 'Field', 'context': None},
        # Excluded by object_type
        {'id': 'Random String - Something Else', 'source_text': 'Test', 'target_text': 'Test', 'object_type': None, 'context': None},
        {'id': 'Other 1', 'source_text': 'Other', 'target_text': 'Andet', 'object_type': 'Action', 'context': None},
        # Excluded by empty/None source/target
        {'id': 'Table 19 - Property Name', 'source_text': '', 'target_text': 'Kunde', 'object_type': 'Table', 'context': None},
        {'id': 'Table 20 - Property Name', 'source_text': None, 'target_text': 'Kunde', 'object_type': 'Table', 'context': None},
        {'id': 'Page 22 - Property Caption', 'source_text': 'Customer Card', 'target_text': '', 'object_type': 'Page', 'context': None},
        {'id': 'Page 23 - Property Caption', 'source_text': 'Customer Card', 'target_text': None, 'object_type': 'Page', 'context': None},
        # Excluded by short source_text
        {'id': 'Table 21 - Property Name', 'source_text': 'A', 'target_text': 'B', 'object_type': 'Table', 'context': None},
        {'id': 'Page 24 - Property Caption', 'source_text': 'AB', 'target_text': 'CD', 'object_type': 'Page', 'context': None},
    ]

def test_filter_includes_table_page_field(enriched_trans_units_sample):
    """
    Given a collection of enriched translation units with various object types
    When the filter_terminology_candidates function is called
    Then it should include only Table, Page, and Field object types
    """
    result = filter_terminology_candidates(enriched_trans_units_sample)
    object_types = [tu['object_type'] for tu in result]
    assert 'Table' in object_types
    assert 'Page' in object_types
    assert 'Field' in object_types

def test_filter_excludes_none_object_type(enriched_trans_units_sample):
    """
    Given a collection of enriched translation units including some with None object_type
    When the filter_terminology_candidates function is called
    Then it should exclude units with None object_type
    """
    result = filter_terminology_candidates(enriched_trans_units_sample)
    for tu in result:
        assert tu['object_type'] is not None
        assert tu['object_type'] in ('Table', 'Page', 'Field')

def test_filter_excludes_empty_or_none_source_target(enriched_trans_units_sample):
    """
    Given a collection of enriched translation units including some with empty or None source/target
    When the filter_terminology_candidates function is called
    Then it should exclude units with empty or None source/target texts
    """
    result = filter_terminology_candidates(enriched_trans_units_sample)
    for tu in result:
        assert tu['source_text'] not in (None, '')
        assert tu['target_text'] not in (None, '')

def test_filter_excludes_short_source_text(enriched_trans_units_sample):
    """
    Given a collection of enriched translation units including some with short source_text
    When the filter_terminology_candidates function is called
    Then it should exclude units with source_text length <= 2
    """
    result = filter_terminology_candidates(enriched_trans_units_sample)
    for tu in result:
        assert tu['source_text'] is not None and len(tu['source_text']) > 2

def test_filter_empty_input():
    """
    Given an empty list of enriched translation units
    When the filter_terminology_candidates function is called
    Then it should return an empty list
    """
    assert filter_terminology_candidates([]) == []

def test_filter_all_excluded():
    """
    Given a collection where all units should be excluded
    When the filter_terminology_candidates function is called
    Then it should return an empty list
    """
    # All should be excluded (wrong object_type, empty/None text, or too short)
    bad_candidates = [
        {'id': '1', 'source_text': '', 'target_text': 'A', 'object_type': None, 'context': None},
        {'id': '2', 'source_text': None, 'target_text': '', 'object_type': 'Action', 'context': None},
        {'id': '3', 'source_text': 'A', 'target_text': 'B', 'object_type': 'Table', 'context': None},
    ]
    assert filter_terminology_candidates(bad_candidates) == []

def test_filter_mixed_candidates():
    """
    Given a mixed collection of valid and invalid candidates
    When the filter_terminology_candidates function is called
    Then it should return only the valid candidates
    """
    candidates = [
        {'id': '1', 'source_text': 'Customer', 'target_text': 'Kunde', 'object_type': 'Table', 'context': None},
        {'id': '2', 'source_text': '', 'target_text': 'Kunde', 'object_type': 'Table', 'context': None},
        {'id': '3', 'source_text': 'A', 'target_text': 'B', 'object_type': 'Page', 'context': None},
        {'id': '4', 'source_text': 'Customer Card', 'target_text': 'Kundekort', 'object_type': 'Page', 'context': None},
        {'id': '5', 'source_text': 'Test', 'target_text': 'Test', 'object_type': None, 'context': None},
    ]
# --- Fixtures for Integration Tests ---

@pytest.fixture
def simple_integration_xliff_file(tmp_path):
    content = """<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en-US" target-language="da-DK" datatype="xml">
    <body>
      <trans-unit id="Table 18 - Field 2 - Property Caption">
        <source>No.</source>
        <target>Nr.</target>
        <note from="Developer" annotates="general" priority="2">ID=FIELD, No.; Short for Number</note>
      </trans-unit>
      <trans-unit id="Page 21 - Property Caption">
        <source>Customer Card</source>
        <target>Kundekort</target>
        <note from="Developer" annotates="general" priority="2">ID=PAGE, Caption</note>
      </trans-unit>
      <trans-unit id="Table 18 - Property Name">
        <source>Customer</source>
        <target>Kunde</target>
        <note from="Developer" annotates="general" priority="2">ID=TABLE, Name</note>
      </trans-unit>
      <trans-unit id="Unrelated ID">
        <source>Ignore Me</source>
        <target>Ignorer Mig</target>
      </trans-unit>
      <trans-unit id="Table 19 - Property Name">
        <source>A</source> <!-- Too short -->
        <target>B</target>
      </trans-unit>
    </body>
  </file>
</xliff>"""
    file = tmp_path / "simple_integration.xlf"
    file.write_text(content, encoding="utf-8")
    return str(file)

@pytest.fixture
def no_candidates_xliff_file(tmp_path):
    content = """<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en-US" target-language="da-DK" datatype="xml">
    <body>
      <trans-unit id="Unrelated ID">
        <source>Ignore Me</source>
        <target>Ignorer Mig</target>
      </trans-unit>
      <trans-unit id="Table 19 - Property Name">
        <source>A</source> <!-- Too short -->
        <target>B</target>
      </trans-unit>
      <trans-unit id="Page 20 - Property Caption">
        <source></source> <!-- Empty source -->
        <target>Tom</target>
      </trans-unit>
    </body>
  </file>
</xliff>"""
    file = tmp_path / "no_candidates.xlf"
    file.write_text(content, encoding="utf-8")
    return str(file)

# --- Integration Tests for parse_xliff_for_terminology ---

def test_parse_xliff_integration_simple(simple_integration_xliff_file):
    """
    Given a simple XLIFF file with valid terminology candidates
    When the parse_xliff_for_terminology function is called
    Then it should return the correct number of terminology candidates with expected properties
    """
    result = parse_xliff_for_terminology(simple_integration_xliff_file)
    assert len(result) == 3
    # Check if the expected candidates are present (order might vary)
    expected_ids = {
        "Table 18 - Field 2 - Property Caption",
        "Page 21 - Property Caption",
        "Table 18 - Property Name"
    }
    result_ids = {tu['id'] for tu in result}
    assert result_ids == expected_ids

    # Check structure of one candidate
    candidate = next(tu for tu in result if tu['id'] == "Table 18 - Field 2 - Property Caption")
    assert candidate['source_text'] == 'No.'
    assert candidate['target_text'] == 'Nr.'
    assert candidate['object_type'] == 'Field'
    assert candidate['context'] is None # Context extraction not implemented yet

def test_parse_xliff_integration_no_candidates(no_candidates_xliff_file):
    """
    Given an XLIFF file with no valid terminology candidates
    When the parse_xliff_for_terminology function is called
    Then it should return an empty list
    """
    result = parse_xliff_for_terminology(no_candidates_xliff_file)
    assert result == []

def test_parse_xliff_integration_file_not_found():
    """
    Given a file path that does not exist
    When the parse_xliff_for_terminology function is called
    Then it should raise a FileNotFoundError
    """
    with pytest.raises(FileNotFoundError):
        parse_xliff_for_terminology("non_existent_file.xlf")

def test_parse_xliff_integration_invalid_xliff(invalid_xliff_file):
    """
    Given an invalid XLIFF file
    When the parse_xliff_for_terminology function is called
    Then it should raise an InvalidXliffError
    """
    with pytest.raises(InvalidXliffError):
        parse_xliff_for_terminology(invalid_xliff_file)

def test_parse_xliff_integration_empty_file(empty_file):
    """
    Given an empty file
    When the parse_xliff_for_terminology function is called
    Then it should raise an EmptyXliffError
    """
    with pytest.raises(EmptyXliffError):
        parse_xliff_for_terminology(empty_file)

def test_parse_xliff_integration_malformed_xml(malformed_xml_file):
    """
    Given a malformed XML file
    When the parse_xliff_for_terminology function is called
    Then it should raise a ParseError
    """
    with pytest.raises(ET.ParseError):
        parse_xliff_for_terminology(malformed_xml_file)

def test_parse_xliff_integration_logging(simple_integration_xliff_file, caplog):
    """
    Given a simple XLIFF file
    When the parse_xliff_for_terminology function is called
    Then it should log key steps of the process
    """
    caplog.set_level(logging.INFO)
    parse_xliff_for_terminology(simple_integration_xliff_file)

    assert "Loading XLIFF file:" in caplog.text
    assert "Extracting trans-units..." in caplog.text
    assert "Extracted 5 trans-units." in caplog.text # Based on simple_integration_xliff_file
    assert "Identifying object types..." in caplog.text
    assert "Filtering terminology candidates..." in caplog.text
    assert "Filtered to 3 terminology candidates." in caplog.text # Based on simple_integration_xliff_file