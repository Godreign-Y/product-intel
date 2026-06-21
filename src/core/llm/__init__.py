"""Centralized LLM client package with provider failover."""

from src.core.llm.client import LLMClient

__all__ = ["LLMClient", "get_llm_client"]


def get_llm_client() -> LLMClient:
    """Return the shared AppState client or create a standalone instance."""
    try:
        from src.api.dependencies import AppState

        if AppState.llm_client is not None:
            return AppState.llm_client
    except ImportError:
        pass
    return LLMClient()
