import sqlite3
import os
from datetime import datetime, timezone
from bcxlftranslator.exceptions import TerminologyDBError

SCHEMA_VERSION = "1.0"

# Singleton support for global terminology database
_TERMINOLOGY_DB_SINGLETON = None

class TerminologyDatabaseRegistry:
    _INSTANCES = set()
    @classmethod
    def register(cls, instance):
        cls._INSTANCES.add(instance)
    @classmethod
    def unregister(cls, instance):
        cls._INSTANCES.discard(instance)
    @classmethod
    def close_all(cls):
        global _TERMINOLOGY_DB_SINGLETON
        for inst in list(cls._INSTANCES):
            try:
                inst.close()
            except Exception:
                pass
        cls._INSTANCES.clear()
        _TERMINOLOGY_DB_SINGLETON = None

def get_terminology_database(db_path=":memory:"):
    global _TERMINOLOGY_DB_SINGLETON
    if _TERMINOLOGY_DB_SINGLETON is None:
        _TERMINOLOGY_DB_SINGLETON = TerminologyDatabase(db_path)
    return _TERMINOLOGY_DB_SINGLETON

def close_terminology_database():
    global _TERMINOLOGY_DB_SINGLETON
    if _TERMINOLOGY_DB_SINGLETON is not None:
        _TERMINOLOGY_DB_SINGLETON.close()
        _TERMINOLOGY_DB_SINGLETON = None

class TerminologyDatabase:
    """
    Encapsulates all terminology database operations.
    Supports context manager protocol and explicit close.
    """

    def __init__(self, db_path: str):
        """
        Initialize the terminology SQLite database with required schema.
        If the database file exists, connect and verify schema version.
        If not, create the database and schema.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self._closed = True  # Assume closed until successful init
        self.conn = None
        try:
            self.conn = self._init_terminology_db(db_path)
            self._closed = False
            TerminologyDatabaseRegistry.register(self)
        except Exception:
            # Leave self._closed True and self.conn as None
            raise

    def _init_terminology_db(self, db_path: str) -> sqlite3.Connection:
        db_exists = os.path.isfile(db_path) if db_path != ":memory:" else False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if db_exists:
            # Check schema version in Metadata table
            try:
                cursor.execute("SELECT version FROM Metadata ORDER BY id DESC LIMIT 1;")
                row = cursor.fetchone()
                if row is None:
                    raise ValueError("Existing database schema version not found.")
                existing_version = row[0]
                if existing_version != SCHEMA_VERSION:
                    raise ValueError(f"Schema version mismatch: expected {SCHEMA_VERSION}, found {existing_version}")
            except sqlite3.Error:
                raise ValueError("Existing database schema incompatible or missing Metadata table.")
        else:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS Terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_term TEXT NOT NULL,
                    target_term TEXT NOT NULL,
                    context TEXT,
                    object_type TEXT,
                    language TEXT NOT NULL
                );
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS Metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_file TEXT,
                    version TEXT,
                    language_pair TEXT,
                    import_date TEXT
                );
                """
            )
            # Indexes for fast lookup
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_terms_source_term ON Terms(source_term);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_terms_language ON Terms(language);")
            cursor.execute(
                "INSERT INTO Metadata (version, import_date) VALUES (?, ?);",
                (SCHEMA_VERSION, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()

        return conn

    def add_term(self, source_term, target_term, language, context=None, object_type=None):
        if not source_term or not target_term or not language:
            raise ValueError("source_term, target_term, and language are required")
        try:
            cursor = self.conn.cursor()
            # Check for duplicate
            cursor.execute(
                "SELECT 1 FROM Terms WHERE source_term = ? AND language = ?",
                (source_term, language)
            )
            if cursor.fetchone():
                raise TerminologyDBError("Term already exists for this source_term and language")
            cursor.execute(
                "INSERT INTO Terms (source_term, target_term, context, object_type, language) VALUES (?, ?, ?, ?, ?)",
                (source_term, target_term, context, object_type, language)
            )
            self.conn.commit()
        except sqlite3.DatabaseError as e:
            raise TerminologyDBError(str(e))

    def get_term(self, source_term, language):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, source_term, target_term, context, object_type, language FROM Terms WHERE source_term = ? AND language = ?",
            (source_term, language)
        )
        row = cursor.fetchone()
        if row:
            columns = ["id", "source_term", "target_term", "context", "object_type", "language"]
            return dict(zip(columns, row))
        return None

    def lookup_term(self, source_term, language):
        return self.get_term(source_term, language)

    def term_exists(self, source_term, language):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM Terms WHERE source_term = ? AND language = ?",
            (source_term, language)
        )
        return cursor.fetchone() is not None

    def update_term(self, term_id, target_term=None, context=None, object_type=None, language=None):
        if not term_id:
            raise ValueError("term_id is required")
        fields = []
        params = []
        if target_term is not None:
            fields.append("target_term = ?")
            params.append(target_term)
        if context is not None:
            fields.append("context = ?")
            params.append(context)
        if object_type is not None:
            fields.append("object_type = ?")
            params.append(object_type)
        if language is not None:
            fields.append("language = ?")
            params.append(language)
        if not fields:
            raise ValueError("At least one field to update must be provided")
        params.append(term_id)
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"UPDATE Terms SET {', '.join(fields)} WHERE id = ?",
                params
            )
            self.conn.commit()
        except sqlite3.DatabaseError as e:
            raise TerminologyDBError(str(e))

    def bulk_import_terms(self, terms_list):
        if not isinstance(terms_list, list):
            raise ValueError("terms_list must be a list of term dicts")
        try:
            cursor = self.conn.cursor()
            # Use a transaction
            self.conn.execute("BEGIN")
            seen = set()
            for term in terms_list:
                source_term = term.get("source_term")
                target_term = term.get("target_term")
                language = term.get("language")
                context = term.get("context")
                object_type = term.get("object_type")
                if not source_term or not target_term or not language:
                    raise ValueError("Each term must have source_term, target_term, and language")
                key = (source_term, language)
                if key in seen:
                    continue  # skip duplicates in input
                seen.add(key)
                # Check for duplicate in DB
                cursor.execute(
                    "SELECT 1 FROM Terms WHERE source_term = ? AND language = ?",
                    (source_term, language)
                )
                if cursor.fetchone():
                    continue  # skip duplicates in DB
                cursor.execute(
                    "INSERT INTO Terms (source_term, target_term, context, object_type, language) VALUES (?, ?, ?, ?, ?)",
                    (source_term, target_term, context, object_type, language)
                )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def add_metadata(self, source_file, language_pair, version):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO Metadata (source_file, language_pair, version, import_date) VALUES (?, ?, ?, ?)",
            (source_file, language_pair, version, datetime.now(timezone.utc).isoformat())
        )
        self.conn.commit()

    def get_metadata(self, language_pair=None):
        cursor = self.conn.cursor()
        if language_pair:
            cursor.execute(
                "SELECT id, source_file, version, language_pair, import_date FROM Metadata WHERE language_pair = ?",
                (language_pair,)
            )
        else:
            cursor.execute(
                "SELECT id, source_file, version, language_pair, import_date FROM Metadata"
            )
        rows = cursor.fetchall()
        columns = ["id", "source_file", "version", "language_pair", "import_date"]
        return [dict(zip(columns, row)) for row in rows]

    def lookup_terms(self, language, source_term_pattern=None, object_type=None, context_pattern=None, limit=None, offset=None):
        if not language:
            raise ValueError("Language parameter is required")

        # If limit or offset is negative, return empty list (test expects this)
        if (limit is not None and limit < 0) or (offset is not None and offset < 0):
            return []

        query = "SELECT id, source_term, target_term, context, object_type, language FROM Terms WHERE language = ?"
        params = [language]

        if source_term_pattern is not None:
            query += " AND source_term LIKE ?"
            params.append(source_term_pattern)

        if object_type is not None:
            query += " AND object_type = ?"
            params.append(object_type)

        if context_pattern is not None:
            query += " AND context LIKE ?"
            params.append(context_pattern)

        query += " ORDER BY id"

        if limit is not None and limit >= 0:
            query += " LIMIT ?"
            params.append(limit)
            if offset is not None and offset >= 0:
                query += " OFFSET ?"
                params.append(offset)
        elif offset is not None and offset >= 0:
            query += " LIMIT -1 OFFSET ?"
            params.append(offset)

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        columns = ["id", "source_term", "target_term", "context", "object_type", "language"]
        results = [dict(zip(columns, row)) for row in rows]
        return results

    def get_terms_by_object_type(self, language, object_type, limit=None, offset=None):
        return self.lookup_terms(language, object_type=object_type, limit=limit, offset=offset)

    def close(self):
        # Defensive: Only close if not already closed and conn exists
        if hasattr(self, "_closed") and not self._closed:
            if hasattr(self, "conn") and self.conn is not None:
                try:
                    self.conn.close()
                except Exception:
                    pass
            self._closed = True
            TerminologyDatabaseRegistry.unregister(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        # Defensive: Don't raise in __del__
        try:
            self.close()
        except Exception:
            pass