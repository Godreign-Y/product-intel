import numpy as np
import json
import os
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from openai import OpenAI
from dotenv import load_dotenv

from src.core.history.storage.models import Report, ReportEmbedding, Experiment, KnowledgeBase
from src.core.history.embeddings.encoder import SentenceTransformerEncoder
from src.utils.logger import setup_logger

logger = setup_logger("similarity_retriever")

class SimilarityRetriever:
    def __init__(self, db: Session, encoder: SentenceTransformerEncoder):
        self.db = db
        self.encoder = encoder
        
        # Initialize OpenAI client for meta-learnings synthesis
        load_dotenv()
        self.api_key = os.getenv("NVIDIA_API_KEY") if hasattr(os, "getenv") else None
        if not self.api_key:
            # Check environment keys in os.environ
            import os as os_lib
            self.api_key = os_lib.environ.get("NVIDIA_API_KEY")
            
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "meta/llama-3.1-70b-instruct"
        
        if self.api_key:
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=None)
        else:
            self.client = None

    def semantic_search(
        self, 
        query: str, 
        limit: int = 5, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic search by encoding the query.
        Uses native pgvector distance operator (<=>) on PostgreSQL/NeonDB for database-side similarity sorting,
        falling back to in-memory numpy cosine similarity for SQLite.
        """
        logger.info(f"Executing semantic search: Query='{query}', Limit={limit}, Filters={filters}")
        
        # 1. Encode query
        query_vector = self.encoder.encode(query)
        
        # 2. Check database dialect
        is_postgresql = False
        try:
            is_postgresql = self.db.bind.dialect.name == "postgresql"
        except Exception:
            pass
            
        if is_postgresql:
            try:
                # PostgreSQL with pgvector: order by cosine distance natively
                stmt = self.db.query(ReportEmbedding)
                
                # Apply joins and filters
                if filters:
                    category = filters.get("category")
                    exp_type = filters.get("type")
                    outcome = filters.get("outcome")
                    stmt = stmt.join(Report).join(Experiment)
                    if category:
                        stmt = stmt.filter(Experiment.category == category)
                    if exp_type:
                        stmt = stmt.filter(Experiment.type == exp_type)
                    if outcome:
                        stmt = stmt.filter(Experiment.outcome == outcome)
                else:
                    stmt = stmt.join(Report).join(Experiment)
                
                if HAS_PGVECTOR:
                    distance = ReportEmbedding.embedding.cosine_distance(query_vector)
                    stmt = stmt.add_columns(distance).order_by(distance).limit(limit)
                    results_raw = stmt.all()
                    
                    results = []
                    for row in results_raw:
                        if isinstance(row, tuple):
                            emb, dist = row
                        else:
                            emb = row
                            dist = 0.0
                        score = 1.0 - float(dist) if dist is not None else 1.0
                        results.append({
                            "score": round(score, 4),
                            "report": emb.report,
                            "experiment": emb.report.experiment
                        })
                    logger.info(f"PostgreSQL native pgvector search completed. Returning top {len(results)} matches.")
                    return results
            except Exception as e:
                logger.warning(f"Native pgvector search failed: {e}. Falling back to in-memory cosine similarity.")

        # 3. Fallback: In-memory cosine similarity (SQLite / Local)
        stmt = self.db.query(ReportEmbedding)
        if filters:
            category = filters.get("category")
            exp_type = filters.get("type")
            outcome = filters.get("outcome")
            stmt = stmt.join(Report).join(Experiment)
            if category:
                stmt = stmt.filter(Experiment.category == category)
            if exp_type:
                stmt = stmt.filter(Experiment.type == exp_type)
            if outcome:
                stmt = stmt.filter(Experiment.outcome == outcome)
        else:
            stmt = stmt.join(Report).join(Experiment)
            
        embeddings_list = stmt.all()
        logger.info(f"Loaded {len(embeddings_list)} candidate report embeddings for in-memory cosine similarity check.")
        if not embeddings_list:
            return []
            
        results = []
        vecA = np.array(query_vector)
        normA = np.linalg.norm(vecA)
        
        for emb in embeddings_list:
            if not emb.embedding:
                continue
                
            vecB = np.array(emb.embedding)
            normB = np.linalg.norm(vecB)
            
            if normA == 0 or normB == 0:
                score = 0.0
            else:
                score = float(np.dot(vecA, vecB) / (normA * normB))
                
            results.append({
                "score": round(score, 4),
                "report": emb.report,
                "experiment": emb.report.experiment
            })
            
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        top_matches = results[:limit]
        logger.info(f"In-memory semantic search completed. Found {len(results)} total matches. Top score: {top_matches[0]['score'] if top_matches else 'N/A'}")
        return top_matches

    def find_similar_experiments(
        self, 
        category: str, 
        features: Dict[str, Any], 
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Finds past experiments with the same category and close parameters (e.g. price/discount overrides).
        """
        logger.info(f"Finding similar experiments in category '{category}' matching features: {features}")
        
        # Query experiments in the same category
        experiments = self.db.query(Experiment).filter(Experiment.category == category).all()
        if not experiments:
            logger.info(f"No experiments found for category '{category}'. Falling back to search all experiments.")
            # Fallback to all if category has no matches
            experiments = self.db.query(Experiment).all()
            
        scored = []
        for exp in experiments:
            score = 0.0
            # Compare parameters safely
            # If outcome is positive, give a slight boost
            if exp.outcome == "positive":
                score += 0.2
                
            # If the change summary matches features, increase score
            # Simple keyword matching for demo similarity
            matches = 0
            total_checks = 0
            for feat_name, feat_val in features.items():
                total_checks += 1
                feat_key = feat_name.lower().replace("_pct", "").replace("_fee", "").replace("_spend", "")
                if feat_key in exp.change_summary.lower():
                    matches += 1
            if total_checks > 0:
                score += (matches / total_checks) * 0.8
                
            scored.append({
                "similarity_score": round(min(0.99, max(0.10, score)), 2),
                "experiment": exp
            })
            
        scored = sorted(scored, key=lambda x: x["similarity_score"], reverse=True)
        top_scores = scored[:limit]
        logger.info(f"Experiment similarity matching complete. Scored {len(scored)} candidates. Returning top {len(top_scores)} matches.")
        return top_scores

    def extract_topic_insights(self, topic: str) -> Dict[str, Any]:
        """
        Checks KnowledgeBase cache. If missing, fetches relevant experiments,
        calls LLM to synthesize meta-learnings and failure patterns, and caches it.
        """
        logger.info(f"Extracting topic insights for topic: '{topic}'")
        
        # 1. Check cache
        cached = self.db.query(KnowledgeBase).filter(KnowledgeBase.pattern_type == topic).first()
        if cached:
            logger.info(f"KnowledgeBase cache HIT for topic '{topic}'.")
            return {
                "topic": topic,
                "synthesized_rules": cached.synthesized_rules,
                "confidence_score": cached.confidence_score,
                "cached": True
            }
            
        logger.info(f"KnowledgeBase cache MISS for topic '{topic}'. Fetching relevant experiments via semantic search...")
        
        # 2. Fetch reports/experiments matching topic keyword
        search_query = f"experiments and learnings related to {topic}"
        similar_reports = self.semantic_search(search_query, limit=10)
        
        if not similar_reports:
            logger.warning(f"No historical experiments found relating to topic '{topic}'. Returning empty fallback rules.")
            return {
                "topic": topic,
                "synthesized_rules": {
                    "success_rate_pct": 0.0,
                    "learnings": f"No historical experiments found relating to topic '{topic}'.",
                    "frequent_failures": [],
                    "successful_strategies": []
                },
                "confidence_score": 0.5,
                "cached": False
            }
            
        # 3. Calculate statistical success rate
        total = len(similar_reports)
        positives = sum(1 for r in similar_reports if r["experiment"].outcome == "positive")
        success_rate = (positives / total * 100.0) if total > 0 else 0.0
        
        # 4. Synthesize with LLM or Fallback Template
        experiments_data = []
        for r in similar_reports:
            exp = r["experiment"]
            rep = r["report"]
            experiments_data.append({
                "id": exp.experiment_id,
                "type": exp.type,
                "outcome": exp.outcome,
                "improvement_pct": exp.improvement_pct,
                "change_summary": exp.change_summary,
                "structured_learnings": rep.structured_json.get("learnings", "") if rep.structured_json else ""
            })
            
        if self.client:
            system_prompt = (
                "You are an Executive Business Intelligence System.\n"
                "Analyze the list of past growth experiments and synthesize recurring patterns, strategies, and failure modes.\n"
                "You must return a valid JSON object containing exactly three fields:\n"
                "- \"learnings\": A brief high-level summary of the recurring patterns.\n"
                "- \"frequent_failures\": List of actions/experiments that failed or backfired.\n"
                "- \"successful_strategies\": List of strategies that consistently succeeded.\n"
                "Keep the tone strictly professional, analytical, and numbers-focused."
            )
            
            user_prompt = (
                f"Topic: {topic}\n"
                f"Historical Experiments Data:\n{json.dumps(experiments_data, indent=2)}"
            )
            
            try:
                logger.info(f"Synthesizing meta-learnings for topic '{topic}' using LLM...")
                logger.info(f"LLM System Prompt:\n{system_prompt}\n")
                logger.info(f"LLM User Prompt:\n{user_prompt}\n")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=600
                )
                raw_text = response.choices[0].message.content.strip()
                logger.info(f"LLM Raw Text Response:\n{raw_text}\n")
                
                # Clean markdown wrapper blocks
                cleaned_text = raw_text.strip()
                if cleaned_text.startswith("```"):
                    cleaned_text = re.sub(r"^```(?:json)?\s*", "", cleaned_text)
                    cleaned_text = re.sub(r"\s*```$", "", cleaned_text)
                    cleaned_text = cleaned_text.strip()
                
                json_match = re.search(r"\{.*\}", cleaned_text, re.DOTALL)
                if json_match:
                    synthesized = json.loads(json_match.group(0))
                else:
                    synthesized = json.loads(cleaned_text)
                    
                logger.info(f"LLM Parsed Synthesized Object:\n{json.dumps(synthesized, indent=2)}\n")
            except Exception as e:
                logger.error(f"LLM insight synthesis failed: {e}. Using template fallback.")
                synthesized = self._get_fallback_synthesis(topic, experiments_data)
        else:
            logger.info("No NVIDIA NIM API client configured. Using deterministic fallback synthesis.")
            synthesized = self._get_fallback_synthesis(topic, experiments_data)
            
        synthesized["success_rate_pct"] = round(success_rate, 2)
        
        # Determine driver, segment, and season from topic keyword
        topic_lower = topic.lower()
        
        driver_val = None
        if "discount" in topic_lower:
            driver_val = "discount_pct"
        elif "price" in topic_lower or "pricing" in topic_lower:
            driver_val = "avg_selling_price"
        elif "shipping" in topic_lower:
            driver_val = "shipping_fee"
        elif "spend" in topic_lower or "marketing" in topic_lower:
            driver_val = "marketing_spend"
            
        segment_val = None
        for cat in ["haircare", "makeup", "skincare", "beauty"]:
            if cat in topic_lower:
                segment_val = cat.capitalize()
                break
                
        season_val = None
        for s in ["winter", "spring", "summer", "fall"]:
            if s in topic_lower:
                season_val = s.capitalize()
                break

        # 5. Cache to KnowledgeBase
        confidence_score = round(float(0.5 + (success_rate / 200.0)), 2)
        kb_entry = KnowledgeBase(
            pattern_type=topic,
            query_context=search_query,
            synthesized_rules=synthesized,
            confidence_score=confidence_score,
            driver=driver_val,
            segment=segment_val,
            season=season_val,
            outcome_score=round(float(success_rate), 2),
            confidence=confidence_score
        )
        self.db.add(kb_entry)
        self.db.commit()
        
        logger.info(f"Topic insights cached in KnowledgeBase for topic '{topic}' (Confidence: {confidence_score}).")
        
        return {
            "topic": topic,
            "synthesized_rules": synthesized,
            "confidence_score": kb_entry.confidence_score,
            "cached": False
        }

    def _get_fallback_synthesis(self, topic: str, exps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fallback pattern generator if NIM API is offline.
        """
        failures = []
        successes = []
        for e in exps:
            outcome = e["outcome"]
            change = e["change_summary"]
            learnings = e["structured_learnings"]
            
            desc = f"{change} ({learnings})" if learnings else change
            if outcome == "negative":
                failures.append(desc)
            elif outcome == "positive":
                successes.append(desc)
                
        return {
            "learnings": f"Aggregated analysis of {len(exps)} historical experiments matching the topic keyword '{topic}'.",
            "frequent_failures": failures[:3] if failures else ["No major failures recorded for this topic."],
            "successful_strategies": successes[:3] if successes else ["No consistent positive strategies recorded for this topic."]
        }

