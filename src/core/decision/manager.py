import datetime
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from src.core.decision.storage.models import DecisionContext, Hypothesis, ValidationResult, ConfidenceScore, Recommendation, ExperimentPlan
from src.core.decision.context.engine import ContextEngine
from src.core.decision.hypothesis.generator import HypothesisGenerator
from src.core.decision.evidence.retriever import EvidenceRetriever
from src.core.decision.validation.validator import ValidationEngine
from src.core.decision.confidence.scorer import ConfidenceScorer
from src.core.decision.ranking.ranker import HypothesisRanker
from src.core.decision.recommendation.engine import RecommendationEngine
from src.core.decision.planner.ab_planner import ExperimentPlanner
from src.core.decision.explanation.explainer import ExplanationEngine

from src.core.forecaster import ProductForecaster
from src.core.sensitivity import SensitivityEngine
from src.core.simulator import ScenarioSimulator

class DecisionManager:
    def __init__(
        self, 
        db: Session,
        df_historical: Any,
        forecaster: ProductForecaster,
        sensitivity_engine: SensitivityEngine,
        simulator: ScenarioSimulator,
        history_manager: Optional[Any] = None
    ):
        self.db = db
        self.context_engine = ContextEngine(db)
        self.hypo_generator = HypothesisGenerator()
        self.evidence_retriever = EvidenceRetriever(db, history_manager)
        self.validator = ValidationEngine(df_historical, forecaster, sensitivity_engine, simulator)
        self.scorer = ConfidenceScorer()
        self.ranker = HypothesisRanker()
        self.rec_engine = RecommendationEngine()
        self.planner = ExperimentPlanner()
        self.explainer = ExplanationEngine()

    def process_decision_flow(self, query: str, product_id: str = "P001", session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the complete AI Scientist decision intelligence loop.
        """
        # 1. Assemble Business Context
        context_data = self.context_engine.assemble_context(query)
        
        # Write Context to DB
        db_context = DecisionContext(
            session_id=session_id,
            user_query=query,
            retrieved_kpi_snapshot=context_data["kpis"],
            active_anomalies=context_data["anomalies"],
            trend_metrics=context_data["trends"]
        )
        self.db.add(db_context)
        self.db.commit() # Get db_context.id
        
        # 2. Generate Candidate Hypotheses
        candidates = self.hypo_generator.generate_candidates(context_data)
        
        # Write Candidates & perform checks
        db_hypos = []
        validation_results = {}
        confidence_scores = {}
        historical_evidences = {}
        
        for cand in candidates:
            # Query similar previous experiments
            evidence = self.evidence_retriever.retrieve_historical_evidence(cand["title"], cand["affected_kpis"])
            historical_evidences[cand["hypothesis_id"]] = evidence
            
            # Run parallel ML validation checks
            validation = self.validator.validate(cand, product_id)
            validation_results[cand["hypothesis_id"]] = validation
            
            # Compute confidence score
            score = self.scorer.compute_confidence(validation, evidence, cand["title"])
            confidence_scores[cand["hypothesis_id"]] = score
            
            # Save Hypothesis to DB
            db_hyp = Hypothesis(
                context_id=db_context.id,
                hypothesis_id=cand["hypothesis_id"],
                title=cand["title"],
                description=cand["description"],
                generated_from=cand["generated_from"],
                affected_kpis=cand["affected_kpis"],
                confidence_prior=cand["confidence_prior"]
            )
            self.db.add(db_hyp)
            self.db.commit() # Get db_hyp.id
            db_hypos.append(db_hyp)
            
            # Save Validation Result to DB
            db_val = ValidationResult(
                hypothesis_id=db_hyp.id,
                correlation_metrics=validation["correlation"],
                forecast_sim_delta=validation["forecast_simulation"],
                sensitivity_elasticity=validation["sensitivity"],
                causal_estimates=validation["causal"],
                segment_consistency={"product_id": product_id}
            )
            self.db.add(db_val)
            
            # Save Confidence Score to DB
            db_score = ConfidenceScore(
                hypothesis_id=db_hyp.id,
                overall_confidence=score["overall_confidence"],
                historical_agreement=score["breakdown"]["historical_agreement"],
                correlation_strength=score["breakdown"]["correlation_strength"],
                sensitivity_agreement=score["breakdown"]["sensitivity_alignment"],
                forecast_agreement=score["breakdown"]["forecast_simulation_agreement"],
                causal_confidence=score["breakdown"]["causal_confidence"],
                reasoning_breakdown=score["reasoning"]
            )
            self.db.add(db_score)
            
        self.db.commit()
        
        # 3. Prioritize & Rank Hypotheses
        ranked_items = self.ranker.rank_hypotheses(candidates, validation_results, confidence_scores)
        
        # 4. Generate Recommendations & Action Steps
        recommendations = self.rec_engine.generate_recommendations(ranked_items)
        
        # Save Recommendations & Experiment Plans to DB
        for idx, rec in enumerate(recommendations):
            # Find the db_hyp by hypothesis_id
            db_hyp = next((h for h in db_hypos if h.hypothesis_id == rec["hypothesis_id"]), None)
            if not db_hyp: continue
            
            db_rec = Recommendation(
                hypothesis_id=db_hyp.id,
                recommendation_text=rec["recommendation_text"],
                action_type=rec["action_type"],
                expected_kpi_improvement=rec["expected_kpi_improvement"],
                estimated_roi=rec["estimated_roi"],
                priority=rec["priority"],
                rollback_strategy=rec["rollback_strategy"]
            )
            self.db.add(db_rec)
            self.db.commit() # Get db_rec.id
            
            # If needs experimentation, plan A/B test parameter requirements
            if rec["needs_experimentation"]:
                hypo_obj = next((item for item in ranked_items if item["hypothesis"]["hypothesis_id"] == rec["hypothesis_id"]), None)
                primary_metric = hypo_obj["hypothesis"]["affected_kpis"][0] if hypo_obj else "mean_conversion_rate"
                
                plan = self.planner.plan_experiment(rec, primary_metric)
                
                db_plan = ExperimentPlan(
                    recommendation_id=db_rec.id,
                    experiment_type=plan["experiment_type"],
                    suggested_duration_days=plan["suggested_duration_days"],
                    required_sample_size=plan["required_sample_size"],
                    primary_metric=plan["primary_metric"],
                    success_criteria=plan["success_criteria"],
                    min_detectable_effect=float(plan["min_detectable_effect"].replace("%", "")) / 100.0
                )
                self.db.add(db_plan)
                
        self.db.commit()
        
        # 5. Compile Executive Markdown Summary
        explanation_markdown = self.explainer.generate_explanation(ranked_items, recommendations)
        
        return {
            "context_id": db_context.id,
            "query": query,
            "business_context": context_data,
            "ranked_hypotheses": ranked_items,
            "recommendations": recommendations,
            "explanation": explanation_markdown
        }
