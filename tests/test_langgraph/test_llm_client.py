"""
Tests for the LLM Client failover chain.

Validates NVIDIA NIM → Ollama failover and JSON parsing.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.core.llm.client import LLMClient


class TestLLMClientFailover:
    """Test provider failover behavior."""

    @patch.dict("os.environ", {"NVIDIA_API_KEY": "test-key"}, clear=False)
    def test_nvidia_success_skips_ollama(self) -> None:
        client = LLMClient()
        assert len(client._providers) >= 1
        assert client._providers[0]["name"] == "nvidia_nim"

    @patch.dict("os.environ", {}, clear=True)
    def test_no_nvidia_key_uses_ollama_only(self) -> None:
        client = LLMClient()
        assert client._providers[0]["name"] == "ollama"

    def test_failover_on_first_provider_error(self) -> None:
        client = LLMClient()
        # Mock both providers
        mock_nvidia = MagicMock()
        mock_nvidia.chat.completions.create.side_effect = ConnectionError("timeout")
        mock_ollama = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        mock_ollama.chat.completions.create.return_value = mock_response

        client._providers = [
            {"name": "nvidia_nim", "client": mock_nvidia, "model": "test-model"},
            {"name": "ollama", "client": mock_ollama, "model": "gemma3:4b"},
        ]

        result = client.generate([{"role": "user", "content": "hello"}])
        assert result == "test response"
        mock_nvidia.chat.completions.create.assert_called_once()
        mock_ollama.chat.completions.create.assert_called_once()

    def test_all_providers_fail_raises_error(self) -> None:
        client = LLMClient()
        mock_provider = MagicMock()
        mock_provider.chat.completions.create.side_effect = RuntimeError("fail")
        client._providers = [{"name": "test", "client": mock_provider, "model": "m"}]

        with pytest.raises(RuntimeError, match="All LLM providers failed"):
            client.generate([{"role": "user", "content": "hello"}])


class TestJSONParsing:
    """Test JSON extraction from LLM output."""

    def test_clean_json(self) -> None:
        result = LLMClient._parse_json('{"intent": "greeting", "confidence": 0.9}')
        assert result["intent"] == "greeting"

    def test_json_with_markdown_fences(self) -> None:
        result = LLMClient._parse_json('```json\n{"intent": "forecast"}\n```')
        assert result["intent"] == "forecast"

    def test_json_with_surrounding_text(self) -> None:
        result = LLMClient._parse_json('Here is the result: {"key": "value"} hope it helps!')
        assert result["key"] == "value"
