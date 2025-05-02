import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.bcxlftranslator.main import match_case, match_single_text

def test_match_single_text_all_upper():
    """
    Given a source text in all uppercase
    When match_single_text is called with this source and a lowercase target
    Then it should return the target text converted to uppercase
    """
    assert match_single_text("TEST", "hello") == "HELLO"

def test_match_single_text_all_lower():
    """
    Given a source text in all lowercase
    When match_single_text is called with this source and a capitalized target
    Then it should return the target text converted to lowercase
    """
    assert match_single_text("test", "Hello") == "hello"

def test_match_single_text_first_capital():
    """
    Given a source text with only first letter capitalized
    When match_single_text is called with this source and a lowercase target
    Then it should return the target text with only first letter capitalized
    """
    assert match_single_text("Test", "hello") == "Hello"

def test_match_single_text_empty():
    """
    Given empty source or target text
    When match_single_text is called
    Then it should handle these edge cases appropriately
    """
    assert match_single_text("", "hello") == "hello"
    assert match_single_text("Test", "") == ""

def test_match_case_comma_list():
    """
    Given a source text with multiple comma-separated words with first letter capitalized
    When match_case is called with this source and a lowercase target containing comma-separated words
    Then it should capitalize the first letter of each word in the target text
    """
    source = "Insert, Modify, Delete"
    translated = "indsæt, ændre, slette"
    expected = "Indsæt, Ændre, Slette"
    assert match_case(source, translated) == expected

def test_match_case_preserve_whitespace():
    """
    Given a source text with varied whitespace between commas
    When match_case is called with this source and a target with uniform whitespace
    Then it should preserve the original whitespace pattern from the source
    """
    source = "Blank,  Item,Attribute,  Total"
    translated = "tom, vare, attribut, total"
    result = match_case(source, translated)
    assert result == "Tom,  Vare,Attribut,  Total"

def test_match_case_different_parts_count():
    """
    Given source and target texts with different numbers of comma-separated parts
    When match_case is called
    Then it should fall back to simple case matching for the entire string
    """
    source = "One, Two, Three"
    translated = "en og to, tre"  # Translation merged parts
    result = match_case(source, translated)
    # Should fall back to simple case matching when parts don't match
    assert result == "En og to, tre"

def test_match_single_text_title_case():
    """
    Given source texts with special title case formats including periods
    When match_single_text is called
    Then it should correctly handle title case for compound words separated by periods
    """
    # Should match title case for each word, including after dots
    assert match_single_text("Prod.Order", "prod.order") == "Prod.Order"
    assert match_single_text("Expand on Prod.Order", "udvid prod.order") == "Udvid Prod.Order"
    assert match_single_text("Test.Case", "test.case") == "Test.Case"
    # Should not change all uppercase or all lowercase
    assert match_single_text("PROD.ORDER", "prod.order") == "PROD.ORDER"
    assert match_single_text("prod.order", "PROD.ORDER") == "prod.order"