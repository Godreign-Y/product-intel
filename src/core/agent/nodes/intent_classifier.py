"""
Intent Classifier Node — first node in the LangGraph pipeline.

Classifies user queries into intents and applies guardrails.
Greetings and out-of-scope queries are short-circuited here.
Uses fast SentenceTransformer embeddings for zero-latency classification.

data_lookup fast-path is intentionally strict: only pure factual SQL lookups
(rankings, counts, totals) bypass the LLM planner. Everything else goes to plan_dag.
"""

import re
from typing import Any

from src.core.agent.state import AgentState
from src.core.agent.prompts.intent_classifier_prompt import INTENT_CLASSIFIER_SYSTEM_PROMPT
from src.core.agent.nodes.intent_embeddings import get_intent_matcher
from src.core.llm import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("intent_classifier")

_GREETING_PATTERNS = {
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "howdy", "greetings", "yo", "sup", "hola", "namaste", "hii", "hiya",
    "thanks", "thank you", "thankyou", "ok", "okay", "bye", "goodbye",
}

_NON_ANALYTICAL_INTENTS = {"greeting", "system_status", "out_of_scope", "clarification_needed", "meta_query"}

_DATA_LOOKUP_MIN_CONFIDENCE = 0.88

# Never treat as a plain SQL lookup when any of these appear.
_NOT_DATA_LOOKUP = re.compile(
    r"\b("
    r"forecast|predict|projection|explain|why|what if|what-if|should we|should i|"
    r"recommend|recommendation|optimi[sz]e|maximi[sz]e|simulate|simulation|"
    r"anomal|outlier|sensitivit|elasticity|driver|root cause|diagnos|"
    r"compare|versus|\bvs\b|benchmark|trend|growth|seasonal|"
    r"strategy|best way|what happens if|what will happen|"
    r"experiment|learning|past report|historical report|a/b test"
    r")\b",
    re.IGNORECASE,
)

# Must match at least one — narrow factual-SQL shapes only.
_STRICT_DATA_LOOKUP_PATTERNS = (
    re.compile(r"\btop\s+\d+\b", re.IGNORECASE),
    re.compile(r"\bshow me the top\s+\d+\b", re.IGNORECASE),
    re.compile(r"\bhow many\s+(products?|orders?|customers?|units?|rows?)\b", re.IGNORECASE),
    re.compile(r"\b(count|number) of\s+(products?|orders?|customers?|units?)\b", re.IGNORECASE),
    re.compile(r"\blist\s+(all\s+)?(the\s+)?(products?|items?|skus?)\b", re.IGNORECASE),
    re.compile(r"\bwhat (is|was) the total\b", re.IGNORECASE),
    re.compile(
        r"\bwhich product (had|has|with) the (highest|lowest|most|least|best|worst|maximum|minimum)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\brank(?:ing)? (?:all )?products? by\b", re.IGNORECASE),
    re.compile(r"\bsum of (revenue|profit|orders|sales)\b", re.IGNORECASE),
    re.compile(
        r"\b(highest|lowest) (total )?(revenue|profit|orders|sales)\b.+\b(product|sku|P\d+)\b",
        re.IGNORECASE,
    ),
)


def _is_strict_data_lookup_query(query: str) -> bool:
    """True only for unambiguous factual DB lookups that NL2SQL alone can answer."""
    if _NOT_DATA_LOOKUP.search(query):
        return False
    if query.count("?") > 1:
        return False
    if re.search(r"\b(and|then|also)\b.+\b(forecast|explain|why|recommend|simulate|optimi[sz]e)\b", query, re.I):
        return False
    return any(pattern.search(query) for pattern in _STRICT_DATA_LOOKUP_PATTERNS)


def _data_lookup_fast_path(query: str, confidence: float, source: str) -> dict[str, Any] | None:
    """Build a direct NL2SQL plan only when confidence and pattern checks both pass."""
    if not _is_strict_data_lookup_query(query):
        logger.info(f"data_lookup rejected for '{query}' ({source}): failed strict pattern gate.")
        return None
    if confidence < _DATA_LOOKUP_MIN_CONFIDENCE:
        logger.info(
            f"data_lookup rejected for '{query}' ({source}): "
            f"confidence {confidence:.2f} < {_DATA_LOOKUP_MIN_CONFIDENCE}."
        )
        return None

    logger.info(f"Strict data_lookup fast-path ({source}): '{query}'")
    return {
        "intent": "data_lookup",
        "intent_confidence": confidence,
        "extracted_params": {"query": query},
        "execution_plan": [
            {"step_id": "s1", "tool_id": "nl2sql_query", "params": {"query": query}, "depends_on": []},
        ],
        "dag_source": source,
        "is_blocked": False,
        "block_reason": "",
    }


def classify_intent(state: AgentState, llm_client: LLMClient) -> dict[str, Any]:
    """Classify the user's query into an intent using embeddings with LLM fallback."""
    query = state.get("user_query", "").strip()
    query_lower = query.lower().strip("!?., ")

    if query_lower in _GREETING_PATTERNS or len(query_lower) < 3:
        logger.info(f"Fast-path greeting detected: '{query}'")
        return {
            "intent": "greeting",
            "intent_confidence": 1.0,
            "extracted_params": {},
            "is_blocked": False,
            "block_reason": "",
        }

    if _is_strict_data_lookup_query(query):
        fast = _data_lookup_fast_path(query, 1.0, "regex_fast_path")
        if fast:
            return fast

    matcher = get_intent_matcher()
    intent, confidence = matcher.match_intent(query, threshold=0.60)

    if intent != "unknown":
        logger.info(f"Embedding matched intent '{intent}' with confidence {confidence:.2f}")

        if intent == "data_lookup":
            fast = _data_lookup_fast_path(query, confidence, "embedding_fast_path")
            if fast:
                return fast
            intent = "analytical"

        is_blocked = intent == "out_of_scope"
        return {
            "intent": intent,
            "intent_confidence": confidence,
            "extracted_params": {"query": query},
            "is_blocked": is_blocked,
            "block_reason": "Query is outside the scope of business analytics." if is_blocked else "",
        }

    logger.info(f"Embedding confidence low ({confidence:.2f}). Falling back to LLM intent classification.")
    try:
        result = llm_client.generate_compact(
            messages=[
                {"role": "system", "content": INTENT_CLASSIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            parser="intent",
            temperature=0.05,
            max_tokens=120,
            model_tier="fast",
        )
        intent = result.get("intent", "clarification_needed")
        confidence = float(result.get("confidence", 0.5))
        params = result.get("extracted_params", {})
        params["query"] = query

        logger.info(f"LLM classified intent: {intent} (confidence={confidence:.2f})")

        if intent == "data_lookup":
            fast = _data_lookup_fast_path(query, confidence, "llm_fast_path")
            if fast:
                return fast
            intent = "analytical"
            logger.info("LLM data_lookup downgraded to analytical (strict gate).")

        is_blocked = intent == "out_of_scope"
        return {
            "intent": intent,
            "intent_confidence": confidence,
            "extracted_params": params,
            "is_blocked": is_blocked,
            "block_reason": "Query is outside the scope of business analytics." if is_blocked else "",
        }

    except Exception as e:
        logger.error(f"Intent classification failed: {e}. Falling back to analytical.")
        return {
            "intent": "analytical",
            "intent_confidence": 0.3,
            "extracted_params": {"query": query},
            "is_blocked": False,
            "block_reason": "",
        }


def is_non_analytical(state: AgentState) -> bool:
    """Check if the classified intent is non-analytical (no engine calls needed)."""
    return state["intent"] in _NON_ANALYTICAL_INTENTS
