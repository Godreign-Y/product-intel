"""Ensure NL2SQL prompts survive str.format() without KeyError on JSON keys."""

from src.core.nl2sql.generator import _GENERATION_SYSTEM_PROMPT, _REPAIR_SYSTEM_PROMPT


def test_generation_prompt_format_escapes_json_keys() -> None:
    rendered = _GENERATION_SYSTEM_PROMPT.format(schema="TABLES")
    assert "TABLES" in rendered
    assert '{"sql"' in rendered


def test_repair_prompt_format_escapes_json_keys() -> None:
    rendered = _REPAIR_SYSTEM_PROMPT.format(schema="TABLES")
    assert "TABLES" in rendered
    assert '{"sql"' in rendered
