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

def test_config_defaults(monkeypatch):
    """
    Given no CLI args, config file, or env vars
    When the configuration is loaded
    Then default values should be applied
    """
    import sys
    from src.bcxlftranslator import config
    test_args = ['prog']
    monkeypatch.setattr(sys, 'argv', test_args)
    cfg = config.load_config()
    # Only check for input and output file defaults
    assert cfg['input_file'] is None
    assert cfg['output_file'] is None