"""
Compact JSONL parsers for minimal-token LLM outputs.

Each line is one small JSON object. Keys are shortened:
  r=reasoning, i=step_id, t=tool_id, p=params dict, f=input_from, d=depends_on
  intent, conf, sql, ok, notes, clarification
"""

from __future__ import annotations

import json
import re
from typing import Any

_LINE = re.compile(r"^\s*\{.*\}\s*$", re.DOTALL)


def parse_jsonl_lines(text: str) -> list[dict[str, Any]]:
    """Parse non-empty lines as JSON objects."""
    cleaned = re.sub(r"```(?:jsonl?|json)?\s*", "", text).strip().rstrip("`")
    objects: list[dict[str, Any]] = []
    for line in cleaned.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            objects.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return objects


def parse_compact_intent(text: str) -> dict[str, Any]:
    """Parse intent classifier JSONL: intent + conf lines."""
    objs = parse_jsonl_lines(text)
    if not objs:
        return json.loads(re.search(r"\{.*\}", text, re.DOTALL).group(0)) if re.search(r"\{", text) else {}

    merged: dict[str, Any] = {}
    for obj in objs:
        merged.update(obj)
    intent = merged.get("intent", merged.get("i", "analytical"))
    conf = merged.get("confidence", merged.get("conf", 0.5))
    params = merged.get("extracted_params", merged.get("p", {}))
    if not isinstance(params, dict):
        params = {}
    return {"intent": intent, "confidence": float(conf), "extracted_params": params}


def parse_compact_dag(text: str) -> dict[str, Any]:
    """Parse planner JSONL into {reasoning, dag, clarification}."""
    objs = parse_jsonl_lines(text)
    if not objs:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {"reasoning": "", "dag": [], "clarification": ""}

    reasoning = ""
    clarification = ""
    dag: list[dict[str, Any]] = []

    for obj in objs:
        kind = obj.get("k", obj.get("type", ""))
        if kind in ("r", "reasoning") or "reasoning" in obj and kind != "s":
            reasoning = str(obj.get("v", obj.get("reasoning", reasoning)))
        if kind in ("c", "clarification") or obj.get("clarification"):
            clarification = str(obj.get("v", obj.get("clarification", clarification)))
        if kind in ("s", "step") or obj.get("tool_id") or obj.get("t"):
            step_id = str(obj.get("i", obj.get("step_id", f"s{len(dag) + 1}")))
            tool_id = str(obj.get("t", obj.get("tool_id", "")))
            params = dict(obj.get("p", obj.get("params", {})))
            input_from = dict(obj.get("f", obj.get("input_from", {})))
            depends_on = list(obj.get("d", obj.get("depends_on", [])))
            if tool_id:
                dag.append({
                    "step_id": step_id,
                    "tool_id": tool_id,
                    "params": params,
                    "input_from": input_from,
                    "depends_on": depends_on,
                })

    return {"reasoning": reasoning, "dag": dag, "clarification": clarification}


def parse_compact_sql(text: str) -> str:
    """Parse NL2SQL JSONL: {\"sql\":\"...\"} or {\"k\":\"sql\",\"v\":\"...\"}."""
    objs = parse_jsonl_lines(text)
    if objs:
        for obj in objs:
            if obj.get("sql"):
                return str(obj["sql"]).strip()
            if obj.get("k") == "sql" and obj.get("v"):
                return str(obj["v"]).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        data = json.loads(match.group(0))
        return str(data.get("sql", "")).strip()
    return ""


def parse_compact_validation(text: str) -> dict[str, Any]:
    """Parse validator JSONL: ok (0|1) and optional notes."""
    objs = parse_jsonl_lines(text)
    if objs:
        merged: dict[str, Any] = {}
        for obj in objs:
            merged.update(obj)
        ok = merged.get("ok", merged.get("passed", 1))
        return {
            "ok": bool(int(ok)) if str(ok).isdigit() else bool(ok),
            "notes": str(merged.get("notes", merged.get("n", ""))),
        }
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        data = json.loads(match.group(0))
        return {"ok": bool(data.get("ok", data.get("passed", True))), "notes": data.get("notes", "")}
    return {"ok": True, "notes": ""}
