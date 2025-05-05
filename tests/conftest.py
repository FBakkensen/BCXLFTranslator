def pytest_sessionfinish(session, exitstatus):
    try:
        from src.bcxlftranslator.terminology_db import close_terminology_database
        close_terminology_database()
    except (ImportError, AttributeError):
        # Gracefully handle missing module or function during test teardown
        pass
