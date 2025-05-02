import os
import sys
import sqlite3
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from bcxlftranslator.terminology_db import TerminologyDatabase, SCHEMA_VERSION
from bcxlftranslator.exceptions import TerminologyDBError

def test_class_instantiation_and_connection():
    """
    Given a TerminologyDatabase is instantiated with an in-memory database
    When the connection is checked
    Then it should be a valid SQLite connection
    """
    db = TerminologyDatabase(":memory:")
    assert isinstance(db.conn, sqlite3.Connection)
    db.close()

def test_context_manager_opens_and_closes():
    """
    Given a TerminologyDatabase is used as a context manager
    When the context block is entered and exited
    Then the connection should be open during the block and closed after
    """
    with TerminologyDatabase(":memory:") as db:
        assert isinstance(db.conn, sqlite3.Connection)
        assert not db._closed
    # After context, connection should be closed
    assert db._closed

def test_explicit_close():
    """
    Given an open TerminologyDatabase
    When the close method is called
    Then the database connection should be closed
    """
    db = TerminologyDatabase(":memory:")
    db.close()
    assert db._closed

def test_double_close_safe():
    """
    Given an already closed TerminologyDatabase
    When the close method is called again
    Then it should not raise an exception
    """
    db = TerminologyDatabase(":memory:")
    db.close()
    db.close()  # Should not raise

def test_create_database_success():
    """
    Given a new TerminologyDatabase is created
    When it's initialized
    Then it should have a valid connection
    """
    with TerminologyDatabase(":memory:") as db:
        assert isinstance(db.conn, sqlite3.Connection)

def test_schema_validation():
    """
    Given a new TerminologyDatabase
    When the database schema is examined
    Then it should have the expected tables and columns with correct types
    """
    with TerminologyDatabase(":memory:") as db:
        cursor = db.conn.cursor()

        # Check Terms table columns
        cursor.execute("PRAGMA table_info(Terms);")
        terms_columns = cursor.fetchall()
        terms_columns_dict = {col[1]: col[2] for col in terms_columns}
        expected_terms_columns = {
            "id": "INTEGER",
            "source_term": "TEXT",
            "target_term": "TEXT",
            "context": "TEXT",
            "object_type": "TEXT",
            "language": "TEXT"
        }
        for col, col_type in expected_terms_columns.items():
            assert col in terms_columns_dict
            assert terms_columns_dict[col] == col_type

        # Check Metadata table columns
        cursor.execute("PRAGMA table_info(Metadata);")
        metadata_columns = cursor.fetchall()
        metadata_columns_dict = {col[1]: col[2] for col in metadata_columns}
        expected_metadata_columns = {
            "id": "INTEGER",
            "source_file": "TEXT",
            "version": "TEXT",
            "language_pair": "TEXT",
            "import_date": "TEXT"
        }
        for col, col_type in expected_metadata_columns.items():
            assert col in metadata_columns_dict
            assert metadata_columns_dict[col] == col_type

def test_indexes_created():
    """
    Given a new TerminologyDatabase
    When the database indexes are examined
    Then it should have the expected indexes on the correct columns
    """
    with TerminologyDatabase(":memory:") as db:
        cursor = db.conn.cursor()
        cursor.execute("PRAGMA index_list(Terms);")
        indexes = cursor.fetchall()
        index_names = [index[1] for index in indexes]
        expected_indexes = {"idx_terms_source_term", "idx_terms_language"}
        assert expected_indexes.issubset(set(index_names))
        # Optionally check index columns
        for index_name in expected_indexes:
            cursor.execute(f"PRAGMA index_info({index_name});")
            index_info = cursor.fetchall()
            assert len(index_info) == 1
            col_name = index_info[0][2]
            assert col_name in ["source_term", "language"]

def test_add_term_success():
    """
    Given a TerminologyDatabase
    When a term is added with all required fields
    Then the term should be retrievable from the database with all the correct attributes
    """
    with TerminologyDatabase(":memory:") as db:
        db.add_term("hello", "hola", "es", context="greeting", object_type="word")
        term = db.get_term("hello", "es")
        assert term is not None
        assert term["source_term"] == "hello"
        assert term["target_term"] == "hola"
        assert term["language"] == "es"
        assert term["context"] == "greeting"
        assert term["object_type"] == "word"

def test_get_term_nonexistent():
    """
    Given a TerminologyDatabase
    When a non-existent term is requested
    Then None should be returned
    """
    with TerminologyDatabase(":memory:") as db:
        term = db.get_term("nonexistent", "en")
        assert term is None

def test_lookup_terms_language_only():
    """
    Given a TerminologyDatabase with multiple terms in different languages
    When terms are looked up with only a language filter
    Then all terms for that language should be returned
    """
    with TerminologyDatabase(":memory:") as db:
        db.add_term("hello", "hola", "es", context="greeting", object_type="word")
        db.add_term("world", "mundo", "es", context="noun", object_type="word")
        db.add_term("test", "prueba", "es", context="noun", object_type="word")
        db.add_term("hello", "bonjour", "fr", context="greeting", object_type="word")

        results = db.lookup_terms(language="es")
        assert len(results) == 3
        for term in results:
            assert term["language"] == "es"

def test_lookup_terms_with_filters():
    """
    Given a TerminologyDatabase with multiple terms
    When terms are looked up with various filter combinations
    Then only terms matching all filter criteria should be returned
    """
    with TerminologyDatabase(":memory:") as db:
        db.add_term("hello", "hola", "es", context="greeting", object_type="word")
        db.add_term("hello", "salut", "fr", context="greeting", object_type="word")
        db.add_term("world", "mundo", "es", context="noun", object_type="word")
        db.add_term("button", "bouton", "fr", context="ui", object_type="object")

        # Filter by language and object_type
        results = db.lookup_terms(language="fr", object_type="word")
        assert len(results) == 1
        assert results[0]["source_term"] == "hello"

        # Filter by language and source_term_pattern
        results = db.lookup_terms(language="es", source_term_pattern="%wor%")
        assert len(results) == 1
        assert results[0]["source_term"] == "world"

        # Filter by language and context_pattern
        results = db.lookup_terms(language="fr", context_pattern="%ui%")
        assert len(results) == 1
        assert results[0]["source_term"] == "button"

def test_lookup_terms_pagination():
    """
    Given a TerminologyDatabase with many terms
    When terms are looked up with pagination parameters
    Then results should be properly paginated according to limit and offset
    """
    with TerminologyDatabase(":memory:") as db:
        for i in range(10):
            db.add_term(f"term{i}", f"target{i}", "en", context="context", object_type="word")

        results = db.lookup_terms(language="en", limit=5, offset=0)
        assert len(results) == 5
        assert results[0]["source_term"] == "term0"

        results = db.lookup_terms(language="en", limit=5, offset=5)
        assert len(results) == 5
        assert results[0]["source_term"] == "term5"

        results = db.lookup_terms(language="en", limit=5, offset=10)
        assert len(results) == 0

def test_get_terms_by_object_type():
    """
    Given a TerminologyDatabase with terms of different object types
    When terms are retrieved by object type
    Then only terms of the specified object type should be returned
    """
    with TerminologyDatabase(":memory:") as db:
        db.add_term("hello", "hola", "es", context="greeting", object_type="word")
        db.add_term("button", "bouton", "fr", context="ui", object_type="object")
        db.add_term("label", "étiquette", "fr", context="ui", object_type="object")

        results = db.get_terms_by_object_type(language="fr", object_type="object")
        assert len(results) == 2
        for term in results:
            assert term["language"] == "fr"
            assert term["object_type"] == "object"

        results = db.get_terms_by_object_type(language="es", object_type="word")
        assert len(results) == 1
        assert results[0]["source_term"] == "hello"

def test_lookup_terms_no_results_and_invalid_filters():
    """
    Given a TerminologyDatabase with some terms
    When terms are looked up with filters that don't match any terms or with invalid filter values
    Then an empty list should be returned
    """
    with TerminologyDatabase(":memory:") as db:
        db.add_term("hello", "hola", "es", context="greeting", object_type="word")

        # No results for unmatched language
        results = db.lookup_terms(language="de")
        assert results == []

        # No results for unmatched object_type
        results = db.lookup_terms(language="es", object_type="nonexistent")
        assert results == []

        # No results for unmatched source_term_pattern
        results = db.lookup_terms(language="es", source_term_pattern="%xyz%")
        assert results == []

        # No results for unmatched context_pattern
        results = db.lookup_terms(language="es", context_pattern="%xyz%")
        assert results == []

        # Invalid limit and offset should be handled gracefully (e.g., treated as None or zero results)
        results = db.lookup_terms(language="es", limit=-1)
        assert results == []

        results = db.lookup_terms(language="es", offset=-5)
        assert results == []

def test_bulk_import_terms_success():
    """
    Given a TerminologyDatabase and a list of term dictionaries
    When bulk_import_terms is called
    Then all terms should be successfully imported into the database
    """
    with TerminologyDatabase(":memory:") as db:
        terms_list = [
            {"source_term": "hello", "target_term": "hola", "language": "es", "context": "greeting", "object_type": "word"},
            {"source_term": "world", "target_term": "mundo", "language": "es", "context": "noun", "object_type": "word"},
            {"source_term": "cat", "target_term": "gato", "language": "es", "context": "animal", "object_type": "word"},
        ]
        db.bulk_import_terms(terms_list)
        cursor = db.conn.cursor()
        cursor.execute("SELECT source_term, target_term, language, context, object_type FROM Terms")
        rows = cursor.fetchall()
        assert len(rows) == 3
        for term in terms_list:
            assert (term["source_term"], term["target_term"], term["language"], term["context"], term["object_type"]) in rows

def test_bulk_import_terms_transaction_rollback_on_error():
    """
    Given a TerminologyDatabase and a list of terms with one invalid term
    When bulk_import_terms is called
    Then no terms should be committed due to transaction rollback
    """
    with TerminologyDatabase(":memory:") as db:
        terms_list = [
            {"source_term": "hello", "target_term": "hola", "language": "es"},
            {"source_term": None, "target_term": "mundo", "language": "es"},  # Malformed entry, source_term None
            {"source_term": "cat", "target_term": "gato", "language": "es"},
        ]
        try:
            db.bulk_import_terms(terms_list)
        except Exception:
            pass
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Terms")
        count = cursor.fetchone()[0]
        # No terms should be committed due to rollback
        assert count == 0

def test_bulk_import_terms_duplicate_handling():
    """
    Given a TerminologyDatabase and a list of terms with duplicates
    When bulk_import_terms is called
    Then only unique terms should be inserted
    """
    with TerminologyDatabase(":memory:") as db:
        terms_list = [
            {"source_term": "hello", "target_term": "hola", "language": "es"},
            {"source_term": "hello", "target_term": "hola", "language": "es"},  # Duplicate
            {"source_term": "world", "target_term": "mundo", "language": "es"},
        ]
        db.bulk_import_terms(terms_list)
        cursor = db.conn.cursor()
        cursor.execute("SELECT source_term FROM Terms WHERE language = 'es'")
        rows = cursor.fetchall()
        # Only unique terms should be inserted
        assert len(rows) == 2

def test_add_metadata_and_get_metadata():
    """
    Given a TerminologyDatabase
    When metadata is added and then retrieved
    Then the retrieved metadata should match what was added
    """
    with TerminologyDatabase(":memory:") as db:
        source_file = "import1.xlf"
        language_pair = "en-es"
        version = "1.0"
        db.add_metadata(source_file, language_pair, version)
        all_metadata = db.get_metadata(None)
        filtered_metadata = db.get_metadata(language_pair)
        assert any(md["source_file"] == source_file and md["language_pair"] == language_pair and md["version"] == version for md in all_metadata)
        assert all(md["language_pair"] == language_pair for md in filtered_metadata)

def test_bulk_import_terms_performance():
    """
    Given a TerminologyDatabase and a large list of terms
    When bulk_import_terms is called
    Then all terms should be imported efficiently
    """
    with TerminologyDatabase(":memory:") as db:
        terms_list = [
            {"source_term": f"term{i}", "target_term": f"term{i}_target", "language": "en"}
            for i in range(100)
        ]
        db.bulk_import_terms(terms_list)
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Terms WHERE language = 'en'")
        count = cursor.fetchone()[0]
        assert count == 100

def test_term_exists_true_and_false():
    """
    Given a TerminologyDatabase with a specific term
    When term_exists is called with various parameters
    Then it should correctly identify whether the term exists
    """
    with TerminologyDatabase(":memory:") as db:
        db.add_term("hello", "hola", "es")
        assert db.term_exists("hello", "es") is True
        assert db.term_exists("hello", "fr") is False
        assert db.term_exists("nonexistent", "es") is False

def test_update_term_success():
    """
    Given a TerminologyDatabase with an existing term
    When update_term is called with new values
    Then the term should be updated with the new values
    """
    with TerminologyDatabase(":memory:") as db:
        db.add_term("hello", "hola", "es")
        term = db.get_term("hello", "es")
        term_id = term["id"]
        db.update_term(term_id, target_term="salut", context="informal")
        updated_term = db.get_term("hello", "es")
        assert updated_term["target_term"] == "salut"
        assert updated_term["context"] == "informal"

def test_add_term_duplicate_raises():
    """
    Given a TerminologyDatabase with an existing term
    When add_term is called with the same source term and language
    Then it should raise a TerminologyDBError
    """
    with TerminologyDatabase(":memory:") as db:
        db.add_term("hello", "hola", "es")
        with pytest.raises(TerminologyDBError):
            db.add_term("hello", "hola2", "es")

@pytest.mark.parametrize("source_term, target_term, language", [
    (None, "hola", "es"),
    ("hello", "hola", None),
    ("", "hola", "es"),
    ("hello", "hola", ""),
])
def test_add_term_invalid_parameters(source_term, target_term, language):
    """
    Given a TerminologyDatabase
    When add_term is called with invalid parameters
    Then it should raise a ValueError
    """
    with TerminologyDatabase(":memory:") as db:
        with pytest.raises(ValueError):
            db.add_term(source_term, target_term, language)

import unittest.mock

def test_database_error_handling():
    """
    Given a TerminologyDatabase with a simulated database error
    When a database operation is performed
    Then it should wrap the underlying error in a TerminologyDBError
    """
    db = TerminologyDatabase(":memory:")

    class MockCursor:
        def execute(self, *args, **kwargs):
            raise sqlite3.DatabaseError("Simulated DB error")
        def fetchone(self):
            return None
        def fetchall(self):
            return []
        def __getattr__(self, attr):
            # For commit, rollback, etc.
            def dummy(*a, **k): return None
            return dummy

    class MockConnection:
        def cursor(self):
            return MockCursor()
        def commit(self):
            pass
        def rollback(self):
            pass
        def close(self):
            pass

    # Replace db.conn with a mock connection after initialization
    db.conn = MockConnection()
    with pytest.raises(TerminologyDBError):
        db.add_term("hello", "hola", "es")
    db.close()

def test_existing_database_behavior(tmp_path):
    """
    Given an existing database file
    When a new TerminologyDatabase instance connects to it
    Then the database schema should be intact
    """
    db_path = tmp_path / "test_existing.db"
    # Create database first time
    db1 = TerminologyDatabase(str(db_path))
    db1.close()

    # Create again, should connect without error and schema should be intact
    db2 = TerminologyDatabase(str(db_path))
    cursor = db2.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    assert "Terms" in tables
    assert "Metadata" in tables
    db2.close()

def test_invalid_path_raises():
    """
    Given an invalid database file path
    When a TerminologyDatabase attempts to connect to it
    Then it should raise an exception
    """
    # Try to open a database in an invalid path
    invalid_path = "/invalid_path/terminology.db"
    with pytest.raises(Exception):
        TerminologyDatabase(invalid_path)