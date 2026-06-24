"""
SQL generator — uses the LLM to convert natural language to SQL.
"""

from typing import Any

from src.core.llm import LLMClient
from src.core.nl2sql.schema import get_schema_prompt
from src.core.nl2sql.dates import get_date_context_for_prompt
from src.utils.logger import setup_logger

logger = setup_logger("nl2sql_generator")

_GENERATION_SYSTEM_PROMPT = """\
You are a SQL expert for a business analytics database.
Convert the user's natural language question into a single SELECT query.

{schema}

Output ONLY JSONL (one line): {{"sql":"SELECT ..."}}

Guidelines:
- Use only listed tables and columns — never reference total_revenue/total_profit as columns; use SUM(revenue) AS total_revenue instead.
- Prefer aggregations (SUM, AVG, COUNT) for totals and rankings.
- When the user asks for "each product" or "all products", GROUP BY product_id.
- When GROUP BY date (or any column), every other selected column MUST be inside SUM(), AVG(), COUNT(), MIN(), or MAX(). Never mix bare columns with GROUP BY.
- Do NOT use window functions (LAG, LEAD, OVER, ROW_NUMBER). For revenue drops compare periods with GROUP BY product_id, date and simple aggregates.
- For daily rollups: SELECT date, SUM(revenue) AS total_revenue, AVG(conversion_rate) AS avg_conversion_rate ... GROUP BY date
- Filter dates with standard comparisons (date >= 'YYYY-MM-DD').
- Resolve relative dates ("last week", "this month") using the DATE CONTEXT above.
- Product IDs look like P001, P002, etc.
- Do NOT use JSON column operators.
- Always include LIMIT (max 25 rows; top-N queries use LIMIT 10).

Example — "top 5 products by revenue in January 2025":
{{"sql":"SELECT product_id, SUM(revenue) AS total_revenue FROM product_performance WHERE date >= '2025-01-01' AND date < '2025-02-01' GROUP BY product_id ORDER BY total_revenue DESC LIMIT 5"}}
"""

_REPAIR_SYSTEM_PROMPT = """\
You are a SQL expert. The previous query failed validation or execution.
Fix the SQL based on the error message.

{schema}

Common fixes:
- GroupingError: wrap every non-GROUP-BY column in SUM() or AVG(). Example: GROUP BY date → use SUM(revenue), AVG(conversion_rate), not bare revenue.
- Missing column: use only columns from the schema.

Output ONLY JSONL: {{"sql":"SELECT ..."}}
"""



def generate_sql(
    llm_client: LLMClient,
    question: str,
    dialect: str = "postgresql",
    error_context: str | None = None,
) -> str:
    """Generate SQL from a natural language question."""
    schema = get_schema_prompt(dialect, date_context=get_date_context_for_prompt())
    if error_context:
        system = _REPAIR_SYSTEM_PROMPT.format(schema=schema)
        user_content = f"Question: {question}\n\nPrevious error:\n{error_context}"
    else:
        system = _GENERATION_SYSTEM_PROMPT.format(schema=schema)
        user_content = question

    result = llm_client.generate_compact(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        parser="sql",
        temperature=0.0,
        max_tokens=350,
        model_tier="fast",
    )
    sql = result.get("sql", "").strip()
    if not sql:
        raise ValueError("LLM did not return a SQL query.")
    logger.debug(f"Generated SQL: {sql[:200]}")
    return sql
