def pytest_sessionfinish(session, exitstatus):
    from bcxlftranslator.terminology_db import close_terminology_database
    close_terminology_database()
