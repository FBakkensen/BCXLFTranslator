import pytest
from src.bcxlftranslator.xliff_parser import identify_object_type

def test_identify_object_type_real_table_property():
    input_dict = {
        'id': 'Table 3928467216 - Property 2879900210',
        'source_text': '...',
        'target_text': '...'
    }
    result = identify_object_type(input_dict)
    assert result['object_type'] == 'Table'

def test_identify_object_type_real_table_field():
    input_dict = {
        'id': 'Table 3928467216 - Field 2185352090 - Property 2879900210',
        'source_text': '...',
        'target_text': '...'
    }
    result = identify_object_type(input_dict)
    assert result['object_type'] == 'Field'

def test_identify_object_type_real_profile_property():
    input_dict = {
        'id': 'Profile 1872758708 - Property 2879900210',
        'source_text': '...',
        'target_text': '...'
    }
    result = identify_object_type(input_dict)
    assert result['object_type'] == 'Profile'

def test_identify_object_type_real_page_action():
    input_dict = {
        'id': 'Page 21 - Action 1102601000 - Property Caption',
        'source_text': '...',
        'target_text': '...'
    }
    result = identify_object_type(input_dict)
    assert result['object_type'] == 'Page'