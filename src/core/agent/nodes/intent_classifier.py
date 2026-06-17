"""
Intent Classifier Node — first node in the LangGraph pipeline.

Classifies user queries into intents and applies guardrails.
Greetings and out-of-scope queries are short-circuited here.
"""

import re
from typing import Any

from src.core.agent.state import AgentState
from src.core.agent.prompts.intent_classifier_prompt import INTENT_CLASSIFIER_SYSTEM_PROMPT
from src.core.llm import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("intent_classifier")

# Fast rule-based patterns for zero-latency classification
_GREETING_PATTERNS = {
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "howdy", "greetings", "yo", "sup", "hola", "namaste", "hii", "hiya",
    "thanks", "thank you", "thankyou", "ok", "okay", "bye", "goodbye",
}

_NON_ANALYTICAL_INTENTS = {"greeting", "system_status", "out_of_scope", "clarification_needed"}

# Factual DB lookups (rankings, counts, lists) → route directly to NL2SQL.
_DATA_LOOKUP_PATTERNS = (
    re.compile(r"\btop\s+\d+\b", re.IGNORECASE),
    re.compile(r"\b(highest|lowest|most|least|biggest|smallest)\b", re.IGNORECASE),
    re.compile(r"\bhow many\b", re.IGNORECASE),
    re.compile(r"\blist\b", re.IGNORECASE),
    re.compile(r"\bcount\b", re.IGNORECASE),
    re.compile(r"\bwhich products?\b", re.IGNORECASE),
    re.compile(r"\ball (the )?products?\b", re.IGNORECASE),
    re.compile(r"\beach product\b", re.IGNORECASE),
    re.compile(r"\btotal\b.+\b(revenue|profit|orders|inventory|sales)\b", re.IGNORECASE),
    re.compile(r"\b(revenue|profit|orders|sales)\b.+\b(for|of|by|per|from)\b", re.IGNORECASE),
)

# If these appear, prefer the ML/analytics engines, not a plain SQL lookup.
_ENGINE_INTENT_PATTERNS = re.compile(
    r"\b(forecast|predict|projection|explain why|what if|what-if|should we|"
    r"recommend|recommendation|optimi[sz]e|simulate|simulation|anomal|sensitivit)\b",
    re.IGNORECASE,
)


def _is_data_lookup_query(query: str) -> bool:
    """Detect ad-hoc factual DB questions without an LLM call."""
    if _ENGINE_INTENT_PATTERNS.search(query):
        return False
    return any(pattern.search(query) for pattern in _DATA_LOOKUP_PATTERNS)


def classify_intent(state: AgentState, llm_client: LLMClient) -> dict[str, Any]:
    """Classify the user's query into an intent with guardrails."""
    query = state["user_query"].strip()
    query_lower = query.lower().strip("!?., ")

    # ── Fast-path: rule-based greeting detection ─────────────────────
    if query_lower in _GREETING_PATTERNS or len(query_lower) < 3:
        logger.info(f"Fast-path greeting detected: '{query}'")
        return {
            "intent": "greeting",
            "intent_confidence": 1.0,
            "extracted_params": {},
            "is_blocked": False,
            "block_reason": "",
        }

    # ── Fast-path: factual data lookup (rankings, lists, counts) ─────
    if _is_data_lookup_query(query):
        logger.info(f"Fast-path data_lookup detected: '{query}'")
        return {
            "intent": "data_lookup",
            "intent_confidence": 0.97,
            "extracted_params": {"query": query},
            "is_blocked": False,
            "block_reason": "",
        }

    # ── LLM classification ───────────────────────────────────────────
    try:
        result = llm_client.generate_json(
            messages=[
                {"role": "system", "content": INTENT_CLASSIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.05,
            max_tokens=300,
        )
        intent = result.get("intent", "clarification_needed")
        confidence = float(result.get("confidence", 0.5))
        params = result.get("extracted_params", {})

        logger.info(f"Classified intent: {intent} (confidence={confidence:.2f})")

        is_blocked = intent == "out_of_scope"
        block_reason = "Query is outside the scope of business analytics." if is_blocked else ""

        return {
            "intent": intent,
            "intent_confidence": confidence,
            "extracted_params": params,
            "is_blocked": is_blocked,
            "block_reason": block_reason,
        }

    except Exception as e:
        logger.error(f"Intent classification failed: {e}. Falling back to multi_step_analysis.")
        return {
            "intent": "multi_step_analysis",
            "intent_confidence": 0.3,
            "extracted_params": {"query": query},
            "is_blocked": False,
            "block_reason": "",
        }


def is_non_analytical(state: AgentState) -> bool:
    """Check if the classified intent is non-analytical (no engine calls needed)."""
    return state["intent"] in _NON_ANALYTICAL_INTENTS
