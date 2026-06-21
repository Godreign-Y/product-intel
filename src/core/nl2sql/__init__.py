__all__ = ["NL2SQLEngine"]


def __getattr__(name: str):
    if name == "NL2SQLEngine":
        from src.core.nl2sql.engine import NL2SQLEngine

        return NL2SQLEngine
    raise AttributeError(name)
