"""
Unified LLM Client with automatic provider failover.

Provider priority: NVIDIA NIM -> Ollama (gemma3:4b).
All LLM calls across the application route through this single client.
"""

import os
import json
import re
from typing import Any, Optional

from openai import OpenAI
from dotenv import load_dotenv

from src.utils.logger import setup_logger

load_dotenv()
logger = setup_logger("llm_client")


class LLMClient:
    """Centralized LLM client with NVIDIA NIM primary and Ollama fallback."""

    def __init__(self) -> None:
        self._providers: list[dict[str, Any]] = []
        self._init_providers()

    def _init_providers(self) -> None:
        """Register available providers in priority order."""
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        if nvidia_key:
            self._providers.append({
                "name": "nvidia_nim",
                "client": OpenAI(
                    base_url="https://integrate.api.nvidia.com/v1",
                    api_key=nvidia_key,
                    timeout=30,
                ),
                "model": os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct"),
            })
            logger.info("Registered provider: NVIDIA NIM")

        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self._providers.append({
            "name": "ollama",
            "client": OpenAI(
                base_url=ollama_url,
                api_key="ollama",
                timeout=60,
            ),
            "model": os.getenv("OLLAMA_MODEL", "gemma3:4b"),
        })
        logger.info("Registered provider: Ollama")

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a text completion, trying providers in priority order."""
        for provider in self._providers:
            try:
                response = provider["client"].chat.completions.create(
                    model=provider["model"],
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                text = response.choices[0].message.content.strip()
                logger.debug(f"LLM response from {provider['name']} ({len(text)} chars)")
                return text
            except Exception as e:
                logger.warning(f"Provider {provider['name']} failed: {e}")
                continue

        raise RuntimeError("All LLM providers failed. Check API keys and connectivity.")

    def generate_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """Generate and parse a JSON response from the LLM."""
        raw = self.generate(messages, temperature, max_tokens)
        return self._parse_json(raw)

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """Extract and parse JSON from LLM output, handling markdown fences."""
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(cleaned)
