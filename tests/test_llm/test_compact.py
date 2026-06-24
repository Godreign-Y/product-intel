"""Tests for compact JSONL LLM parsers."""

from src.core.llm.compact import (
    parse_compact_dag,
    parse_compact_intent,
    parse_compact_sql,
    parse_compact_validation,
)


def test_parse_compact_intent():
    text = '{"intent":"analytical"}\n{"conf":0.91}\n{"p":{"product_id":"P001"}}'
    out = parse_compact_intent(text)
    assert out["intent"] == "analytical"
    assert out["confidence"] == 0.91
    assert out["extracted_params"]["product_id"] == "P001"


def test_parse_compact_dag():
    text = (
        '{"k":"r","v":"Channel then decision"}\n'
        '{"k":"s","i":"s1","t":"analytics_channel","p":{},"f":{},"d":[]}\n'
        '{"k":"s","i":"s2","t":"decision_ask","p":{"query":"help"},"f":{},"d":["s1"]}'
    )
    out = parse_compact_dag(text)
    assert out["reasoning"] == "Channel then decision"
    assert len(out["dag"]) == 2
    assert out["dag"][1]["tool_id"] == "decision_ask"


def test_parse_compact_sql():
    assert parse_compact_sql('{"sql":"SELECT 1"}') == "SELECT 1"


def test_parse_compact_validation():
    assert parse_compact_validation('{"ok":0,"notes":"missing decision"}')["ok"] is False
