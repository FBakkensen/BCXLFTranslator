import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from main import match_case, match_single_text

def test_match_single_text_all_upper():
    assert match_single_text("TEST", "hello") == "HELLO"

def test_match_single_text_all_lower():
    assert match_single_text("test", "Hello") == "hello"

def test_match_single_text_first_capital():
    assert match_single_text("Test", "hello") == "Hello"

def test_match_single_text_empty():
    assert match_single_text("", "hello") == "hello"
    assert match_single_text("Test", "") == ""

def test_match_case_comma_list():
    source = "Insert, Modify, Delete"
    translated = "indsæt, ændre, slette"
    expected = "Indsæt, Ændre, Slette"
    assert match_case(source, translated) == expected

def test_match_case_preserve_whitespace():
    source = "Blank,  Item,Attribute,  Total"
    translated = "tom, vare, attribut, total"
    result = match_case(source, translated)
    assert result == "Tom,  Vare,Attribut,  Total"

def test_match_case_different_parts_count():
    source = "One, Two, Three"
    translated = "en og to, tre"  # Translation merged parts
    result = match_case(source, translated)
    # Should fall back to simple case matching when parts don't match
    assert result == "En og to, tre"

def test_match_single_text_title_case():
    # Should match title case for each word, including after dots
    assert match_single_text("Prod.Order", "prod.order") == "Prod.Order"
    assert match_single_text("Expand on Prod.Order", "udvid prod.order") == "Udvid Prod.Order"
    assert match_single_text("Test.Case", "test.case") == "Test.Case"
    # Should not change all uppercase or all lowercase
    assert match_single_text("PROD.ORDER", "prod.order") == "PROD.ORDER"
    assert match_single_text("prod.order", "PROD.ORDER") == "prod.order"