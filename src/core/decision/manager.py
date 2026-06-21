import datetime
import concurrent.futures
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
        history_manager: Optional[Any] = None,
        explainer: Optional[Any] = None
    ):
        self.db = db
        
        # Fallback to AppState if explainer is not provided directly
        if explainer is None:
            try:
                from src.api.dependencies import AppState
                explainer = AppState.explainer
            except ImportError:
                pass
                
        self.context_engine = ContextEngine(db)
        self.hypo_generator = HypothesisGenerator(
            db=db,
            forecaster=forecaster,
            explainer=explainer,
            history_manager=history_manager
        )
        self.evidence_retriever = EvidenceRetriever(db, history_manager)
        self.validator = ValidationEngine(df_historical, forecaster, sensitivity_engine, simulator)
        self.scorer = ConfidenceScorer()
        self.ranker = HypothesisRanker()
        self.rec_engine = RecommendationEngine()
        self.planner = ExperimentPlanner()
        self.explainer = ExplanationEngine()
        self.df_historical = df_historical

    def _get_product_df_len(self, product_id: str) -> int:
        """Returns the number of rows for a given product in the historical DataFrame."""
        try:
            if self.df_historical is not None:
                return len(self.df_historical[self.df_historical["product_id"] == product_id])
        except Exception:
            pass
        return 0

    def process_decision_flow(self, query: str, product_id: str = "P001", session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the complete AI Scientist decision intelligence loop.
        Now with: product-scoped context, parallel evidence+validation,
        bulk DB flush, data_quality_factor, and context-aware planner.
        """
        # 1. Assemble Business Context — product-scoped
        context_data = self.context_engine.assemble_context(query, product_id)
        
        # Write Context to DB
        db_context = DecisionContext(
            session_id=session_id,
            user_query=query,
            retrieved_kpi_snapshot=context_data["kpis"],
            active_anomalies=context_data["anomalies"],
            trend_metrics=context_data["trends"]
        )
        self.db.add(db_context)
        self.db.flush()  # Get db_context.id without committing yet
        
        # 2. Generate Candidate Hypotheses
        candidates = self.hypo_generator.generate_candidates(context_data)
        
        # Pre-compute product data length for data quality factor
        product_df_len = self._get_product_df_len(product_id)

        # Write Candidates & perform checks
        db_hypos = []
        validation_results = {}
        confidence_scores = {}
        historical_evidences = {}
        
        for cand in candidates:
            # Ensure hypothesis_id is globally unique to satisfy DB constraint
            unique_id = f"HYP_{db_context.id}_{cand['hypothesis_id']}"
            cand["hypothesis_id"] = unique_id
            
            # Run evidence retrieval and validation in parallel (they are independent)
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                f_evidence = executor.submit(
                    self.evidence_retriever.retrieve_historical_evidence,
                    cand["title"], cand["affected_kpis"]
                )
                f_validation = executor.submit(
                    self.validator.validate, cand, product_id, query
                )
                evidence = f_evidence.result()
                validation = f_validation.result()

            historical_evidences[cand["hypothesis_id"]] = evidence
            validation_results[cand["hypothesis_id"]] = validation
            
            # Compute confidence score (with data quality factor)
            score = self.scorer.compute_confidence(
                validation, evidence, cand["title"],
                product_df_len=product_df_len
            )
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
            self.db.flush()  # Get db_hyp.id without committing
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
            
            # Save Confidence Score to DB (now includes data_quality_factor)
            db_score = ConfidenceScore(
                hypothesis_id=db_hyp.id,
                overall_confidence=score["overall_confidence"],
                historical_agreement=score["breakdown"]["historical_agreement"],
                correlation_strength=score["breakdown"]["correlation_strength"],
                sensitivity_agreement=score["breakdown"]["sensitivity_alignment"],
                forecast_agreement=score["breakdown"]["forecast_simulation_agreement"],
                causal_confidence=score["breakdown"]["causal_confidence"],
                data_quality_factor=score.get("data_quality_factor", 0.0),
                reasoning_breakdown=score["reasoning"]
            )
            self.db.add(db_score)
            
        # Bulk commit all hypothesis/validation/confidence records at once
        self.db.commit()
        
        # 3. Prioritize & Rank Hypotheses
        ranked_items = self.ranker.rank_hypotheses(candidates, validation_results, confidence_scores)
        
        # 4. Generate Recommendations & Action Steps (with context revenue for ROI normalization)
        context_revenue = context_data.get("kpis", {}).get("total_revenue", 0.0)
        recommendations = self.rec_engine.generate_recommendations(ranked_items, context_revenue=context_revenue, db=self.db)
        
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
                rollback_strategy=rec["rollback_strategy"],
                risk_assessment=rec.get("risk_assessment")
            )
            self.db.add(db_rec)
            self.db.flush()  # Get db_rec.id
            
            # If needs experimentation, plan A/B test parameter requirements
            if rec["needs_experimentation"]:
                hypo_obj = next((item for item in ranked_items if item["hypothesis"]["hypothesis_id"] == rec["hypothesis_id"]), None)
                primary_metric = hypo_obj["hypothesis"]["affected_kpis"][0] if hypo_obj else "mean_conversion_rate"
                
                # Pass context to planner for live traffic data
                plan = self.planner.plan_experiment(rec, primary_metric, context=context_data)
                
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
                
        # Bulk commit all recommendations and experiment plans
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
