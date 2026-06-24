"""
SQL validator — enforces read-only, allowlisted queries before execution.
"""

import re
from typing import Optional

from src.core.nl2sql.schema import ALLOWED_TABLES

_FORBIDDEN_KEYWORDS = re.compile(
    r"\b("
    r"INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|MERGE|"
    r"GRANT|REVOKE|EXEC|EXECUTE|CALL|COPY|INTO|ATTACH|DETACH|PRAGMA"
    r")\b",
    re.IGNORECASE,
)

_DEFAULT_LIMIT = 25
_RANKING_LIMIT = 10
_AGG_FUNCS = re.compile(r"\b(SUM|AVG|COUNT|MIN|MAX)\s*\(", re.IGNORECASE)
_WINDOW_FUNCS = re.compile(r"\b(LAG|LEAD|ROW_NUMBER|RANK|DENSE_RANK|NTILE)\s*\(|\bOVER\s*\(", re.IGNORECASE)


class SQLValidationError(ValueError):
    """Raised when generated SQL fails safety checks."""


def validate_sql(sql: str, allowed_tables: frozenset[str] | None = None) -> str:
    """
    Validate and normalize a SQL query.

    Returns the sanitized SQL (with LIMIT enforced if missing).
    Raises SQLValidationError on unsafe input.
    """
    if not sql or not sql.strip():
        raise SQLValidationError("Empty SQL query.")

    allowed = allowed_tables or ALLOWED_TABLES
    normalized = _strip_comments(sql.strip()).rstrip(";").strip()

    if ";" in normalized:
        raise SQLValidationError("Multiple statements are not allowed.")

    if not re.match(r"^SELECT\b", normalized, re.IGNORECASE):
        raise SQLValidationError("Only SELECT queries are allowed.")

    if _FORBIDDEN_KEYWORDS.search(normalized):
        raise SQLValidationError("Query contains forbidden keywords.")

    if _WINDOW_FUNCS.search(normalized):
        raise SQLValidationError(
            "Window functions (LAG, OVER, ROW_NUMBER) are not allowed. "
            "Use GROUP BY with SUM/AVG instead."
        )

    referenced = _extract_table_names(normalized)
    unknown = referenced - allowed
    if unknown:
        raise SQLValidationError(f"Query references disallowed tables: {sorted(unknown)}")

    if not referenced:
        raise SQLValidationError("Query must reference at least one allowed table.")

    normalized = repair_group_by(normalized)
    max_limit = _infer_limit(normalized)
    return _ensure_limit(normalized, max_limit)


def _infer_limit(sql: str) -> int:
    """Use smaller limits for rankings and daily rollups."""
    lower = sql.lower()
    if re.search(r"\border by\b", lower) and re.search(
        r"\b(top|desc|asc|rank|highest|lowest)\b", lower
    ):
        return _RANKING_LIMIT
    if re.search(r"\bgroup by\b", lower) and "date" in lower:
        return min(_DEFAULT_LIMIT, 31)
    return _DEFAULT_LIMIT


def repair_group_by(sql: str) -> str:
    """
    Fix common GROUP BY violations: non-aggregated SELECT columns not in GROUP BY.
    Wraps bare columns in SUM() or AVG() so PostgreSQL accepts the query.
    """
    if not re.search(r"\bGROUP BY\b", sql, re.IGNORECASE):
        return sql

    select_match = re.search(r"\bSELECT\b(.*?)\bFROM\b", sql, re.IGNORECASE | re.DOTALL)
    group_match = re.search(
        r"\bGROUP BY\b(.*?)(?=\bORDER BY\b|\bLIMIT\b|\bHAVING\b|$)",
        sql,
        re.IGNORECASE | re.DOTALL,
    )
    if not select_match or not group_match:
        return sql

    group_cols = _parse_group_by_columns(group_match.group(1))
    fields = _split_select_fields(select_match.group(1))
    if not fields:
        return sql

    fixed_fields: list[str] = []
    changed = False
    for field in fields:
        fixed, field_changed = _fix_select_field(field, group_cols)
        fixed_fields.append(fixed)
        changed = changed or field_changed

    if not changed:
        return sql

    new_select = ", ".join(fixed_fields)
    return (
        sql[: select_match.start(1)]
        + " "
        + new_select
        + " "
        + sql[select_match.end(1) :]
    )


def _parse_group_by_columns(group_clause: str) -> set[str]:
    cols: set[str] = set()
    for part in group_clause.split(","):
        token = part.strip().split()[-1]
        token = token.split(".")[-1].lower().strip()
        if token:
            cols.add(token)
    return cols


def _split_select_fields(select_clause: str) -> list[str]:
    fields: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in select_clause:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            fields.append("".join(current).strip())
            current = []
            continue
        current.append(ch)
    tail = "".join(current).strip()
    if tail:
        fields.append(tail)
    return [f for f in fields if f]


def _fix_select_field(field: str, group_cols: set[str]) -> tuple[str, bool]:
    if _AGG_FUNCS.search(field):
        return field, False

    alias_match = re.match(
        r"^(?P<expr>(?:[\w.]+\.)?[\w]+)\s+(?:AS\s+)?(?P<alias>[\w]+)$",
        field.strip(),
        re.IGNORECASE,
    )
    if alias_match:
        expr = alias_match.group("expr")
        alias = alias_match.group("alias")
        col_name = expr.split(".")[-1].lower()
    else:
        expr = field.strip()
        col_name = expr.split(".")[-1].lower()
        alias = col_name

    if col_name in group_cols:
        return field, False

    agg = "SUM" if _prefer_sum(col_name) else "AVG"
    return f"{agg}({expr}) AS {alias}", True


def _prefer_sum(column: str) -> bool:
    col = column.lower()
    return any(
        token in col
        for token in (
            "revenue",
            "profit",
            "orders",
            "spend",
            "traffic",
            "users",
            "inventory",
            "fee",
        )
    )


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def _extract_table_names(sql: str) -> set[str]:
    """Extract table names from FROM and JOIN clauses."""
    tables: set[str] = set()
    pattern = re.compile(
        r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(sql):
        tables.add(match.group(1).lower())
    return tables


def _ensure_limit(sql: str, max_limit: int) -> str:
    if re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
        limit_match = re.search(r"\bLIMIT\s+(\d+)", sql, re.IGNORECASE)
        if limit_match and int(limit_match.group(1)) > max_limit:
            return re.sub(
                r"\bLIMIT\s+\d+",
                f"LIMIT {max_limit}",
                sql,
                count=1,
                flags=re.IGNORECASE,
            )
        return sql
    return f"{sql} LIMIT {max_limit}"
