from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy import create_engine, text

from src.core.agent.nodes.tool_nodes import execute_tool


def _sqlite_product_engine():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE product_performance (
                    product_id TEXT,
                    revenue REAL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO product_performance VALUES
                ('P001', 100.0),
                ('P002', 150.0)
                """
            )
        )
    return engine


def test_nl2sql_direct_select_uses_executor_without_llm() -> None:
    nl2sql_engine = SimpleNamespace(_db_engine=_sqlite_product_engine(), ask=MagicMock())

    result = execute_tool(
        "nl2sql_query",
        {"query": "SELECT product_id, revenue FROM product_performance ORDER BY revenue DESC LIMIT 1"},
        {"nl2sql_engine": nl2sql_engine},
    )

    assert result["row_count"] == 1
    assert result["rows"][0]["product_id"] == "P002"
    nl2sql_engine.ask.assert_not_called()


def test_nl2sql_natural_language_uses_engine_ask() -> None:
    nl2sql_engine = SimpleNamespace(
        _db_engine=_sqlite_product_engine(),
        ask=MagicMock(return_value={"rows": [{"ok": True}], "row_count": 1}),
    )

    result = execute_tool("nl2sql_query", {"query": "top product by revenue"}, {"nl2sql_engine": nl2sql_engine})

    assert result["row_count"] == 1
    nl2sql_engine.ask.assert_called_once_with("top product by revenue")
