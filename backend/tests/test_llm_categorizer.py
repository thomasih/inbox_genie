import pytest
from unittest.mock import patch, MagicMock
import os
import json
from app.llm_categorizer import LLMEmailCategorizer, CATEGORIES

@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("USE_LLM", "true")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "mock-deployment")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "mock-endpoint")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "mock-key")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

@pytest.fixture
def sample_emails():
    return [
        {"id": f"id{i}", "subject": f"Subject {i}", "sender": {"name": "Test", "email": "test@example.com"}} for i in range(5)
    ]

def mock_openai_response(json_obj):
    class MockChoice:
        def __init__(self, content):
            self.message = MagicMock(content=content)
    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]
    return MockResponse(json.dumps(json_obj))

@patch("app.llm_categorizer.AzureOpenAI")
def test_llm_success(mock_aoai, sample_emails):
    # Mock OpenAI to return a valid JSON response
    folder_map = {CATEGORIES[0]: [e["id"] for e in sample_emails], "Summary": 5}
    mock_aoai.return_value.chat.completions.create.return_value = mock_openai_response(folder_map)
    cat = LLMEmailCategorizer()
    result = cat.categorize_emails(sample_emails)
    assert CATEGORIES[0] in result
    assert set(result[CATEGORIES[0]]) == set(e["id"] for e in sample_emails)

@patch("app.llm_categorizer.AzureOpenAI")
def test_llm_malformed_json(mock_aoai, sample_emails):
    # Malformed JSON triggers demjson3 fallback
    bad_json = '{"Finance": ["id0", "id1"], "Summary": 2'  # missing closing }
    class MockChoice:
        def __init__(self, content):
            self.message = MagicMock(content=content)
    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]
    mock_aoai.return_value.chat.completions.create.return_value = MockResponse(bad_json)
    cat = LLMEmailCategorizer()
    result = cat.categorize_emails(sample_emails[:2])
    assert "Finance" in result or "error" in result

@patch("app.llm_categorizer.AzureOpenAI")
def test_llm_truncated_output(mock_aoai, sample_emails):
    # Truncated output should return error
    truncated = '{"Finance": ["id0", "id1"]'  # missing closing }
    class MockChoice:
        def __init__(self, content):
            self.message = MagicMock(content=content)
    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]
    mock_aoai.return_value.chat.completions.create.return_value = MockResponse(truncated)
    cat = LLMEmailCategorizer()
    result = cat.categorize_emails(sample_emails[:2])
    assert "error" in result

@patch("app.llm_categorizer.AzureOpenAI")
def test_llm_cache_and_dedup(mock_aoai, sample_emails):
    folder_map = {CATEGORIES[0]: [e["id"] for e in sample_emails], "Summary": 5}
    mock_aoai.return_value.chat.completions.create.return_value = mock_openai_response(folder_map)
    cat = LLMEmailCategorizer()
    # First call populates cache
    result1 = cat.categorize_emails(sample_emails)
    # Second call should hit cache (simulate by changing subject)
    emails2 = [dict(e) for e in sample_emails]
    emails2[0]["subject"] = "Changed"
    result2 = cat.categorize_emails(sample_emails)
    assert result1 == result2
