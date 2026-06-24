"""Centralized LLM client package with provider failover."""

__all__ = ["LLMClient", "get_llm_client"]


def __getattr__(name: str):
    if name == "LLMClient":
        from src.core.llm.client import LLMClient
        return LLMClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_llm_client() -> "LLMClient":
    """Return the shared AppState client or create a standalone instance."""
    from src.core.llm.client import LLMClient

    try:
        from src.api.dependencies import AppState

        if AppState.llm_client is not None:
            return AppState.llm_client
    except ImportError:
        pass
    return LLMClient()
