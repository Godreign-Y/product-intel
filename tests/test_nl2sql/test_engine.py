"""Tests for NL2SQL engine ask flow."""

from unittest.mock import MagicMock

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from src.core.nl2sql.engine import NL2SQLEngine


@pytest.fixture
def sqlite_engine():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE product_performance (
                date TEXT,
                product_id TEXT,
                category TEXT,
                revenue REAL,
                profit REAL,
                orders REAL
            )
        """))
        conn.execute(text("""
            INSERT INTO product_performance VALUES
            ('2025-01-01', 'P001', 'skincare', 100.0, 40.0, 10.0),
            ('2025-01-02', 'P001', 'skincare', 120.0, 48.0, 12.0),
            ('2025-01-01', 'P002', 'haircare', 80.0, 30.0, 8.0)
        """))
    return engine


class TestNL2SQLEngineAsk:
    def test_ask_returns_rows(self, sqlite_engine) -> None:
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "sql": (
                "SELECT product_id, SUM(revenue) AS total_revenue "
                "FROM product_performance GROUP BY product_id ORDER BY total_revenue DESC LIMIT 10"
            ),
        }

        engine = NL2SQLEngine(mock_llm, sqlite_engine)
        result = engine.ask("What is total revenue by product?")

        assert result["row_count"] == 2
        assert result["columns"] == ["product_id", "total_revenue"]
        assert result["rows"][0]["product_id"] == "P001"
        assert result["rows"][0]["total_revenue"] == 220.0
        assert result.get("error") is None

    def test_ask_retries_on_validation_failure(self, sqlite_engine) -> None:
        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = [
            {"sql": "DELETE FROM product_performance"},
            {
                "sql": (
                    "SELECT COUNT(*) AS cnt FROM product_performance LIMIT 1"
                ),
            },
        ]

        engine = NL2SQLEngine(mock_llm, sqlite_engine)
        result = engine.ask("How many records are there?")

        assert result["row_count"] == 1
        assert result["rows"][0]["cnt"] == 3
        assert mock_llm.generate_json.call_count == 2

    def test_ask_returns_error_after_retries(self, sqlite_engine) -> None:
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {"sql": "DELETE FROM product_performance"}

        engine = NL2SQLEngine(mock_llm, sqlite_engine)
        result = engine.ask("Delete everything")

        assert result["row_count"] == 0
        assert "error" in result
