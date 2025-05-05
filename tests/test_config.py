import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import asyncio
import time
from src.bcxlftranslator.main import translate_with_retry, DELAY_BETWEEN_REQUESTS, MAX_RETRIES, RETRY_DELAY

class DelayMockTranslator:
    """Mock translator that respects delays"""
    def __init__(self):
        self.translate_count = 0
        self.last_translate_time = 0

    async def translate(self, text, dest, src):
        current_time = time.time()
        if self.translate_count > 0:
            time_diff = current_time - self.last_translate_time
            assert time_diff >= DELAY_BETWEEN_REQUESTS, f"Request made too quickly: {time_diff} seconds"
        self.translate_count += 1
        self.last_translate_time = current_time
        return type('obj', (object,), {'text': 'translated'})

def test_cli_arguments_set_terminology_config(monkeypatch):
    """
    Given CLI arguments for terminology usage
    When the configuration is loaded
    Then the configuration should reflect the CLI options
    """
    import sys
    from src.bcxlftranslator import config
    test_args = [
        'prog',
        '--use-terminology',
        '--db', 'myterms.db',
        '--enable-term-matching',
        '--disable-term-highlighting',
        'input.xlf',
        'output.xlf',
    ]
    monkeypatch.setattr(sys, 'argv', test_args)
    cfg = config.load_config()
    assert cfg['use_terminology'] is True
    assert cfg['db'] == 'myterms.db'
    assert cfg['enable_term_matching'] is True
    assert cfg['disable_term_highlighting'] is True
    assert cfg['input_file'] == 'input.xlf'
    assert cfg['output_file'] == 'output.xlf'

@pytest.mark.asyncio
async def test_delay_between_requests():
    """Test that delay between requests is respected"""
    translator = DelayMockTranslator()

    # Make multiple translation requests
    for _ in range(3):
        await translate_with_retry(translator, "test", "da", "en")

    # If we got here without assertion errors, the delays were respected
    assert translator.translate_count == 3

@pytest.mark.asyncio
async def test_retry_delay():
    """Test that retry delay is respected"""
    start_time = time.time()

    # Create a mock translator that always fails
    class MockTranslator:
        async def translate(self, text, dest, src):
            raise Exception("Translation failed")

    translator = MockTranslator()

    # Attempt translation (should fail after MAX_RETRIES)
    result = await translate_with_retry(translator, "test", "da", "en")

    elapsed_time = time.time() - start_time
    # Should have waited RETRY_DELAY between each retry
    assert elapsed_time >= RETRY_DELAY * (MAX_RETRIES - 1)
    assert result is None  # Should have failed

@pytest.mark.asyncio
async def test_max_retries():
    """Test that max retries is respected"""
    attempts = 0

    # Create a mock translator that counts attempts
    class MockTranslator:
        async def translate(self, text, dest, src):
            nonlocal attempts
            attempts += 1
            raise Exception("Translation failed")

    translator = MockTranslator()

    # Attempt translation
    await translate_with_retry(translator, "test", "da", "en")

    # Should have tried exactly MAX_RETRIES + 1 times (initial try + retries)
    assert attempts == MAX_RETRIES + 1

def test_load_config_from_file(tmp_path, monkeypatch):
    """
    Given a configuration file specifying terminology options
    When the configuration is loaded
    Then the configuration should reflect the file values
    """
    import sys
    import json
    from src.bcxlftranslator import config
    config_file = tmp_path / "config.json"
    config_data = {
        "use_terminology": True,
        "db": "fileterms.db",
        "enable_term_matching": True,
        "disable_term_highlighting": True
    }
    config_file.write_text(json.dumps(config_data))
    test_args = ['prog', '--config', str(config_file), 'input.xlf', 'output.xlf']
    monkeypatch.setattr(sys, 'argv', test_args)
    cfg = config.load_config()
    assert cfg['use_terminology'] is True
    assert cfg['db'] == 'fileterms.db'
    assert cfg['enable_term_matching'] is True
    assert cfg['disable_term_highlighting'] is True
    assert cfg['input_file'] == 'input.xlf'
    assert cfg['output_file'] == 'output.xlf'

def test_load_config_from_env(monkeypatch):
    """
    Given terminology options set as environment variables
    When the configuration is loaded
    Then the configuration should reflect the environment variable values
    """
    import sys
    from src.bcxlftranslator import config
    monkeypatch.setenv('BCXLF_USE_TERMINOLOGY', '1')
    monkeypatch.setenv('BCXLF_DB', 'envterms.db')
    monkeypatch.setenv('BCXLF_ENABLE_TERM_MATCHING', '1')
    monkeypatch.setenv('BCXLF_DISABLE_TERM_HIGHLIGHTING', '1')
    test_args = ['prog', 'input.xlf', 'output.xlf']
    monkeypatch.setattr(sys, 'argv', test_args)
    cfg = config.load_config()
    assert cfg['use_terminology'] is True
    assert cfg['db'] == 'envterms.db'
    assert cfg['enable_term_matching'] is True
    assert cfg['disable_term_highlighting'] is True
    assert cfg['input_file'] == 'input.xlf'
    assert cfg['output_file'] == 'output.xlf'

def test_config_precedence(monkeypatch, tmp_path):
    """
    Given terminology options set in env, config file, and CLI
    When the configuration is loaded
    Then precedence should be CLI > file > env
    """
    import sys
    import json
    from src.bcxlftranslator import config
    # Set env lowest precedence
    monkeypatch.setenv('BCXLF_USE_TERMINOLOGY', '0')
    monkeypatch.setenv('BCXLF_DB', 'envterms.db')
    # File middle precedence
    config_file = tmp_path / "config.json"
    config_data = {
        "use_terminology": True,
        "db": "fileterms.db"
    }
    config_file.write_text(json.dumps(config_data))
    # CLI highest precedence
    test_args = [
        'prog',
        '--use-terminology',
        '--db', 'cliterms.db',
        '--config', str(config_file),
        'input.xlf',
        'output.xlf',
    ]
    monkeypatch.setattr(sys, 'argv', test_args)
    cfg = config.load_config()
    # CLI wins
    assert cfg['use_terminology'] is True
    assert cfg['db'] == 'cliterms.db'
    assert cfg['input_file'] == 'input.xlf'
    assert cfg['output_file'] == 'output.xlf'

def test_config_defaults(monkeypatch):
    """
    Given no CLI args, config file, or env vars for terminology
    When the configuration is loaded
    Then default values should be applied
    """
    import sys
    from src.bcxlftranslator import config
    test_args = ['prog']
    monkeypatch.setattr(sys, 'argv', test_args)
    cfg = config.load_config()
    assert cfg['use_terminology'] is False
    assert cfg['db'] is None
    assert cfg['enable_term_matching'] is False
    assert cfg['disable_term_matching'] is False
    assert cfg['enable_term_highlighting'] is False
    assert cfg['disable_term_highlighting'] is False
    assert cfg['input_file'] is None
    assert cfg['output_file'] is None

def test_config_validation_rejects_invalid(monkeypatch):
    """
    Given conflicting terminology config options (e.g. both enable and disable for the same feature)
    When the configuration is loaded
    Then an error should be raised
    """
    import sys
    from src.bcxlftranslator import config
    test_args = [
        'prog',
        '--enable-term-matching',
        '--disable-term-matching',
        'input.xlf',
        'output.xlf',
    ]
    monkeypatch.setattr(sys, 'argv', test_args)
    try:
        config.load_config()
        assert False, "Expected ValueError for conflicting options"
    except ValueError as e:
        assert "enable and disable" in str(e) or "conflict" in str(e).lower()