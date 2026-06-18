"""
Intent Classifier Node — first node in the LangGraph pipeline.

Classifies user queries into intents and applies guardrails.
Greetings and out-of-scope queries are short-circuited here.
Uses fast SentenceTransformer embeddings for zero-latency classification.
"""

import re
from typing import Any

from src.core.agent.state import AgentState
from src.core.agent.prompts.intent_classifier_prompt import INTENT_CLASSIFIER_SYSTEM_PROMPT
from src.core.agent.nodes.intent_embeddings import get_intent_matcher
from src.core.llm import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("intent_classifier")

# Fast rule-based patterns for zero-latency classification
_GREETING_PATTERNS = {
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "howdy", "greetings", "yo", "sup", "hola", "namaste", "hii", "hiya",
    "thanks", "thank you", "thankyou", "ok", "okay", "bye", "goodbye",
}

_NON_ANALYTICAL_INTENTS = {"greeting", "system_status", "out_of_scope", "clarification_needed", "meta_query"}

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
    r"\b(forecast|predict|projection|explain why|why|what if|what-if|should we|"
    r"recommend|recommendation|optimi[sz]e|simulate|simulation|anomal|sensitivit|compare)\b",
    re.IGNORECASE,
)


def _is_data_lookup_query(query: str) -> bool:
    """Detect ad-hoc factual DB questions without an LLM call."""
    if _ENGINE_INTENT_PATTERNS.search(query):
        return False
    return any(pattern.search(query) for pattern in _DATA_LOOKUP_PATTERNS)


def classify_intent(state: AgentState, llm_client: LLMClient) -> dict[str, Any]:
    """Classify the user's query into an intent using embeddings with LLM fallback."""
    query = state.get("user_query", "").strip()
    query_lower = query.lower().strip("!?., ")

    # 1. Fast-path: rule-based greeting detection
    if query_lower in _GREETING_PATTERNS or len(query_lower) < 3:
        logger.info(f"Fast-path greeting detected: '{query}'")
        return {
            "intent": "greeting",
            "intent_confidence": 1.0,
            "extracted_params": {},
            "is_blocked": False,
            "block_reason": "",
        }

    # 2. Fast-path: factual data lookup (rankings, lists, counts)
    if _is_data_lookup_query(query):
        logger.info(f"Fast-path data_lookup regex detected: '{query}'")
        return {
            "intent": "data_lookup",
            "intent_confidence": 0.95,
            "extracted_params": {"query": query},
            "execution_plan": [{"step_id": "s1", "tool_id": "nl2sql_query", "params": {"query": query}, "depends_on": []}],
            "dag_source": "fast_path",
            "is_blocked": False,
            "block_reason": "",
        }

    # 3. Embedding matching
    matcher = get_intent_matcher()
    intent, confidence = matcher.match_intent(query, threshold=0.65)
    
    if intent != "unknown":
        logger.info(f"Embedding matched intent '{intent}' with confidence {confidence:.2f}")
        is_blocked = intent == "out_of_scope"
        block_reason = "Query is outside the scope of business analytics." if is_blocked else ""
        
        result = {
            "intent": intent,
            "intent_confidence": confidence,
            "extracted_params": {"query": query}, # Planner will extract actual params
            "is_blocked": is_blocked,
            "block_reason": block_reason,
        }
        
        # If the embedding strongly hits data_lookup, inject the plan directly
        if intent == "data_lookup":
            result["execution_plan"] = [{"step_id": "s1", "tool_id": "nl2sql_query", "params": {"query": query}, "depends_on": []}]
            result["dag_source"] = "embedding_fast_path"
            
        return result

    # 4. LLM fallback
    logger.info(f"Embedding confidence low ({confidence:.2f}). Falling back to LLM intent classification.")
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
        params["query"] = query

        logger.info(f"LLM Classified intent: {intent} (confidence={confidence:.2f})")

        is_blocked = intent == "out_of_scope"
        block_reason = "Query is outside the scope of business analytics." if is_blocked else ""

        response = {
            "intent": intent,
            "intent_confidence": confidence,
            "extracted_params": params,
            "is_blocked": is_blocked,
            "block_reason": block_reason,
        }
        
        if intent == "data_lookup":
            response["execution_plan"] = [{"step_id": "s1", "tool_id": "nl2sql_query", "params": {"query": query}, "depends_on": []}]
            response["dag_source"] = "llm_fast_path"
            
        return response

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
