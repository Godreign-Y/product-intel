"""
Unified LLM Client with automatic provider failover.

Provider priority: configurable via LLM_PROVIDER_ORDER (default: ollama,nvidia_nim).
Ollama uses OpenAI-compatible /v1 API; falls back to native ollama SDK if installed.
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

DEFAULT_OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "300"))
DEFAULT_NVIDIA_TIMEOUT = float(os.getenv("NVIDIA_TIMEOUT_SECONDS", "45"))


class LLMClient:
    """Centralized LLM client with configurable provider order and Ollama native fallback."""

    def __init__(self) -> None:
        self._providers: list[dict[str, Any]] = []
        self._init_providers()

    def _init_providers(self) -> None:
        """Register available providers; order controlled by LLM_PROVIDER_ORDER."""
        registry: dict[str, dict[str, Any]] = {}

        nvidia_key = os.getenv("NVIDIA_API_KEY")
        if nvidia_key:
            registry["nvidia_nim"] = {
                "name": "nvidia_nim",
                "client": OpenAI(
                    base_url="https://integrate.api.nvidia.com/v1",
                    api_key=nvidia_key,
                    timeout=DEFAULT_NVIDIA_TIMEOUT,
                ),
                "tiers": {
                    "fast": os.getenv("NVIDIA_MODEL_FAST", "google/gemma-3n-e2b-it"),
                    "capable": os.getenv("NVIDIA_MODEL_CAPABLE", "google/gemma-3n-e4b-it"),
                },
            }
            logger.info("Registered provider: NVIDIA NIM")

        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        ollama_model = os.getenv("OLLAMA_MODEL", "gemma3:4b")
        registry["ollama"] = {
            "name": "ollama",
            "client": OpenAI(
                base_url=ollama_url,
                api_key="ollama",
                timeout=DEFAULT_OLLAMA_TIMEOUT,
            ),
            "tiers": {
                "fast": ollama_model,
                "capable": ollama_model,
            },
            "native_model": ollama_model,
        }
        logger.info("Registered provider: Ollama (OpenAI-compatible %s)", ollama_url)

        order_raw = os.getenv("LLM_PROVIDER_ORDER", "nvidia_nim,ollama")
        order = [p.strip() for p in order_raw.split(",") if p.strip()]
        for name in order:
            if name in registry:
                self._providers.append(registry[name])
        for name, provider in registry.items():
            if provider not in self._providers:
                self._providers.append(provider)

    def _native_ollama_generate(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        model: str,
    ) -> str:
        """Fallback using the native ollama Python SDK (same as ollama_test.py)."""
        try:
            import ollama
        except ImportError as exc:
            raise RuntimeError("Native ollama package not installed") from exc

        response = ollama.chat(
            model=model,
            messages=messages,
            stream=False,
            options={"temperature": temperature, "num_predict": max_tokens},
        )
        content = response.get("message", {}).get("content", "")
        if not content:
            raise RuntimeError("Native ollama returned empty content")
        return content.strip()

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1024,
        model_tier: str = "capable",
    ) -> str:
        """Generate a text completion, trying providers in priority order."""
        errors: list[str] = []
        ollama_model = os.getenv("OLLAMA_MODEL", "gemma3:4b")
        native_first = os.getenv("OLLAMA_NATIVE_FIRST", "true").lower() in ("1", "true", "yes")

        for provider in self._providers:
            model = provider["tiers"].get(model_tier, provider["tiers"]["capable"])

            if provider["name"] == "ollama" and native_first:
                try:
                    text = self._native_ollama_generate(
                        messages, temperature, max_tokens, ollama_model
                    )
                    logger.info("LLM response via native ollama SDK (%s chars)", len(text))
                    return text
                except Exception as native_err:
                    errors.append(f"ollama_native: {native_err}")
                    logger.warning("Native ollama (primary) failed: %s", native_err)

            try:
                response = provider["client"].chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                text = response.choices[0].message.content.strip()
                logger.debug(
                    "LLM response from %s using %s (%s chars)",
                    provider["name"],
                    model,
                    len(text),
                )
                return text
            except Exception as e:
                msg = f"{provider['name']}: {e}"
                errors.append(msg)
                logger.warning("Provider %s failed: %s", provider["name"], e)

                if provider["name"] == "ollama" and not native_first:
                    try:
                        text = self._native_ollama_generate(
                            messages, temperature, max_tokens, ollama_model
                        )
                        logger.info("LLM recovered via native ollama SDK (%s chars)", len(text))
                        return text
                    except Exception as native_err:
                        errors.append(f"ollama_native: {native_err}")
                        logger.warning("Native ollama fallback failed: %s", native_err)

        raise RuntimeError(
            "All LLM providers failed. Check API keys and connectivity. "
            + " | ".join(errors)
        )

    def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1024,
        model_tier: str = "capable",
    ):
        """Generate a streaming text completion, yielding text chunks."""
        for provider in self._providers:
            try:
                model = provider["tiers"].get(model_tier, provider["tiers"]["capable"])
                response = provider["client"].chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                logger.debug(f"LLM streaming response from {provider['name']} using {model}")
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                return
            except Exception as e:
                logger.warning(f"Provider {provider['name']} failed streaming: {e}")
                continue

        raise RuntimeError("All LLM providers failed. Check API keys and connectivity.")

    def generate_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1024,
        model_tier: str = "capable",
    ) -> dict[str, Any]:
        """Generate and parse a JSON response from the LLM."""
        raw = self.generate(messages, temperature, max_tokens, model_tier)
        return self._parse_json(raw)

    def generate_compact(
        self,
        messages: list[dict[str, str]],
        parser: str,
        temperature: float = 0.1,
        max_tokens: int = 512,
        model_tier: str = "fast",
    ) -> dict[str, Any]:
        """Generate and parse compact JSONL (or fallback JSON) from the LLM."""
        from src.core.llm.compact import (
            parse_compact_dag,
            parse_compact_intent,
            parse_compact_sql,
            parse_compact_validation,
        )

        raw = self.generate(messages, temperature, max_tokens, model_tier)
        parsers = {
            "intent": parse_compact_intent,
            "dag": parse_compact_dag,
            "sql": lambda t: {"sql": parse_compact_sql(t)},
            "validation": parse_compact_validation,
        }
        fn = parsers.get(parser)
        if fn is None:
            return self._parse_json(raw)
        try:
            return fn(raw)
        except Exception:
            return self._parse_json(raw)

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """Extract and parse JSON from LLM output, handling markdown fences."""
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(cleaned)
