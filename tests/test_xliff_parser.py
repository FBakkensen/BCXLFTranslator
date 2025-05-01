import pytest
from src.bcxlftranslator.xliff_parser import identify_object_type

def test_identify_object_type_page_control():
    input_data = {'id': 'Page 141867820 - Control 3794685984 - Property 1295455071'}
    result = identify_object_type(input_data)
    assert result['object_type'] == 'Control'

def test_identify_object_type_page_namedtype():
    input_data = {'id': 'Page 2563671150 - NamedType 3114637384'}
    result = identify_object_type(input_data)
    assert result['object_type'] == 'NamedType'

def test_identify_object_type_table_namedtype():
    input_data = {'id': 'Table 3416302668 - NamedType 904652358'}
    result = identify_object_type(input_data)
    assert result['object_type'] == 'NamedType'

def test_identify_object_type_codeunit_namedtype():
    input_data = {'id': 'Codeunit 3055525730 - NamedType 1010428964'}
    result = identify_object_type(input_data)
    assert result['object_type'] == 'NamedType'

def test_identify_object_type_query_property():
    input_data = {'id': 'Query 149526480 - Property 1064389655'}
    result = identify_object_type(input_data)
    assert result['object_type'] == 'Query'

def test_identify_object_type_query_column():
    input_data = {'id': 'Query 149526480 - QueryColumn 2598849494 - Property 2879900210'}
    result = identify_object_type(input_data)
    assert result['object_type'] == 'QueryColumn'

def test_identify_object_type_page_control_special_chars_1():
    input_data = {'id': 'Page 141867820 - Control Aggregation[2]5D; - Property 62802879'}
    result = identify_object_type(input_data)
    assert result['object_type'] == 'Control'

def test_identify_object_type_page_control_special_chars_2():
    input_data = {'id': 'Page 141867820 - Control ChartTypeReduced[3]5D; - Property 4227316127'}

def test_identify_object_type_page_control_angle_brackets():
    input_data = {'id': 'Page 141867820 - Control <Control35> - Property 2879900210', 'source_text': 'Test', 'target_text': 'Test'}
    result = identify_object_type(input_data)
    assert result['object_type'] == 'Control'
    result = identify_object_type(input_data)
    assert result['object_type'] == 'Control'