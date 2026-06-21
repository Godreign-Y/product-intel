"""Agent visualization pipeline."""

__all__ = ["discover_candidates", "stream_visualizations"]


def __getattr__(name: str):
    if name in __all__:
        from src.core.agent.visualization import generator
        return getattr(generator, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
